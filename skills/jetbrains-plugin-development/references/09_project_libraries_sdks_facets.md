# Libraries, SDKs, and Facets

## Libraries

```kotlin
// project-wide library table
val table = LibraryTablesRegistrar.getInstance().getLibraryTable(project)
val libs: Array<Library> = table.libraries

// modify
WriteAction.runAndWait<Throwable> {
  val modTable = table.modifiableModel
  val newLib = modTable.createLibrary("my-library")
  val modLib = newLib.modifiableModel
  modLib.addRoot(jarFile, OrderRootType.CLASSES)
  modLib.commit()
  modTable.commit()
}
```

`AdditionalLibraryRootsProvider` exposes "synthetic" libraries (e.g., language runtimes
auto-detected from the project). Returned `SyntheticLibrary` objects participate in
`ProjectFileIndex` as library classes/sources without a real `LibraryEntity`.

```xml
<additionalLibraryRootsProvider implementation="com.example.MyRootsProvider"/>
```

## SDKs (JDK and others)

```kotlin
val projectSdk = ProjectRootManager.getInstance(project).projectSdk
val moduleSdk  = ModuleRootManager.getInstance(module).sdk

projectSdk?.name
projectSdk?.homePath
projectSdk?.sdkType
```

The IDE-wide SDK registry is `ProjectJdkTable.getInstance()`. Custom SDK types implement
`SdkType` and register `<sdkType>`. To validate the SDK at project setup time, implement
`ProjectSdkSetupValidator` and register `<projectSdkSetupValidator>` — the IDE shows a
notification when validation fails.

## Facets

A facet attaches per-module, per-technology configuration on top of the base module model
(e.g. Spring facet, Web facet, Android facet).

```kotlin
val facetManager = FacetManager.getInstance(module)
val mySpringFacet = facetManager.getFacetByType(SpringFacet.FACET_TYPE_ID)
val allFacets: Array<Facet<*>> = facetManager.allFacets
```

Implement `FacetType<F, C>` (where `C` is a `FacetConfiguration` you persist) and register
`<facetType>` to add a new kind. Default usage is to **read** existing facets to gate
behavior (e.g., "this is a Web module, enable my web feature").
