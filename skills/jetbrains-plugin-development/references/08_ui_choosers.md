# Choosers

## File, class, and reference choosers

The platform ships ready-made pickers; replicating them with custom Swing trees almost
always yields a worse UX (no Speed Search, no preview, no project-aware filtering).

```kotlin
// Pick a file from the project, restricted to one file type
val descriptor = FileChooserDescriptorFactory
  .createSingleFileDescriptor(SimpleFileType)
  .withTitle("Select Input")
  .withDescription("Pick a .simple file inside the project")
val chosen: VirtualFile? = FileChooser.chooseFile(descriptor, project, /* toSelect = */ null)
```

```kotlin
// Pick a directory under the project
val dir = FileChooser.chooseFile(
  FileChooserDescriptorFactory.createSingleFolderDescriptor(),
  project, /* toSelect = */ null
)
```

```kotlin
// Pick a Java/Kotlin class — backed by the class index, supports Speed Search
val chooser = TreeClassChooserFactory.getInstance(project)
  .createAllProjectScopeChooser("Choose Target Class")
chooser.showDialog()
val selected: PsiClass? = chooser.selected
```

```kotlin
// Pick a file from the project tree (no descriptor restriction)
val fileChooser = TreeFileChooserFactory.getInstance(project)
  .createFileChooser("Pick a File", /* initial = */ null, /* type = */ null,
                     /* filter = */ null, /* disableStructureProviders = */ false)
fileChooser.showDialog()
val pickedFile = fileChooser.selectedFile
```

For text-based "Goto Symbol/Class/File"-style flows inside your own UI, plug into
`ChooseByNameContributorEx` and reuse the platform's popup. See
`06_code_insight_parameter_info_and_navigation.md`.
