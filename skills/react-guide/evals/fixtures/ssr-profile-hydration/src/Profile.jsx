import { useId, useState, useSyncExternalStore } from 'react';

function NoteEditor({ noteId }) {
  const [note, setNote] = useState('');
  return <><label htmlFor={noteId}>Note</label><input id={noteId} value={note} onChange={(event) => setNote(event.target.value)} /></>;
}

export function Profile({ store, renderedAt }) {
  const profile = useSyncExternalStore(store.subscribe, store.getSnapshot, store.getServerSnapshot);
  const noteId = useId();
  return <main>
    <h1>{profile.name}</h1>
    <time>{new Date().toISOString()}</time>
    <p>Visits: {profile.visits}</p>
    <button onClick={() => store.increment()}>Visit</button>
    <NoteEditor key={profile.visits} noteId={noteId} />
  </main>;
}
