# UI Data Context

## `UiDataProvider` / `DataContext` — passing context to actions

Custom data keys let actions read data from your UI. On 2024.2+ (branch `242`), implement `UiDataProvider` on the component that owns the data:

```kotlin
val MY_SELECTED_ITEM_KEY: DataKey<MyItem> = DataKey.create("com.example.MyItem")

class MyPanel : JPanel(), UiDataProvider {
  override fun uiDataSnapshot(sink: DataSink) {
    sink[MY_SELECTED_ITEM_KEY] = selectedItem
  }
}
```

For a component you do not subclass, wrap it instead (`wrapComponent` is 2024.3+):

```kotlin
val wrapped: JComponent = UiDataProvider.wrapComponent(myTree) { sink ->
  sink[MY_SELECTED_ITEM_KEY] = selectedItem
}
```

Actions can then call `e.getData(MY_SELECTED_ITEM_KEY)`. `uiDataSnapshot` is called on the EDT; for a value that is expensive to compute, use `sink.lazy(MY_SELECTED_ITEM_KEY) { … }`, which registers it as a background data provider.

`UiDataProvider` does not exist on 2024.1 (`241`). A plugin that still supports that branch keeps the older pattern there: the component itself implements `DataProvider` and answers `getData(dataId)`. `DataProvider` is `@ApiStatus.Obsolete` from 2024.3, so use it only on the branch that needs it. Do not register providers through `DataConstants` or `DataManager.registerDataProvider(...)`: both are deprecated for removal, and `DataConstants` has no `DATA_PROVIDER` field.

Checked at `idea/2026.3`, commit `c91871ae2864649d952825cff72569e3db0e7ac6`: [`UiDataProvider.kt`](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/core-ui/src/openapi/actionSystem/UiDataProvider.kt), [`DataProvider.java`](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/core-ui/src/openapi/actionSystem/DataProvider.java), [`DataConstants.java`](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/platform-api/src/com/intellij/openapi/actionSystem/DataConstants.java), and [`DataManager.java`](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/editor-ui-api/src/com/intellij/ide/DataManager.java). The version boundaries come from the 2024.2 and 2024.3 release builds `idea/242.20224.300` and `idea/243.21565.193`.
