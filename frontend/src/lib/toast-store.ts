import { create } from 'zustand';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

interface ToastStore {
  toasts: Toast[];
  add: (message: string, type?: ToastType) => void;
  remove: (id: string) => void;
}

let _counter = 0;
function uid(): string {
  return `toast-${++_counter}-${Date.now()}`;
}

export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],

  add: (message, type = 'info') => {
    const id = uid();
    set((state) => ({
      toasts: [...state.toasts, { id, message, type }],
    }));
  },

  remove: (id) => {
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    }));
  },
}));

export function toast(message: string, type?: ToastType) {
  useToastStore.getState().add(message, type);
}
