import { create } from 'zustand';

export type MsgRole = 'user' | 'assistant' | 'system' | 'error';
export type LLMProvider = 'ollama' | 'lmstudio';

export interface Message {
  id: string;
  role: MsgRole;
  content: string;
  timestamp: string;
  actions?: string[];
  toolCall?: { server: string; tool: string } | null;
  thinking?: boolean;
}

export interface ServerInfo {
  name: string;
  ready: boolean;
  tool_count: number;
  error: string | null;
}

export interface Settings {
  llm_provider: LLMProvider;
  ollama_base_url: string;
  ollama_model: string;
  lmstudio_base_url: string;
  lmstudio_model: string;
  available_models: string[];
  debug: boolean;
}

interface EdnaStore {
  messages: Message[];
  thinking: boolean;
  connected: boolean;
  servers: ServerInfo[];
  sidebarOpen: boolean;
  settings: Settings;

  addMessage: (msg: Omit<Message, 'id'>) => void;
  setThinking: (v: boolean) => void;
  setConnected: (v: boolean) => void;
  setServers: (s: ServerInfo[]) => void;
  setSettings: (s: Partial<Settings>) => void;
  toggleSidebar: () => void;
  clearMessages: () => void;
}

let _id = 0;
const uid = () => String(++_id);

export const useEdnaStore = create<EdnaStore>((set) => ({
  messages: [],
  thinking: false,
  connected: false,
  servers: [],
  sidebarOpen: true,
  settings: {
    llm_provider: 'lmstudio',
    ollama_base_url: 'http://localhost:11434',
    ollama_model: 'qwen2.5:27b',
    lmstudio_base_url: 'http://127.0.0.1:1234/v1',
    lmstudio_model: '',
    available_models: [],
    debug: false,
  },

  addMessage: (msg) =>
    set((s) => ({ messages: [...s.messages, { ...msg, id: uid() }] })),
  setThinking: (v) => set({ thinking: v }),
  setConnected: (v) => set({ connected: v }),
  setServers: (servers) => set({ servers }),
  setSettings: (updates) => set((s) => ({ settings: { ...s.settings, ...updates } })),
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  clearMessages: () => set({ messages: [] }),
}));
