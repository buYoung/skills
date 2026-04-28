# UI Data Context

## `UiDataProvider` / `DataContext` — passing context to actions

Custom data keys let actions read data from your UI:

```kotlin
val MY_SELECTED_ITEM_KEY: DataKey<MyItem> = DataKey.create("com.example.MyItem")

myComponent.putClientProperty(DataConstants.DATA_PROVIDER, DataProvider { id ->
  if (MY_SELECTED_ITEM_KEY.`is`(id)) selectedItem else null
})
```

Modern alternative — `UiDataProvider`:

```kotlin
class MyPanel : JPanel(), UiDataProvider {
  override fun uiDataSnapshot(sink: DataSink) {
    sink[MY_SELECTED_ITEM_KEY] = selectedItem
  }
}
```

Actions can then call `e.getData(MY_SELECTED_ITEM_KEY)`.
