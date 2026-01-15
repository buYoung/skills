# Typst MCP Tools Reference

Available MCP tools for Typst document creation and validation.

## Available Tools

| Tool | Purpose |
|------|---------|
| `list_docs_chapters` | List all available Typst documentation chapters |
| `get_docs_chapter` | Get content of a specific documentation chapter |
| `get_docs_chapters` | Get multiple chapters at once |
| `check_if_snippet_is_valid_typst_syntax` | Validate Typst syntax |
| `check_if_snippets_are_valid_typst_syntax` | Validate multiple snippets |
| `latex_snippet_to_typst` | Convert LaTeX to Typst |
| `latex_snippets_to_typst` | Convert multiple LaTeX snippets |
| `typst_snippet_to_image` | Render Typst to preview image |

## Syntax Validation

### Single Snippet Validation

```
Tool: check_if_snippet_is_valid_typst_syntax
Input: "$f in K ( t^H , beta )_delta$"
Output: "VALID"
```

### Invalid Syntax Detection

```
Tool: check_if_snippet_is_valid_typst_syntax
Input: "$a = \frac{1}{2}$"
Output: "INVALID! Error message: unknown variable: rac..."
```

## LaTeX Conversion

### Convert LaTeX to Typst

```
Tool: latex_snippet_to_typst
Input: "$ f\in K ( t^ { H } , \beta ) _ { \delta } $"
Output: "$f in K ( t^H , beta )_delta$"
```

### Figure Conversion

```
Tool: latex_snippet_to_typst
Input: 
\begin{figure}[t]
    \includegraphics[width=8cm]{"placeholder.png"}
    \caption{Placeholder image}
    \label{fig:placeholder}
\end{figure}

Output:
#figure(image("placeholder.png", width: 8cm),
    caption: [
        Placeholder image
    ]
)
<fig:placeholder>
```

## Documentation Lookup

### List Chapters

```
Tool: list_docs_chapters
Output: List of all available documentation routes
```

### Get Chapter Content

```
Tool: get_docs_chapter
Input: "____reference____syntax"  (route with ____ instead of /)
Output: Full syntax documentation content
```

## Image Preview

### Render Snippet

```
Tool: typst_snippet_to_image
Input: "$sum_(i=1)^n i = (n(n+1))/2$"
Output: PNG image of rendered formula
```

## Common Routes

| Route | Content |
|-------|---------|
| `____reference____syntax` | Syntax reference |
| `____reference____styling` | Styling guide |
| `____reference____scripting` | Scripting reference |
| `____reference____math` | Math mode reference |
| `____reference____layout____page` | Page setup |
| `____reference____model____table` | Table reference |
| `____reference____model____figure` | Figure reference |
| `____guides____guide-for-latex-users` | LaTeX migration guide |

## Workflow Pattern

1. **Write Typst code** based on references
2. **Validate syntax** with `check_if_snippet_is_valid_typst_syntax`
3. **Fix errors** if validation fails
4. **Preview output** with `typst_snippet_to_image` (optional)
5. **Lookup documentation** with `get_docs_chapter` if needed
