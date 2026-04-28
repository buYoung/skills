# Formatter and Commenter

## Formatter — `FormattingModelBuilder` and `Block`

```java
public class MyFormattingModelBuilder implements FormattingModelBuilder {
  @Override public @NotNull FormattingModel createModel(@NotNull FormattingContext ctx) {
    PsiFile file = ctx.getPsiFile();
    CodeStyleSettings settings = ctx.getCodeStyleSettings();
    MyBlock root = new MyBlock(file.getNode(),
                               Wrap.createWrap(WrapType.NONE, false),
                               Alignment.createAlignment(),
                               buildSpacing(settings));
    return FormattingModelProvider.createFormattingModelForPsiFile(file, root, settings);
  }
}
```

```xml
<lang.formatter language="MyLang"
                implementationClass="com.example.MyFormattingModelBuilder"/>
```

`Block` (typically `extends AbstractBlock`) describes one node's formatting:
- `getSubBlocks()` — children, computed by walking the PSI.
- `getIndent()`, `getAlignment()`, `getWrap()` — per-block.
- `getSpacing(child1, child2)` — usually delegated to a `SpacingBuilder` DSL.
- `getChildAttributes(newChildIndex)` — indent rule when the user presses Enter.
- `isIncomplete()` — true when the syntactic node is unfinished (open brace, unclosed paren).
- `isLeaf()` — true when there's nothing to descend into.

Block ranges should not overlap and must cover the file's non-whitespace text.

## `Commenter` — line/block comment toggling

```java
public class MyCommenter implements Commenter {
  @Override public String getLineCommentPrefix()      { return "#"; }
  @Override public String getBlockCommentPrefix()     { return "/*"; }
  @Override public String getBlockCommentSuffix()     { return "*/"; }
  @Override public String getCommentedBlockCommentPrefix() { return null; }
  @Override public String getCommentedBlockCommentSuffix() { return null; }
}
```

```xml
<lang.commenter language="MyLang" implementationClass="com.example.MyCommenter"/>
```

`Ctrl+/` (line) and `Ctrl+Shift+/` (block) both rely on this.
