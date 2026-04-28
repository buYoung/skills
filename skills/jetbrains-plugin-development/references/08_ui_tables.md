# Tables

## Tables — `JBTable`, `TableView`, `ListTableModel`

```kotlin
data class Row(val name: String, val count: Int)

val columns = arrayOf(
  object : ColumnInfo<Row, String>("Name") {
    override fun valueOf(item: Row): String = item.name
  },
  object : ColumnInfo<Row, Int>("Count") {
    override fun valueOf(item: Row): Int = item.count
    override fun getColumnClass(): Class<*> = Integer::class.javaObjectType
    override fun isCellEditable(item: Row): Boolean = true
    override fun setValue(item: Row, value: Int) { /* mutate row, refresh model */ }
  },
)

val model = ListTableModel(columns, mutableListOf<Row>())
val table = TableView(model).apply {
  setShowGrid(false)
  emptyText.text = "No entries"
}
val scrollable = JBScrollPane(table)
```

`TableView` extends `JBTable`; both inherit IDE styling and Speed Search. For very simple
read-only lists, `JBList` + a `DefaultListModel` is enough — escalate to `TableView` when
you need columns, sorting, or per-row editors.

`ColumnInfo` overrides:
- `valueOf(item)` — required, the cell's display value.
- `getColumnClass()` — drives the default renderer (number columns right-align).
- `isCellEditable(item)` / `getEditor(item)` / `setValue(item, value)` — make a column
  editable.
- `getRenderer(item)` — custom Swing renderer.

`TableView`-specific helpers like `setSelection(items)` work in object terms rather than
row indices, which is what you want when the model can be sorted or filtered.
