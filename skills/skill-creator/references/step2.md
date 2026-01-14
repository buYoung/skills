# Step 2: Structure Planning

Decide file structure based on complexity.

## Structure Decision Tree

```
Simple (single domain, <100 lines expected):
└── SKILL.md only

Medium (multi-domain or detailed specs):
├── SKILL.md
└── references/

Complex (executable code + docs + templates):
├── SKILL.md
├── scripts/
├── references/
└── assets/
```

## Directory Purposes

| Directory | Purpose | When to Include |
|-----------|---------|-----------------|
| `scripts/` | Executable code | Deterministic reliability needed, repeated code |
| `references/` | Documentation | Detailed specs, schemas, domain knowledge |
| `assets/` | Output resources | Templates, images, boilerplate for final output |
