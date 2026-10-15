import { basename, resolve } from "node:path";

export function describeWorkspace(cwd: string) {
  const path = resolve(cwd);
  return { name: basename(path) || path, path };
}
