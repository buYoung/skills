import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { createServer } from 'vite';

export async function createPageHandler({ isProduction, root }) {
  const vite = await createServer({ root, server: { middlewareMode: true }, appType: 'custom' });
  return async (url) => {
    const template = await readFile(path.join(root, 'index.html'), 'utf8');
    const transformed = await vite.transformIndexHtml(url, template);
    const { render } = await vite.ssrLoadModule('/src/entry-server.js');
    const manifest = isProduction ? JSON.parse(await readFile(path.join(root, 'dist/server/.vite/ssr-manifest.json'), 'utf8')) : {};
    const { html, preloadLinks } = await render(url, manifest);
    return transformed.replace('<!--app-html-->', html).replace('<!--preload-links-->', preloadLinks);
  };
}
