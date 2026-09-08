"""Create isolated Git fixtures for code-review comparisons (standard library only)."""
import argparse
import json
from pathlib import Path
import subprocess


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()


def write(repo, name, text):
    (repo / name).write_text(text)


def commit(repo, message):
    git(repo, 'add', '.')
    git(repo, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
        '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', message)


def initialize(root, name):
    repo = root / name
    repo.mkdir(parents=True, exist_ok=False)
    git(repo, 'init', '-q')
    return repo


def build(root):
    mixed = initialize(root, 'mixed')
    write(mixed, 'README.md', 'Python 3.9+. Totals are integer cents. Discounts apply once to the subtotal, then shipping is added.\n')
    write(mixed, 'pricing.py', 'def total(subtotal_cents, shipping_cents):\n    return subtotal_cents + shipping_cents\n')
    write(mixed, 'checkout.py', 'from pricing import total\n\ndef checkout(subtotal_cents):\n    return total(subtotal_cents, 500)\n')
    commit(mixed, 'Initial pricing')
    write(mixed, 'pricing.py', 'def total(subtotal_cents, shipping_cents, discount_percent=0):\n    return (subtotal_cents + shipping_cents) * (100 - discount_percent) // 100\n')
    git(mixed, 'add', 'pricing.py')
    write(mixed, 'pricing.py', 'def total(subtotal_cents, shipping_cents, discount_percent=0):\n    discounted_cents = (subtotal_cents + shipping_cents) * (100 - discount_percent) // 100\n    return discounted_cents\n')
    write(mixed, 'checkout.py', 'from pricing import total\n\ndef checkout(subtotal_cents):\n    return total(subtotal_cents, 500, discount_percent=10)\n')
    write(mixed, 'renewal.py', 'from pricing import total\n\ndef renewal(subtotal_cents):\n    return total(subtotal_cents, 200, discount_percent=10)\n')

    historical = initialize(root, 'historical')
    write(historical, 'README.md', 'Python 3.9+. The transport contract is send(url, timeout_ms=None, signal=None). None means unlimited wait or no cancellation. The supplied signal must be forwarded unchanged.\n')
    write(historical, 'transport.py', 'class Transport:\n    def send(self, url, timeout_ms=None, signal=None):\n        """Diagnostic transport returns exactly the options received by I/O."""\n        return {"url": url, "timeout_ms": timeout_ms, "signal": signal}\n')
    write(historical, 'client.py', 'def request(transport, url, **options):\n    return transport.send(url, **options)\n')
    write(historical, 'service.py', 'from client import request\n\ndef load(transport, signal):\n    return request(transport, "/items", timeout_ms=5000, signal=signal)\n')
    commit(historical, 'Initial forwarding')
    write(historical, 'client.py', 'def dispatch(transport, url, options):\n    return transport.send(url)\n\ndef request(transport, url, **options):\n    return dispatch(transport, url, options)\n')
    commit(historical, 'Introduce dispatch layer')
    git(historical, 'tag', 'review-target')
    write(historical, 'client.py', 'def dispatch(transport, url, options):\n    return transport.send(url, **options)\n\ndef request(transport, url, **options):\n    return dispatch(transport, url, options)\n')
    commit(historical, 'Forward dispatch options')

    compatibility = initialize(root, 'compatibility')
    write(compatibility, 'README.md', 'Python 3.9+. Public account_response must keep accountStatus for existing consumers. Internal records may use status. Checkout and renewal share one discount policy: active members with subtotal >= 10000 cents receive 10%, otherwise zero.\n')
    write(compatibility, 'account.py', 'def account_record():\n    return {"accountStatus": "active"}\n\ndef account_response():\n    return account_record()\n')
    write(compatibility, 'consumer.py', 'from account import account_response\n\ndef is_active():\n    return account_response()["accountStatus"] == "active"\n')
    commit(compatibility, 'Initial account contract')
    write(compatibility, 'account.py', 'def account_record():\n    return {"status": "active"}\n\ndef account_response():\n    record = account_record()\n    return {"accountStatus": record["status"]}\n')
    for name in ('checkout', 'renewal'):
        write(compatibility, name + '.py', 'def discount_percent(is_active_member, subtotal_cents):\n    if is_active_member and subtotal_cents >= 10000:\n        return 10\n    return 0\n')
    git(compatibility, 'add', '.')
    return {name: str(root / name) for name in ('mixed', 'historical', 'compatibility')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.destination.resolve()), indent=2))
