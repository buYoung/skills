# Graphs and Trees

## Contents

- [Graphs and Trees Without Reference Cycles](#graphs-and-trees-without-reference-cycles)
- [Common Mistakes](#common-mistakes)

Examples use stable APIs unless marked otherwise; see [compatibility](../../SKILL.md#compatibility). Shared ownership with `Rc`, `Arc`, and `Weak` is in [ownership and borrowing](ownership-and-borrowing.md#shared-ownership-and-cycles); container choice in [collections](collections.md).

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

## Common Mistakes

- Storing indices as bare `usize` across several arenas, then mixing them up; wrap each in its own newtype.
