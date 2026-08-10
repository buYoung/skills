# Dry-run findings

- The package manager resolves `vite` through a temporary package override instead of the stable package.
- Dependency optimization reports a compatibility conversion for an esbuild-era nested option.
- Production output reports that the configured Rollup output path is deprecated under the native bundler.
- The existing object-style chunk declaration is rejected rather than converted.
- The explicit esbuild minifier selection is not available on the target path.
- No install or production build has been run after these findings were copied into the fixture.
