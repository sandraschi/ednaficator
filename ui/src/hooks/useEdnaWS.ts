import { useEffect, useRef, useCallback } from 'react';
import { useEdnaStore } from '../store';

// Both URLs relative — go through Vite proxy → backend on 10942
const WS_URL = `ws://${window.location.host}/ws`;
const SERVERS_URL = '/api/servers';

export function useEdnaWS() {
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const { addMessage, setThinking, setConnected, setServers } = useEdnaStore();

  const fetchServers = useCallback(async () => {
    try {
      const res = await fetch(SERVERS_URL);
      if (res.ok) setServers(await res.json());
    } catch { /* backend not up yet */ }
  }, [setServers]);

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;

    const socket = new WebSocket(WS_URL);
    ws.current = socket;

    socket.onopen = () => {
      setConnected(true);
      fetchServers();
    };

    socket.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        if (data.type === 'thinking') {
          setThinking(true);
          return;
        }
        if (data.type === 'system') {
          addMessage({ role: 'system', content: data.message, timestamp: data.timestamp });
          return;
        }
        if (data.type === 'response') {
          setThinking(false);
          addMessage({
            role: 'assistant',
            content: data.message,
            timestamp: data.timestamp,
            actions: data.actions_taken,
            toolCall: data.tool_call,
          });
          fetchServers();
          return;
        }
        if (data.type === 'error') {
          setThinking(false);
          addMessage({ role: 'error', content: data.message, timestamp: new Date().toISOString() });
        }
      } catch { /* ignore parse errors */ }
    };

    socket.onclose = () => {
      setConnected(false);
      reconnectTimer.current = setTimeout(connect, 3000);
    };

    socket.onerror = () => {
      setConnected(false);
    };
  }, [addMessage, setThinking, setConnected, fetchServers]);

  useEffect(() => {
    // Fetch servers immediately — don't wait for WS handshake
    fetchServers();
    connect();

    // Also poll servers every 10s so the sidebar stays fresh
    const poll = setInterval(fetchServers, 10_000);

    return () => {
      clearInterval(poll);
      reconnectTimer.current && clearTimeout(reconnectTimer.current);
      ws.current?.close();
    };
  }, [connect, fetchServers]);

  const send = useCallback((message: string) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'chat', message }));
    }
  }, []);

  return { send };
}
