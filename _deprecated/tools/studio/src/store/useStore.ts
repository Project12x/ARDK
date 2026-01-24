import { create } from 'zustand';

export interface OracleProposal {
    title: string;
    description: string;
    data: any;
    onConfirm: () => Promise<void> | void;
}

// Stash
export interface StashItem {
    id: string; // Unique ID for the stash entry
    originalId: number | string;
    type: 'inventory' | 'asset' | 'project' | 'task' | 'note' | 'goal' | 'routine' | string;
    title: string;
    subtitle?: string;
    data?: any; // payload for dropping
}

interface UIState {
    sidebarOpen: boolean;
    toggleSidebar: () => void;
    currentProjectId: number | null;
    setCurrentProjectId: (id: number | null) => void;

    // Ingestion State
    isIngesting: boolean;
    ingestMessage: string;
    setIngesting: (isIngesting: boolean, message?: string) => void;

    // Global Modals
    isCreateProjectOpen: boolean;
    setCreateProjectOpen: (open: boolean) => void;

    // Oracle Action System
    oracleProposal: OracleProposal | null;
    setOracleProposal: (proposal: OracleProposal | null) => void;

    // Oracle Chat Control
    isOracleChatOpen: boolean;
    setOracleChatOpen: (open: boolean) => void;
    oraclePendingMessage: string | null;
    setOraclePendingMessage: (msg: string | null) => void;

    // Active Contexts
    activeGoalId: number | null;
    setActiveGoalId: (id: number | null) => void;

    // Theme System (Dual)
    mainTheme: string;
    musicTheme: string;
    setMainTheme: (t: string) => void;
    setMusicTheme: (t: string) => void;


    // Notebook Panel (Global)
    isNotebookPanelOpen: boolean;
    setNotebookPanelOpen: (open: boolean) => void;

    // Transporter (Stash)
    stashItems: StashItem[];
    addToStash: (item: StashItem) => void;
    removeFromStash: (id: string) => void;
    clearStash: () => void;

    // Task Scheduling Modal
    taskScheduleModal: {
        isOpen: boolean;
        taskId: number;
        taskTitle: string;
        targetDate: Date | null;
        stashId: string;
    };
    setTaskScheduleModal: (modal: { isOpen: boolean; taskId: number; taskTitle: string; targetDate: Date | null; stashId: string }) => void;
    // Transporter Pop-out
    isTransporterPopped: boolean;
    setTransporterPopped: (popped: boolean) => void;

    // Pomodoro (Global State)
    pomodoro: {
        timeLeft: number;
        isRunning: boolean;
        mode: 'work' | 'break';
        sessions: number;
        isVisible: boolean;
        isFinished?: boolean;
    };
    togglePomodoro: () => void;
    resetPomodoro: () => void;
    setPomodoroMode: (mode: 'work' | 'break') => void;
    tickPomodoro: () => void;
    nextPomodoroSession: () => void;
    showPomodoro: () => void;
    hidePomodoro: () => void;

    // Global Search
    isGlobalSearchOpen: boolean;
    globalSearchQuery: string;
    setGlobalSearchOpen: (open: boolean) => void;
    setGlobalSearchQuery: (query: string) => void;
    openGlobalSearchWithQuery: (query: string) => void;
}

const WORK_DURATION = 25 * 60;
const BREAK_DURATION = 5 * 60;

export const useUIStore = create<UIState>((set) => ({
    sidebarOpen: true,
    toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
    currentProjectId: null,
    setCurrentProjectId: (id) => set({ currentProjectId: id }),

    isIngesting: false,
    ingestMessage: '',
    setIngesting: (isIngesting, message = '') => set({ isIngesting, ingestMessage: message }),

    // Global Modals
    isCreateProjectOpen: false,
    setCreateProjectOpen: (open: boolean) => set({ isCreateProjectOpen: open }),

    // Oracle
    oracleProposal: null,
    setOracleProposal: (proposal) => set({ oracleProposal: proposal }),

    isOracleChatOpen: false,
    setOracleChatOpen: (open) => set({ isOracleChatOpen: open }),
    oraclePendingMessage: null,
    setOraclePendingMessage: (msg) => set({ oraclePendingMessage: msg }),

    activeGoalId: null,
    setActiveGoalId: (id) => set({ activeGoalId: id }),

    // Theme System (Dual)
    mainTheme: 'default',
    musicTheme: 'music',
    setMainTheme: (t) => set({ mainTheme: t }),
    setMusicTheme: (t) => set({ musicTheme: t }),


    // Notebook Panel (Global)
    isNotebookPanelOpen: false,
    setNotebookPanelOpen: (open) => set({ isNotebookPanelOpen: open }),

    // Transporter (Stash)
    stashItems: [],
    addToStash: (item) => set((state) => ({ stashItems: [...state.stashItems, item] })),
    removeFromStash: (id) => set((state) => ({ stashItems: state.stashItems.filter(i => i.id !== id) })),
    clearStash: () => set({ stashItems: [] }),

    // Task Scheduling Modal
    taskScheduleModal: { isOpen: false, taskId: 0, taskTitle: '', targetDate: null, stashId: '' },
    setTaskScheduleModal: (modal) => set({ taskScheduleModal: modal }),
    closeTaskScheduleModal: () => set({ taskScheduleModal: { isOpen: false, taskId: 0, taskTitle: '', targetDate: null, stashId: '' } }),

    // Transporter Pop-out
    isTransporterPopped: false,
    setTransporterPopped: (popped) => set({ isTransporterPopped: popped }),

    // Pomodoro
    pomodoro: {
        timeLeft: WORK_DURATION,
        isRunning: false,
        mode: 'work',
        sessions: 0,
        isVisible: false,
        isFinished: false,
    },
    togglePomodoro: () => set((state) => ({
        pomodoro: {
            ...state.pomodoro,
            isRunning: !state.pomodoro.isRunning,
            isVisible: true // Auto-show on toggle
        }
    })),
    resetPomodoro: () => set((state) => ({
        pomodoro: {
            ...state.pomodoro,
            isRunning: false,
            timeLeft: state.pomodoro.mode === 'work' ? WORK_DURATION : BREAK_DURATION
        }
    })),
    setPomodoroMode: (mode) => set((state) => ({
        pomodoro: {
            ...state.pomodoro,
            mode,
            timeLeft: mode === 'work' ? WORK_DURATION : BREAK_DURATION,
            isRunning: false,
            isVisible: true // Auto-show on mode change
        }
    })),
    tickPomodoro: () => set((state) => {
        const { timeLeft, mode, sessions, isFinished } = state.pomodoro;
        if (isFinished) return state; // Do nothing if already finished

        if (timeLeft > 0) {
            return { pomodoro: { ...state.pomodoro, timeLeft: timeLeft - 1 } };
        } else {
            // Timer Finished
            return {
                pomodoro: {
                    ...state.pomodoro,
                    timeLeft: 0,
                    isRunning: false,
                    isFinished: true, // New flag to indicate completion waiting for user
                    isVisible: true
                }
            };
        }
    }),
    nextPomodoroSession: () => set((state) => {
        const { mode, sessions } = state.pomodoro;
        const newMode = mode === 'work' ? 'break' : 'work';
        return {
            pomodoro: {
                ...state.pomodoro,
                mode: newMode,
                timeLeft: newMode === 'work' ? WORK_DURATION : BREAK_DURATION,
                sessions: mode === 'work' ? sessions + 1 : sessions,
                isRunning: false,
                isFinished: false,
                isVisible: true
            }
        };
    }),
    showPomodoro: () => set((state) => ({ pomodoro: { ...state.pomodoro, isVisible: true } })),
    hidePomodoro: () => set((state) => ({ pomodoro: { ...state.pomodoro, isVisible: false } })),

    // Global Search
    isGlobalSearchOpen: false,
    globalSearchQuery: '',
    setGlobalSearchOpen: (open) => set({ isGlobalSearchOpen: open }),
    setGlobalSearchQuery: (query) => set({ globalSearchQuery: query }),
    openGlobalSearchWithQuery: (query) => set({ isGlobalSearchOpen: true, globalSearchQuery: query }),
}));
