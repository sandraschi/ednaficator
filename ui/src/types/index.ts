export interface EdnaConfig {
  theme: 'light' | 'dark' | 'auto';
  language: 'de' | 'en';
  privacy: {
    dataStorage: 'local' | 'encrypted';
    analytics: boolean;
    thirdParty: boolean;
  };
}

export interface TabCategory {
  id: string;
  label: string;
  icon: string;
  component: React.ComponentType;
}

export interface UserProfile {
  name: string;
  preferences: EdnaConfig;
  connectedServices: ConnectedService[];
}

export interface ConnectedService {
  id: string;
  name: string;
  type: 'mcp' | 'local' | 'external';
  status: 'connected' | 'disconnected' | 'error';
  lastSync?: Date;
}

export interface LogEntry {
  timestamp: Date;
  level: 'info' | 'warning' | 'error' | 'debug';
  component: string;
  message: string;
  details?: any;
}

export interface MCPServerStatus {
  name: string;
  running: boolean;
  lastHeartbeat?: Date;
  capabilities: string[];
  errorCount: number;
}