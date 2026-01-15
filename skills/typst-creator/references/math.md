# Typst Math Reference

Mathematical notation syntax in Typst.

## Math Mode Entry

| Type | Syntax | Result |
|------|--------|--------|
| Inline | `$x^2$` | Inline equation |
| Block | `$ x^2 $` (with spaces) | Centered equation |

## Basic Notation

### Subscripts and Superscripts

```typst
$x^2$           // x squared
$x_1$           // x subscript 1
$x_1^2$         // both
$x^(2n)$        // grouped exponent
$x_(i j)$       // grouped subscript
```

### Fractions

```typst
$a/b$               // simple fraction
$(a + b)/(c + d)$   // grouped fraction
$frac(a, b)$        // explicit fraction function
```

### Roots

```typst
$sqrt(x)$           // square root
$root(3, x)$        // cube root
$root(n, x)$        // nth root
```

## Common Functions

```typst
$sin(x)$, $cos(x)$, $tan(x)$
$log(x)$, $ln(x)$, $exp(x)$
$lim_(x -> 0) f(x)$
$max(a, b)$, $min(a, b)$
```

## Sums and Products

```typst
$sum_(i=1)^n i$             // summation
$product_(i=1)^n i$         // product
$integral_0^1 f(x) dif x$   // integral
```

## Matrices and Vectors

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

```typst
// Multi-line aligned equations
$ x &= 2 + 3 \
    &= 5 $

// Equation numbering
#set math.equation(numbering: "(1)")
$ E = m c^2 $
```

## Cases

```typst
$f(x) = cases(
  0 &"if" x < 0,
  1 &"if" x >= 0,
)$
```

## Text in Math

```typst
$x "where" x > 0$
$"area" = pi r^2$
```

## Accents

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

```typst
$cancel(x)$           // strikethrough
$cancel(x, cross: true)$  // X mark
```

## Spacing in Math

```typst
$a b$               // implicit multiplication (thin space)
$a " " b$           // explicit space
$a med b$           // medium space
$a thick b$         // thick space
```
