"""Verify documented Git comparison semantics in an isolated temporary repository."""
import tempfile
from pathlib import Path
from build_fixtures import commit, git, initialize, write


def check():
    with tempfile.TemporaryDirectory(prefix='code-review-git-') as directory:
        repo = initialize(Path(directory), 'repo')
        assert git(repo, 'status', '--porcelain=v1') == ''
        write(repo, 'value.txt', 'root\n')
        git(repo, 'add', '.')
        assert '+root' in git(repo, 'diff', '--cached', '--')
        commit(repo, 'root')
        root = git(repo, 'rev-parse', 'HEAD')
        assert '+root' in git(repo, 'show', '--root', '--format=', root, '--')
        empty = git(repo, 'hash-object', '-t', 'tree', '-w', '--stdin')
        assert '+root' in git(repo, 'diff', empty, root, '--')
        main = git(repo, 'symbolic-ref', '--short', 'HEAD')
        git(repo, 'checkout', '-qb', 'side')
        write(repo, 'side.txt', 'side\n')
        commit(repo, 'side')
        side = git(repo, 'rev-parse', 'HEAD')
        git(repo, 'checkout', '-q', main)
        write(repo, 'main.txt', 'main\n')
        commit(repo, 'main')
        before_merge = git(repo, 'rev-parse', 'HEAD')
        endpoint = git(repo, 'diff', '--name-only', before_merge + '..' + side)
        common = git(repo, 'diff', '--name-only', before_merge + '...' + side)
        assert set(endpoint.splitlines()) == {'main.txt', 'side.txt'}
        assert common == 'side.txt'
        assert git(repo, 'merge-base', '--all', before_merge, side) == root
        git(repo, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
            '-c', 'core.hooksPath=/dev/null', 'merge', '--no-ff', '-qm', 'merge', 'side')
        merge = git(repo, 'rev-parse', 'HEAD')
        assert git(repo, 'diff', '--name-only', merge + '^1', merge, '--') == 'side.txt'
        assert git(repo, 'diff', '--name-only', merge + '^2', merge, '--') == 'main.txt'
        assert git(repo, 'show', '--cc', '--format=', merge) == ''
        assert set(git(repo, 'diff', '--name-only', before_merge + '^1', merge).splitlines()) == {'main.txt', 'side.txt'}
        git(repo, 'merge-base', '--is-ancestor', before_merge, merge)
        assert git(repo, 'status', '--porcelain=v1') == ''
        write(repo, 'value.txt', 'staged\n')
        git(repo, 'add', 'value.txt')
        write(repo, 'value.txt', 'final\n')
        write(repo, 'new file.txt', 'new\n')
        assert git(repo, 'show', ':value.txt') == 'staged'
        assert '+staged' in git(repo, 'diff', '--cached', '--')
        assert '+final' in git(repo, 'diff', '--', 'value.txt')
        assert '+final' in git(repo, 'diff', 'HEAD', '--')
        assert git(repo, 'ls-files', '--others', '--exclude-standard', '-z') == 'new file.txt\x00'
        commit(repo, 'final')
        git(repo, 'checkout', '-qb', 'conflict-side')
        write(repo, 'value.txt', 'theirs\n')
        commit(repo, 'theirs')
        git(repo, 'checkout', '-q', main)
        write(repo, 'value.txt', 'ours\n')
        commit(repo, 'ours')
        import subprocess
        result = subprocess.run(['git', '-C', str(repo), '-c', 'user.name=Fixture',
            '-c', 'user.email=fixture@example.invalid', '-c', 'core.hooksPath=/dev/null',
            'merge', 'conflict-side'], capture_output=True, text=True)
        assert result.returncode == 1
        assert git(repo, 'ls-files', '-u')
        assert git(repo, 'show', ':1:value.txt') == 'final'
        assert git(repo, 'show', ':2:value.txt') == 'ours'
        assert git(repo, 'show', ':3:value.txt') == 'theirs'
    print('PASS: unborn/root, endpoints, merge-base, inclusive range, merge parents, partial staging, untracked, clean state, conflicts')


if __name__ == '__main__':
    check()
