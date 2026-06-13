import { create } from 'zustand';

// This is our Global App State
export const useStore = create((set) => ({
    documents: [],          // The list of uploaded PDFs
    activeDocument: null,   // The PDF the user is currently looking at

    // Actions to update the state
    setDocuments: (docs) => set({ documents: docs }),
    setActiveDocument: (doc) => set({ activeDocument: doc }),
}));
