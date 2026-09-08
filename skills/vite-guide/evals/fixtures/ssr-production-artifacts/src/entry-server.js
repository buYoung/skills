import { releaseLabel } from '@fixture/banner';
import '@fixture/theme';

export async function render(url, manifest) {
  const files = manifest['src/entry-client.js'] || [];
  const preloadLinks = files.map((file) => file.endsWith('.css')
    ? `<link rel="stylesheet" href="${file}">`
    : `<link rel="modulepreload" href="${file}">`).join('');
  // Server-only; never serialize this value into HTML or import it from the client.
  const token = process.env.INTERNAL_API_TOKEN;
  if (token === '') throw new Error('Invalid server token configuration');
  return { html: `<h1>${releaseLabel}</h1><button id="counter">0</button>`, preloadLinks };
}
