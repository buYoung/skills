import { hydrateRoot } from 'react-dom/client';
import { Profile } from './Profile.jsx';
import { createProfileStore } from './profileStore.mjs';

const cachedProfile = JSON.parse(localStorage.getItem('profile') || '{"name":"Guest","visits":0}');
const store = createProfileStore(cachedProfile);
hydrateRoot(
  document.getElementById('root'),
  <Profile store={store} renderedAt={new Date().toISOString()} />,
  { identifierPrefix: 'client-' }
);
