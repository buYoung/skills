import { useState, useSyncExternalStore } from 'react';

export function Grid({ store }) {
  const snapshot = useSyncExternalStore(store.subscribe, store.getSnapshot, store.getSnapshot);
  return (
    <div role="grid">
      {snapshot.ids.map((id) => (
        <GridRow key={id} row={snapshot.rows.get(id)} />
      ))}
    </div>
  );
}

export function GridRow({ row }) {
  const [draft, setDraft] = useState(row.note ?? '');
  return (
    <div role="row" data-row-id={row.id}>
      <span role="gridcell">{row.name}</span>
      <span role="gridcell">{row.price}</span>
      <input aria-label={`${row.name} draft`} value={draft} onChange={(event) => setDraft(event.target.value)} />
    </div>
  );
}
