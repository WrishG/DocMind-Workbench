import { create } from 'zustand';

const getInitialTheme = () => {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem('docmind-theme');
    if (saved) return saved;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  return 'dark';
};

export const useStore = create((set, get) => ({
  documents: [],
  activeDocument: null,
  theme: getInitialTheme(),

  // Chat history keyed by document ID so switching docs preserves conversations
  chatHistories: {},

  setDocuments: (docs) => set({ documents: docs }),
  setActiveDocument: (doc) => set({ activeDocument: doc }),

  toggleTheme: () => set((state) => {
    const next = state.theme === 'dark' ? 'light' : 'dark';
    localStorage.setItem('docmind-theme', next);
    return { theme: next };
  }),

  // Get messages for the currently active document
  getMessages: () => {
    const state = get();
    if (!state.activeDocument) return [];
    return state.chatHistories[state.activeDocument._id] || [];
  },

  // Add a message to the active document's chat
  addMessage: (msg) => set((state) => {
    if (!state.activeDocument) return {};
    const docId = state.activeDocument._id;
    const existing = state.chatHistories[docId] || [];
    return {
      chatHistories: {
        ...state.chatHistories,
        [docId]: [...existing, msg],
      },
    };
  }),

  // Set the entire history for a specific document
  setChatHistory: (docId, messages) => set((state) => ({
    chatHistories: {
      ...state.chatHistories,
      [docId]: messages,
    },
  })),
}));
