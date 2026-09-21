# Collections

## Contents

- [Semantics, Representation, and Cost](#semantics-representation-and-cost)
- [Default Choice](#default-choice)
- [When to Use Which Collection](#when-to-use-which-collection)
- [Operation Costs](#operation-costs)
- [Capacity Management](#capacity-management)
- [Entry API](#entry-api)
- [Hashing and HashDoS](#hashing-and-hashdos)
- [Iteration Order and Determinism](#iteration-order-and-determinism)
- [Ordered Maps: Ranges, First and Last](#ordered-maps-ranges-first-and-last)
- [Priority Queues](#priority-queues)
- [Queues and Sliding Windows](#queues-and-sliding-windows)
- [Removing Elements](#removing-elements)
- [Several Mutable Elements at Once](#several-mutable-elements-at-once)
- [Keys That Are Not Ord or Hash](#keys-that-are-not-ord-or-hash)
- [Graphs and Trees Without Reference Cycles](#graphs-and-trees-without-reference-cycles)
- [Static Lookup Tables](#static-lookup-tables)
- [Fixed-Length and Frozen Sequences](#fixed-length-and-frozen-sequences)
- [Common Mistakes](#common-mistakes)
- [Availability by Version](#availability-by-version)
- [Practical Boundaries](#practical-boundaries)

Examples are independent items using stable APIs unless stated otherwise; see [compatibility](../../SKILL.md#compatibility).

## Semantics, Representation, and Cost

A collection combines behavior with a storage strategy. Vec stores elements contiguously, VecDeque supports efficient operations at both ends, hash collections use hashing and equality, and ordered trees use key ordering. Required order, uniqueness, ranges, and stable identity narrow the suitable representations before performance comparisons.

Operation complexity describes scaling, not elapsed time. Key comparison or hashing, allocation, element size, locality, and input size can change the practical result. Iteration-heavy code may favor a different representation from lookup-heavy code. Capacity reuse reduces repeated growth but can retain a large allocation; connect collection operations to [memory and allocation](memory-and-allocation.md).

## Default Choice

Use Vec for a growable sequence and HashMap for key lookup when no stronger ordering or access requirement applies. Sorted ranges, operations at both ends, and priority retrieval justify different representations. Start from the required operations; a default does not override their semantics.

## When to Use Which Collection

| Collection | Use when | Requires |
|---|---|---|
| `Vec<T>` | Items collected for later processing, a sequence appended at or near the end, a stack, a resizable or heap-allocated array | nothing |
| `VecDeque<T>` | A `Vec` with efficient insertion and removal at both ends, a queue, a double-ended queue | nothing |
| `LinkedList<T>` | Node-based list operations or concatenation that justify per-node allocation and pointer chasing | nothing; avoiding buffer growth does not establish bounded allocation latency |
| `HashMap<K, V>` | Arbitrary keys mapped to values, a cache, a map with no extra functionality | `K: Eq + Hash` |
| `BTreeMap<K, V>` | Map sorted by key, ranges of entries on demand, the smallest or largest entry, the nearest key below or above a value | `K: Ord` |
| `HashSet<T>` / `BTreeSet<T>` | Remembering which keys were seen, membership without an associated value | same as the map |
| `BinaryHeap<T>` | Always processing the "biggest" or "most important" element next, a priority queue | `T: Ord` |

A closed set of known keys is often better served by an `enum` with a `match` or an array indexed by the enum than by a map.

## Operation Costs

`n` is the collection size, `m` a second collection, `i` an index; `*` marks amortized cost, `~` expected cost. Map lookup/insertion/removal use keys rather than sequence indices. These bounds treat a key comparison or hash as a unit cost; long strings can make that assumption significant.

| | `get(i)` | `insert(i)` | `remove(i)` | `append` | `split_off(i)` | `range` |
|---|---|---|---|---|---|---|
| `Vec` | O(1) | O(n−i)* | O(n−i) | O(m)* | O(n−i) | n/a |
| `VecDeque` | O(1) | O(min(i, n−i))* | O(min(i, n−i)) | O(m)* | O(min(i, n−i)) | n/a |
| `LinkedList` | O(min(i, n−i)) | O(min(i, n−i)) | O(min(i, n−i)) | O(1) | O(min(i, n−i)) | n/a |
| `HashMap` | O(1)~ | O(1)~* | O(1)~ | n/a | n/a | n/a |
| `BTreeMap` | O(log n) | O(log n) | O(log n) | O(n+m) | n/a | O(log n) |

Set operations have the corresponding map's complexity. For similar operation counts, contiguous storage often reduces allocation and pointer chasing, but input shape and access patterns determine elapsed time. Removing Vec elements retains its capacity; dropping list nodes releases their individual allocations. Distinguish element removal, backing-storage capacity, and memory returned to the operating system.

## Capacity Management

Growth beyond capacity can reallocate and move elements. A credible size estimate can avoid repeated growth; buffer reuse trades fewer allocations against retained memory.

```rust
fn parse_numbers(lines: &[&str], expected: usize) -> Vec<u32> {
    let mut numbers = Vec::with_capacity(expected);
    for line in lines {
        if let Ok(n) = line.trim().parse::<u32>() {
            numbers.push(n);
        }
    }
    numbers.shrink_to_fit(); // only when the vector lives long and expected was a loose bound
    numbers
}

fn process_batches(batches: &[&[u8]]) -> usize {
    let mut scratch: Vec<u8> = Vec::new();
    let mut total = 0;
    for batch in batches {
        scratch.clear(); // keeps the allocation
        scratch.extend_from_slice(batch);
        scratch.retain(|b| b.is_ascii_alphanumeric());
        total += scratch.len();
    }
    total
}
```

- `Vec::new()` does not allocate. Vec does not guarantee a specific growth factor or initial capacity; zero-sized elements require no element allocation.
- `reserve(n)` asks for room for n additional elements beyond the current length. reserve_exact avoids deliberate speculative growth, but the allocator can still supply excess capacity.
- `capacity()` reports how many elements fit without reallocation by push/insert. Read it after reserving instead of assuming it equals the request. shrink_to_fit may retain excess capacity.
- `vec![0; n]` clearly requests an initialized zeroed buffer and can use efficient allocator paths. Its performance depends on element type, allocator, and target.
- A HashMap capacity counts entries and includes its own table/load-factor strategy; String capacity counts bytes. Do not transfer Vec growth assumptions to either one.

## Entry API

The entry API performs one lookup for get-or-insert and update-or-insert patterns. It exists on `HashMap` and `BTreeMap`.

```rust
use std::collections::HashMap;

fn word_counts(text: &str) -> HashMap<&str, usize> {
    let mut counts = HashMap::new();
    for word in text.split_whitespace() {
        *counts.entry(word).or_insert(0) += 1;
    }
    counts
}

struct RenderCache {
    rendered: HashMap<u64, String>,
}

impl RenderCache {
    fn get_or_render(&mut self, key: u64, render: impl FnOnce() -> String) -> &str {
        self.rendered.entry(key).or_insert_with(render)
    }

    fn touch(&mut self, key: u64) {
        self.rendered
            .entry(key)
            .and_modify(|s| s.push('!'))
            .or_insert_with(String::new);
    }
}
```

`or_insert_with` takes a closure so the value is built only when the key is absent; `or_insert(expensive())` evaluates the argument every time. `insert` on an existing key replaces the value but keeps the stored key object, which matters only when keys carry fields that do not take part in `Eq`/`Hash`.

## Hashing and HashDoS

`HashMap` uses SipHash 1-3 through `RandomState`, which the docs describe as "very competitive for medium sized keys" while "other hashing algorithms will outperform it for small keys such as integers as well as large keys such as long strings." The default resists HashDoS because every map is seeded randomly. Keys that come from untrusted input (request parameters, file contents) should keep the default.

For trusted keys on a measured hot path, swap the hasher through the `BuildHasher` parameter. The std-only form:

```rust
use std::collections::HashMap;
use std::hash::{BuildHasherDefault, Hasher};

/// Identity hash for keys that are already well distributed (database ids, random tokens).
#[derive(Default)]
struct IdentityHasher(u64);

impl Hasher for IdentityHasher {
    fn finish(&self) -> u64 {
        self.0
    }
    fn write(&mut self, _bytes: &[u8]) {
        unreachable!("IdentityHasher is only used with u64 keys");
    }
    fn write_u64(&mut self, n: u64) {
        self.0 = n;
    }
}

type IdMap<V> = HashMap<u64, V, BuildHasherDefault<IdentityHasher>>;

fn new_id_map<V>() -> IdMap<V> {
    IdMap::default()
}
```

Ecosystem hashers plug into the same parameter: `rustc_hash::FxHashMap` (fast, low quality, used inside the compiler), `ahash` (uses AES instructions where available), `fnv` (higher quality than Fx, a little slower), `nohash_hasher` (identity for already-random keys). Hasher changes can help or hurt depending on key distribution, hashing cost, and collision behavior. Compare the actual workload and retain protection appropriate for untrusted keys.

Never persist or compare hashes across processes or Rust versions: `DefaultHasher` and `RandomState` are explicitly not stable, and `RandomState` differs per map instance.

## Iteration Order and Determinism

`HashMap` and `HashSet` iterate in an arbitrary order that changes between runs. Anything observable (test output, serialized files, log lines, generated code) must sort first or use an ordered collection.

```rust
use std::collections::{BTreeMap, HashMap};

fn sorted_entries(map: &HashMap<String, u32>) -> Vec<(&str, u32)> {
    let mut entries: Vec<(&str, u32)> = map.iter().map(|(k, v)| (k.as_str(), *v)).collect();
    entries.sort_unstable_by(|a, b| a.0.cmp(b.0));
    entries
}

fn into_ordered(map: HashMap<String, u32>) -> BTreeMap<String, u32> {
    map.into_iter().collect()
}
```

`BTreeMap` iterators yield entries in key order at amortized constant time per item. A snapshot test that compares a `HashMap`'s `Debug` output is flaky by construction.

## Ordered Maps: Ranges, First and Last

`BTreeMap` answers "everything between", "the newest", and "the nearest key" without scanning.

```rust
use std::collections::BTreeMap;
use std::ops::Bound::{Excluded, Included};

struct Timeline {
    by_timestamp: BTreeMap<u64, String>,
}

impl Timeline {
    fn between(&self, start: u64, end: u64) -> impl Iterator<Item = (&u64, &String)> {
        self.by_timestamp.range((Included(start), Excluded(end)))
    }

    fn newest(&self) -> Option<(&u64, &String)> {
        self.by_timestamp.last_key_value()
    }

    fn latest_at_or_before(&self, ts: u64) -> Option<(&u64, &String)> {
        self.by_timestamp.range(..=ts).next_back()
    }

    fn drop_older_than(&mut self, cutoff: u64) {
        let keep = self.by_timestamp.split_off(&cutoff);
        self.by_timestamp = keep;
    }
}
```

Keys must implement `Ord` with a total order; a broken `Ord` produces a corrupt tree, a logic error whose consequences can include incorrect results or a panic; unsafe code cannot rely on trait implementations being logically correct for memory safety.

## Priority Queues

`BinaryHeap` is a max-heap. Wrap in `std::cmp::Reverse` for a min-heap, and implement `Ord` on a task struct to order by priority while keeping the payload out of the comparison.

```rust
use std::cmp::{Ordering, Reverse};
use std::collections::BinaryHeap;

#[derive(Debug, PartialEq, Eq)]
struct Job {
    priority: u8,
    sequence: u64, // tie-breaker so equal priorities run first-in first-out
    name: String,
}

impl Ord for Job {
    fn cmp(&self, other: &Self) -> Ordering {
        self.priority
            .cmp(&other.priority)
            .then_with(|| other.sequence.cmp(&self.sequence))
    }
}

impl PartialOrd for Job {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

fn next_job(queue: &mut BinaryHeap<Job>) -> Option<Job> {
    queue.pop()
}

fn smallest_first(values: &[u32]) -> BinaryHeap<Reverse<u32>> {
    values.iter().copied().map(Reverse).collect()
}
```

`Ord`, `PartialOrd`, `Eq`, and `PartialEq` must agree; deriving `PartialOrd` while hand-writing `Ord` is a deny-level Clippy correctness lint (`derive_ord_xor_partial_ord`). `BinaryHeap::peek` is O(1), `pop` and `push` are O(log n), and `into_sorted_vec` returns ascending order.

## Queues and Sliding Windows

```rust
use std::collections::VecDeque;

struct SlidingWindow {
    samples: VecDeque<f64>,
    capacity: usize,
}

impl SlidingWindow {
    fn new(capacity: usize) -> Self {
        Self { samples: VecDeque::with_capacity(capacity), capacity }
    }

    fn push(&mut self, sample: f64) {
        if self.samples.len() == self.capacity {
            self.samples.pop_front();
        }
        self.samples.push_back(sample);
    }

    fn mean(&self) -> Option<f64> {
        if self.samples.is_empty() {
            return None;
        }
        Some(self.samples.iter().sum::<f64>() / self.samples.len() as f64)
    }
}
```

`VecDeque` is a ring buffer: both ends are O(1), indexing is O(1), and `make_contiguous` returns one slice when an algorithm needs contiguous memory. A `Vec` used as a FIFO with `remove(0)` shifts every element on each pop.

## Removing Elements

| Goal | Method | Cost and notes |
|---|---|---|
| Remove one element, order matters | `Vec::remove(i)` | O(n−i), shifts the tail |
| Remove one element, order irrelevant | `Vec::swap_remove(i)` | O(1), moves the last element into `i` |
| Keep elements matching a predicate | `retain` / `retain_mut` | one pass, in place |
| Move out elements matching a predicate | `extract_if(range, pred)` | one pass; returns an iterator of removed items (`Vec`/`LinkedList` 1.87, `HashMap`/`HashSet` 1.88, `BTreeMap`/`BTreeSet` 1.91) |
| Remove and yield a range | `drain(range)` | unconsumed items are dropped when the iterator drops |
| Remove from the front | `VecDeque::pop_front` | O(1) |
| Remove the last if it matches | `Vec::pop_if` (1.86), `VecDeque::pop_front_if` / `pop_back_if` (1.93) | O(1) |

```rust
struct Session {
    id: u64,
    expires_at: u64,
}

fn expire_sessions(sessions: &mut Vec<Session>, now: u64) -> Vec<Session> {
    // Rust 1.87+: removed sessions are returned so they can be logged or persisted.
    sessions.extract_if(.., |s| s.expires_at <= now).collect()
}

fn purge_quietly(sessions: &mut Vec<Session>, now: u64) {
    sessions.retain(|s| s.expires_at > now);
}
```

Removing during iteration with indices is the classic off-by-one bug; `retain`, `extract_if`, and `drain` exist so that loop never has to be written.

## Several Mutable Elements at Once

Borrowing two elements of one collection mutably used to need `split_at_mut` arithmetic or `unsafe`. Since 1.86, `get_disjoint_mut` checks index distinctness at runtime and returns all borrows.

```rust
fn transfer(balances: &mut [u64], from: usize, to: usize, amount: u64) -> Result<(), String> {
    let [from_balance, to_balance] = balances
        .get_disjoint_mut([from, to])
        .map_err(|e| e.to_string())?;
    *from_balance = from_balance
        .checked_sub(amount)
        .ok_or_else(|| "insufficient funds".to_string())?;
    *to_balance += amount;
    Ok(())
}
```

`HashMap::get_disjoint_mut([&k1, &k2])` does the same for maps. Below 1.86, `split_at_mut` for slices or restructuring the update (read both, then write both) are the safe options.

## Keys That Are Not Ord or Hash

Floats implement neither `Eq` nor `Ord` because of NaN. Give the key a total order explicitly with `f64::total_cmp`, and keep `PartialEq` consistent with `Ord` so that equal comparison and `Ordering::Equal` agree.

```rust
use std::cmp::Ordering;

#[derive(Debug, Clone, Copy)]
struct Score(f64);

impl PartialEq for Score {
    fn eq(&self, other: &Self) -> bool {
        self.cmp(other) == Ordering::Equal
    }
}
impl Eq for Score {}

impl PartialOrd for Score {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}
impl Ord for Score {
    fn cmp(&self, other: &Self) -> Ordering {
        self.0.total_cmp(&other.0)
    }
}
```

For hashing a float key, hash the bit pattern (`self.0.to_bits().hash(state)`) after normalizing `-0.0` and NaN payloads, or store an integer representation (cents instead of dollars). Sorting a `Vec<f64>` needs `sort_by(f64::total_cmp)`; `sort()` does not compile because `f64: !Ord`.

Keys with interior mutability (`Cell`, `RefCell`, `Mutex` inside the key) can change their hash while stored, which corrupts the map; Clippy `mutable_key_type` warns about it.

## Graphs and Trees Without Reference Cycles

Parent pointers and cycles fight the ownership model. The plain solution is an arena: nodes live in a `Vec`, and edges are indices wrapped in a newtype so they cannot be confused with other integers.

```rust
#[derive(Clone, Copy, PartialEq, Eq, Hash, Debug)]
struct NodeId(u32);

struct Node {
    label: String,
    parent: Option<NodeId>,
    children: Vec<NodeId>,
}

#[derive(Default)]
struct Tree {
    nodes: Vec<Node>,
}

impl Tree {
    fn add(&mut self, parent: Option<NodeId>, label: &str) -> NodeId {
        let id = NodeId(u32::try_from(self.nodes.len()).expect("node count fits u32"));
        self.nodes.push(Node { label: label.to_owned(), parent, children: Vec::new() });
        if let Some(parent) = parent {
            self.nodes[parent.0 as usize].children.push(id);
        }
        id
    }

    fn node(&self, id: NodeId) -> &Node {
        &self.nodes[id.0 as usize]
    }

    fn depth(&self, mut id: NodeId) -> usize {
        let mut depth = 0;
        while let Some(parent) = self.node(id).parent {
            depth += 1;
            id = parent;
        }
        depth
    }
}
```

Removal from an arena needs tombstones or generational indices so stale identifiers can be detected. Rc/Arc with Weak back-links suits nodes whose ownership is distributed: strong parent-to-child links can keep children alive without a strong cycle back to the parent. Choose the owning directions according to the graph's lifetime requirements.

## Static Lookup Tables

```rust
use std::collections::HashMap;
use std::sync::LazyLock;

static MIME_TYPES: LazyLock<HashMap<&'static str, &'static str>> = LazyLock::new(|| {
    HashMap::from([
        ("html", "text/html"),
        ("json", "application/json"),
        ("png", "image/png"),
    ])
});

fn mime_type(extension: &str) -> Option<&'static str> {
    MIME_TYPES.get(extension).copied()
}
```

`LazyLock` (1.80) replaces `lazy_static!` and `once_cell::sync::Lazy`. For a handful of entries, consider a match on string literals; measure size and lookup cost rather than promising it beats every map. For a large fixed key set, evaluate a static/perfect-hash representation and apply the library admission policy to new dependencies.

## Fixed-Length and Frozen Sequences

- `[T; N]` when the length is a compile-time constant; it lives inline without allocation.
- `Box<[T]>` for a heap sequence whose length is final: it drops the capacity word and signals that no pushes follow. `Vec::into_boxed_slice` reallocates only when `len != capacity`.
- `Vec<T>` stores elements inline; `Vec<Box<T>>` only pays off when `T` is large and elements are reordered often, or when element addresses must stay stable across pushes.
- smallvec can keep short sequences inline and spill to the heap; heapless offers fixed-capacity storage with explicit full handling. Inline capacity enlarges containing types. See [allocation strategy](memory-and-allocation.md) and [library selection](library-selection.md) before adopting one.

## Common Mistakes

- Using `LinkedList` for "fast insertion in the middle": finding the position is O(n) and every node is a separate allocation; `Vec` or `VecDeque` wins in practice.
- `contains_key` followed by `insert` (two lookups); use the entry API. Clippy `map_entry` flags this.
- Collecting into a `Vec` only to iterate it again; return `impl Iterator` or `extend` an existing collection.
- Depending on `HashMap` order in tests or output.
- Switching hashers for a map keyed by user input, which reintroduces HashDoS.
- Storing indices as bare `usize` across several arenas, then mixing them up; wrap each in its own newtype.
- Implementing `Hash` by hand while deriving `PartialEq` (or the reverse); equal values must hash equally (`derived_hash_with_manual_eq` is a Clippy correctness lint).
- Calling `Vec::remove(0)` in a loop to implement a queue.

## Availability by Version

| Version | Addition |
|---|---|
| 1.80 | `LazyLock`, `LazyCell`; `impl IntoIterator for Box<[T]>` |
| 1.83 | `hash_map::Entry::insert_entry` |
| 1.86 | `<[T]>::get_disjoint_mut`, `HashMap::get_disjoint_mut`, `Vec::pop_if` |
| 1.87 | `Vec::extract_if`, `LinkedList::extract_if`, `<[T]>::split_off_first`, `split_off_last` |
| 1.88 | `HashMap::extract_if`, `HashSet::extract_if`, `<[T]>::as_chunks`, `as_rchunks` |
| 1.91 | `BTreeMap::extract_if`, `BTreeSet::extract_if` |
| 1.92 | `btree_map::Entry::insert_entry` |
| 1.93 | `VecDeque::pop_front_if`, `pop_back_if`; `<[T]>::as_array` |
| 1.94 | `<[T]>::array_windows` |
| 1.95 | `Vec::push_mut`, `insert_mut`; `VecDeque::push_back_mut` |

Check the project's `rust-version` before using any of these; the per-release details live in [the versions index](../versions/index.md).

## Practical Boundaries

Container guarantees such as sorted iteration, uniqueness, and stable identifiers belong to the API contract. A faster lookup does not compensate for losing required ordering or using inconsistent Eq/Hash/Ord implementations.

Capacity reservation and reuse fit credible size estimates and repeated workloads; unusually large retained capacity can justify releasing a buffer. Entry, retain, drain, extract_if, and swap_remove express different mutation semantics, including whether order survives. Match those semantics before comparing timings or changing a hasher for trusted input.
