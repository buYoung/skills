export function createProfileStore(initialProfile) {
  let profile = initialProfile;
  const listeners = new Set();
  return {
    getSnapshot() { return { ...profile }; },
    getServerSnapshot() { return profile; },
    subscribe(listener) { listeners.add(listener); return () => listeners.delete(listener); },
    replace(nextProfile) { profile = nextProfile; listeners.forEach((listener) => listener()); },
    increment() { profile.visits += 1; listeners.forEach((listener) => listener()); }
  };
}

export const profileStore = createProfileStore({ name: 'Guest', visits: 0 });
