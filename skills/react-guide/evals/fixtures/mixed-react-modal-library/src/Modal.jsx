import { useEffect } from 'react';

export function Modal({ ref, open, onClose, labelledBy, children }) {
  useEffect(() => {
    if (!open) return undefined;
    const onKeyDown = (event) => {
      if (event.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div ref={ref} role="dialog" aria-modal="true" aria-labelledby={labelledBy}>
      {children}
    </div>
  );
}
