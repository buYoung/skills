export function createGridStore(initialRows) {
  let ids = initialRows.map((row) => row.id);
  const rows = new Map(initialRows.map((row) => [row.id, Object.freeze({ ...row })]));
  const globalListeners = new Set();
  const idListeners = new Set();
  const rowListeners = new Map();

  function emitRow(id) {
    for (const listener of rowListeners.get(id) ?? []) listener();
    for (const listener of globalListeners) listener();
  }

  return {
    getSnapshot: () => ({ ids, rows }),
    subscribe: (listener) => {
      globalListeners.add(listener);
      return () => globalListeners.delete(listener);
    },
    getIds: () => ids,
    subscribeIds: (listener) => {
      idListeners.add(listener);
      return () => idListeners.delete(listener);
    },
    getRow: (id) => rows.get(id),
    subscribeRow: (id, listener) => {
      const listeners = rowListeners.get(id) ?? new Set();
      listeners.add(listener);
      rowListeners.set(id, listeners);
      return () => listeners.delete(listener);
    },
    updatePrice(id, price) {
      const current = rows.get(id);
      rows.set(id, Object.freeze({ ...current, price }));
      emitRow(id);
    },
    replaceIds(nextIds) {
      ids = nextIds;
      for (const listener of idListeners) listener();
      for (const listener of globalListeners) listener();
    }
  };
}
