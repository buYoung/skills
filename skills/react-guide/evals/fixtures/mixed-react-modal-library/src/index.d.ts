import type { ReactNode, Ref } from 'react';

export interface ModalProps {
  ref?: Ref<HTMLDivElement>;
  open: boolean;
  onClose(): void;
  labelledBy: string;
  children?: ReactNode;
}

export declare function Modal(props: ModalProps): ReactNode;
export default Modal;
export declare function ModalProvider(props: { children?: ReactNode }): ReactNode;
export declare function useModalController(): {
  activeModal: string | null;
  setActiveModal(value: string | null): void;
};
