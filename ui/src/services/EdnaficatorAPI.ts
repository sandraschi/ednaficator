/**
 * Ednaficator API Service
 * 
 * Handles all communication between React UI and Python backend.
 * Supports both REST API and WebSocket real-time communication.
 */

export interface ChatMessage {
  message: string;
  user_id?: string;
}

export interface ChatResponse {
  message: string;
  actions_taken: string[];
  suggestions: string[];
  success: boolean;
  timestamp: string;
}

export interface SystemStatus {
  status: string;
  mcp_servers: MCPServer[];
  memory_status: string;
  austrian_services: string;
}

export interface MCPServer {
  id: string;
  name: string;
  type: string;
  status: 'connected' | 'disconnected' | 'error';
  lastSync: string;
  capabilities?: string[];
}

export interface ViennaService {
  id: string;
  name: string;
  category: string;
  status: string;
}

export interface SystemLog {
  timestamp: string;
  level: 'INFO' | 'WARN' | 'ERROR';
  source: string;
  message: string;
}

export interface UserPreferences {
  theme: 'light' | 'dark';
  language: 'de' | 'en';
  privacy_settings: {
    dataStorage: 'local' | 'cloud';
    analytics: boolean;
    thirdParty: boolean;
  };
}

class EdnaficatorAPI {
  private baseURL: string;
  private websocket: WebSocket | null = null;
  private wsListeners: Map<string, Function[]> = new Map();

  constructor(baseURL: string = 'http://localhost:8000') {
    this.baseURL = baseURL;
  }

  /**
   * REST API Methods
   */

  async getSystemStatus(): Promise<SystemStatus> {
    const response = await fetch(`${this.baseURL}/api/status`);
    if (!response.ok) {
      throw new Error(`Status request failed: ${response.statusText}`);
    }
    return response.json();
  }

  async sendChatMessage(message: string): Promise<ChatResponse> {
    const response = await fetch(`${this.baseURL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message, user_id: 'user' }),
    });

    if (!response.ok) {
      throw new Error(`Chat request failed: ${response.statusText}`);
    }

    return response.json();
  }

  async getMCPServers(): Promise<MCPServer[]> {
    const response = await fetch(`${this.baseURL}/api/mcp/servers`);
    if (!response.ok) {
      throw new Error(`MCP servers request failed: ${response.statusText}`);
    }
    return response.json();
  }

  async getViennaServices(): Promise<ViennaService[]> {
    const response = await fetch(`${this.baseURL}/api/vienna/services`);
    if (!response.ok) {
      throw new Error(`Vienna services request failed: ${response.statusText}`);
    }
    return response.json();
  }

  async updatePreferences(preferences: UserPreferences): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${this.baseURL}/api/preferences`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(preferences),
    });

    if (!response.ok) {
      throw new Error(`Preferences update failed: ${response.statusText}`);
    }

    return response.json();
  }

  async getSystemLogs(): Promise<SystemLog[]> {
    const response = await fetch(`${this.baseURL}/api/logs`);
    if (!response.ok) {
      throw new Error(`Logs request failed: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * WebSocket Methods for Real-time Communication
   */

  connectWebSocket(): void {
    if (this.websocket?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    const wsURL = this.baseURL.replace('http:', 'ws:').replace('https:', 'wss:');
    this.websocket = new WebSocket(`${wsURL}/ws`);

    this.websocket.onopen = () => {
      console.log('🔌 Connected to Ednaficator WebSocket');
      this.emit('connected', {});
    };

    this.websocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('📩 WebSocket message:', data);
        
        // Emit to listeners based on message type
        this.emit(data.type || 'message', data);
        this.emit('*', data); // Emit to wildcard listeners
      } catch (error) {
        console.error('❌ WebSocket message parse error:', error);
      }
    };

    this.websocket.onclose = () => {
      console.log('🔌 Disconnected from Ednaficator WebSocket');
      this.emit('disconnected', {});
      
      // Auto-reconnect after 3 seconds
      setTimeout(() => {
        this.connectWebSocket();
      }, 3000);
    };

    this.websocket.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      this.emit('error', { error });
    };
  }

  disconnectWebSocket(): void {
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
  }

  sendWebSocketMessage(type: string, data: any): void {
    if (this.websocket?.readyState === WebSocket.OPEN) {
      this.websocket.send(JSON.stringify({ type, ...data }));
    } else {
      console.warn('⚠️ WebSocket not connected, cannot send message');
    }
  }

  sendChatMessageWS(message: string): void {
    this.sendWebSocketMessage('chat', { message });
  }

  /**
   * Event System for WebSocket
   */

  on(event: string, callback: Function): void {
    if (!this.wsListeners.has(event)) {
      this.wsListeners.set(event, []);
    }
    this.wsListeners.get(event)!.push(callback);
  }

  off(event: string, callback: Function): void {
    const listeners = this.wsListeners.get(event);
    if (listeners) {
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  private emit(event: string, data: any): void {
    const listeners = this.wsListeners.get(event);
    if (listeners) {
      listeners.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`❌ Error in WebSocket listener for ${event}:`, error);
        }
      });
    }
  }

  /**
   * Health Check
   */

  async healthCheck(): Promise<{ status: string; edna_initialized: boolean }> {
    const response = await fetch(`${this.baseURL}/health`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Utility Methods
   */

  isWebSocketConnected(): boolean {
    return this.websocket?.readyState === WebSocket.OPEN;
  }

  getConnectionStatus(): 'connected' | 'connecting' | 'disconnected' | 'error' {
    if (!this.websocket) return 'disconnected';
    
    switch (this.websocket.readyState) {
      case WebSocket.CONNECTING:
        return 'connecting';
      case WebSocket.OPEN:
        return 'connected';
      case WebSocket.CLOSING:
      case WebSocket.CLOSED:
        return 'disconnected';
      default:
        return 'error';
    }
  }
}

// Create singleton instance
export const ednaficatorAPI = new EdnaficatorAPI();

// React Hook for easy integration
import { useState, useEffect } from 'react';

export interface UseEdnaAPIReturn {
  api: EdnaficatorAPI;
  status: SystemStatus | null;
  connectionStatus: 'connected' | 'connecting' | 'disconnected' | 'error';
  error: string | null;
  isConnected: boolean;
}

export function useEdnaficatorAPI(): UseEdnaAPIReturn {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'connecting' | 'disconnected' | 'error'>('disconnected');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Connect WebSocket
    ednaficatorAPI.connectWebSocket();

    // Set up WebSocket listeners
    const handleConnected = () => {
      setConnectionStatus('connected');
      setError(null);
    };

    const handleDisconnected = () => {
      setConnectionStatus('disconnected');
    };

    const handleError = (data: { error: any }) => {
      setConnectionStatus('error');
      setError(data.error?.message || 'WebSocket connection error');
    };

    ednaficatorAPI.on('connected', handleConnected);
    ednaficatorAPI.on('disconnected', handleDisconnected);
    ednaficatorAPI.on('error', handleError);

    // Fetch initial system status
    const fetchStatus = async () => {
      try {
        const systemStatus = await ednaficatorAPI.getSystemStatus();
        setStatus(systemStatus);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch system status');
      }
    };

    fetchStatus();

    // Clean up on unmount
    return () => {
      ednaficatorAPI.off('connected', handleConnected);
      ednaficatorAPI.off('disconnected', handleDisconnected);
      ednaficatorAPI.off('error', handleError);
    };
  }, []);

  return {
    api: ednaficatorAPI,
    status,
    connectionStatus,
    error,
    isConnected: connectionStatus === 'connected'
  };
}

// Helper hook for chat functionality
export interface UseChatReturn {
  messages: Array<{ type: 'user' | 'assistant' | 'system'; content: string; timestamp: string }>;
  sendMessage: (message: string) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

export function useEdnaficatorChat(): UseChatReturn {
  const [messages, setMessages] = useState<Array<{ type: 'user' | 'assistant' | 'system'; content: string; timestamp: string }>>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Connect to WebSocket for real-time responses
    ednaficatorAPI.connectWebSocket();

    const handleResponse = (data: any) => {
      if (data.type === 'response') {
        setMessages(prev => [...prev, {
          type: 'assistant',
          content: data.message,
          timestamp: data.timestamp
        }]);
        setIsLoading(false);
      } else if (data.type === 'system') {
        setMessages(prev => [...prev, {
          type: 'system',
          content: data.message,
          timestamp: data.timestamp
        }]);
      }
    };

    ednaficatorAPI.on('*', handleResponse);

    return () => {
      ednaficatorAPI.off('*', handleResponse);
    };
  }, []);

  const sendMessage = async (message: string) => {
    setIsLoading(true);
    setError(null);

    // Add user message to chat
    const userMessage = {
      type: 'user' as const,
      content: message,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      if (ednaficatorAPI.isWebSocketConnected()) {
        // Use WebSocket for real-time response
        ednaficatorAPI.sendChatMessageWS(message);
      } else {
        // Fallback to REST API
        const response = await ednaficatorAPI.sendChatMessage(message);
        setMessages(prev => [...prev, {
          type: 'assistant',
          content: response.message,
          timestamp: response.timestamp
        }]);
        setIsLoading(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
      setIsLoading(false);
    }
  };

  return {
    messages,
    sendMessage,
    isLoading,
    error
  };
}

export default ednaficatorAPI;
