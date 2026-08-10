import { createContext, useContext, useMemo, useState } from 'react';

const ModalContext = createContext(null);

export function ModalProvider({ children }) {
  const [activeModal, setActiveModal] = useState(null);
  const value = useMemo(() => ({ activeModal, setActiveModal }), [activeModal]);
  return <ModalContext value={value}>{children}</ModalContext>;
}

export function useModalController() {
  const value = useContext(ModalContext);
  if (!value) throw new Error('useModalController requires ModalProvider');
  return value;
}
