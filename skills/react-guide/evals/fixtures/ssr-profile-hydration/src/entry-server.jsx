import { renderToString } from 'react-dom/server';
import { Profile } from './Profile.jsx';
import { profileStore } from './profileStore.mjs';

export async function renderPage({ requestId, loadProfile }) {
  profileStore.replace(await loadProfile());
  await Promise.resolve();
  const renderedAt = new Date().toISOString();
  const html = renderToString(<Profile store={profileStore} renderedAt={renderedAt} />, { identifierPrefix: requestId });
  return `<!doctype html><html><head><title>Profile</title></head><body><div id="root">${html}</div><script type="module" src="/assets/client.js"></script></body></html>`;
}
