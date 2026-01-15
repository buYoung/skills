# Typst Math Reference

Mathematical notation syntax in Typst.

## Function Parameters

These functions provide fine-grained control over mathematical typesetting when the shorthand syntax isn't sufficient.

### `equation` Function

The wrapper for all math content. Usually implicit, but use explicitly for numbering control or advanced configuration.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `block` | bool | `false` | Display as block (centered) equation |
| `numbering` | none \| str \| func | `none` | Equation number format: `"(1)"`, `"[1]"` |
| `number-align` | alignment | `end + horizon` | Number alignment |
| `supplement` | auto \| none \| content | `auto` | Reference prefix (e.g., "Equation") |
| `body` | content | required | Equation content |

### `mat` Function (Matrix)

Creates matrices with customizable delimiters and alignment. Rows are separated by semicolons, columns by commas.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `delim` | none \| str | `"("` | Delimiter: `"("`, `"["`, `"{"`, `"|"`, `"||"` |
| `align` | alignment | `center` | Cell alignment |
| `augment` | none \| int \| dict | `none` | Augmentation line position |
| `gap` | relative | `0pt` | Gap between cells |
| `row-gap` | relative | `0.2em` | Gap between rows |
| `column-gap` | relative | `0.5em` | Gap between columns |
| `rows` | content | required | Matrix rows (`;` separated) |

### `vec` Function (Vector)

Creates column vectors. Elements are stacked vertically with configurable delimiters.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `delim` | none \| str | `"("` | Delimiter: `"("`, `"["`, `"{"`, `"|"`, `"||"` |
| `align` | alignment | `center` | Element alignment |
| `gap` | relative | `0.2em` | Gap between elements |
| `children` | content | required | Vector elements (`,` separated) |

### `frac` Function (Fraction)

Explicit fraction function for when the `/` shorthand produces unwanted grouping or styling.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `num` | content | required | Numerator |
| `denom` | content | required | Denominator |

### `cases` Function

Creates piecewise function definitions with conditions. Each case is separated by commas.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `delim` | str | `"{"` | Delimiter |
| `reverse` | bool | `false` | Place delimiter on right |
| `gap` | relative | `0.2em` | Gap between rows |
| `children` | content | required | Case rows (`,` separated) |

### `cancel` Function

Draws a strikethrough line through content, commonly used to show cancellation in algebraic simplification.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `body` | content | required | Content to cancel |
| `length` | relative | `100% + 3pt` | Line length |
| `inverted` | bool | `false` | Invert line angle |
| `cross` | bool | `false` | Draw X instead of line |
| `angle` | auto \| angle | `auto` | Line angle |
| `stroke` | stroke | `0.5pt` | Line stroke |

### `accent` Function

Places diacritical marks above mathematical symbols. Use for vectors, estimates, averages, and other notations.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base` | content | required | Base content |
| `accent` | str \| content | required | Accent: `hat`, `tilde`, `macron`, `dot`, `dot.double`, `arrow` |
| `size` | auto \| relative | `auto` | Accent size |

## Math Mode Entry

The presence of spaces after `$` determines whether math renders inline or as a centered block. This is the most important distinction for equation layout.

| Type | Syntax | Result |
|------|--------|--------|
| Inline | `$x^2$` | Inline equation |
| Block | `$ x^2 $` (with spaces) | Centered equation |

## Basic Notation

Core syntax for mathematical expressions. Use parentheses to group complex sub/superscripts.

### Subscripts and Superscripts

Use `_` for subscripts and `^` for superscripts. Wrap multi-character expressions in parentheses.

```typst
$x^2$           // x squared
$x_1$           // x subscript 1
$x_1^2$         // both
$x^(2n)$        // grouped exponent
$x_(i j)$       // grouped subscript
```

### Fractions

The `/` operator creates fractions automatically. Parentheses control grouping. Use `frac()` for explicit control.

```typst
$a/b$               // simple fraction
$(a + b)/(c + d)$   // grouped fraction
$frac(a, b)$        // explicit fraction function
```

### Roots

Square roots use `sqrt()`. For other roots, use `root(n, x)` where `n` is the root degree.

```typst
$sqrt(x)$           // square root
$root(3, x)$        // cube root
$root(n, x)$        // nth root
```

## Common Functions

Standard mathematical functions are recognized automatically and rendered in upright text. Limits and bounds attach with subscripts.

```typst
$sin(x)$, $cos(x)$, $tan(x)$
$log(x)$, $ln(x)$, $exp(x)$
$lim_(x -> 0) f(x)$
$max(a, b)$, $min(a, b)$
```

## Sums and Products

Large operators like summation, product, and integral accept limits via subscript/superscript syntax. Use `dif` for differential notation.

```typst
$sum_(i=1)^n i$             // summation
$product_(i=1)^n i$         // product
$integral_0^1 f(x) dif x$   // integral
```

## Matrices and Vectors

Matrices use semicolons for row breaks and commas for column separation. Vectors are single-column matrices.

```typst
// Vector
$vec(x, y, z)$

// Matrix
$mat(
  1, 2, 3;
  4, 5, 6;
  7, 8, 9;
)$

// Matrix with delimiters
$mat(delim: "[",
  a, b;
  c, d;
)$
```

## Brackets and Delimiters

Use `lr()` for auto-scaling delimiters that grow with content. Special functions like `abs()`, `norm()`, `floor()`, and `ceil()` provide semantic delimiters.

```typst
$(a + b)$           // parentheses
$[a + b]$           // brackets
${a + b}$           // braces (use lr for scaling)
$lr(( a/b ))$       // auto-scaling
$abs(x)$            // absolute value
$norm(x)$           // norm
$floor(x)$          // floor
$ceil(x)$           // ceiling
```

## Greek Letters

Greek letters are written by name without any prefix. Lowercase names produce lowercase letters; capitalize the first letter for uppercase.

| Letter | Typst | Letter | Typst |
|--------|-------|--------|-------|
| α | `alpha` | ν | `nu` |
| β | `beta` | ξ | `xi` |
| γ | `gamma` | π | `pi` |
| δ | `delta` | ρ | `rho` |
| ε | `epsilon` | σ | `sigma` |
| ζ | `zeta` | τ | `tau` |
| η | `eta` | υ | `upsilon` |
| θ | `theta` | φ | `phi` |
| ι | `iota` | χ | `chi` |
| κ | `kappa` | ψ | `psi` |
| λ | `lambda` | ω | `omega` |
| μ | `mu` | | |

Capital letters: `Alpha`, `Beta`, `Gamma`, `Delta`, `Theta`, `Lambda`, `Pi`, `Sigma`, `Phi`, `Psi`, `Omega`

## Operators and Symbols

Common mathematical operators and symbols. Use these names directly in math mode without any prefix.

```typst
$+$, $-$, $times$, $div$
$=$, $!=$, $<$, $>$, $<=$, $>=$
$approx$, $equiv$, $prop$
$in$, $not in$, $subset$, $supset$
$union$, $sect$               // set operations
$and$, $or$, $not$            // logical
$forall$, $exists$            // quantifiers
$infinity$, $emptyset$
$arrow$, $arrow.l$, $arrow.double$
$partial$, $nabla$            // calculus
```

## Alignment

Use `&` as alignment points and `\` for line breaks. Multiple equations align at the `&` symbols across lines.

```typst
// Multi-line aligned equations
$ x &= 2 + 3 \
    &= 5 $

// Equation numbering
#set math.equation(numbering: "(1)")
$ E = m c^2 $
```

## Cases

Piecewise function notation using the `cases` function. Separate conditions with `&` and cases with commas.

```typst
$f(x) = cases(
  0 &"if" x < 0,
  1 &"if" x >= 0,
)$
```

## Text in Math

Wrap regular text in quotes to include it in equations. Quoted text renders in the document's text font rather than math italics.

```typst
$x "where" x > 0$
$"area" = pi r^2$
```

## Accents

Mathematical accents and diacritical marks for vectors, estimates, derivatives, and other notations.

```typst
$accent(x, hat)$      // x̂
$accent(x, tilde)$    // x̃
$accent(x, macron)$   // x̄ (bar)
$accent(x, dot)$      // ẋ
$accent(x, dot.double)$  // ẍ
$accent(x, arrow)$    // x→
$overline(x y)$       // overline
$underline(x y)$      // underline
```

## Cancel and Strikethrough

Show algebraic cancellation or struck-out terms. Useful for demonstrating simplification steps.

```typst
$cancel(x)$           // strikethrough
$cancel(x, cross: true)$  // X mark
```

## Spacing in Math

Typst automatically handles spacing in math mode. Override with explicit spaces when needed for clarity.

```typst
$a b$               // implicit multiplication (thin space)
$a " " b$           // explicit space
$a med b$           // medium space
$a thick b$         // thick space
```
