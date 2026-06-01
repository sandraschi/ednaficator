import React, { useEffect } from 'react';
import { useEdnaStore } from './store';
import { Topbar } from './components/layout/Topbar';
import { Sidebar } from './components/layout/Sidebar';
import { ChatContainer } from './components/chat/ChatContainer';
import './index.css';

export default function App() {
  const sidebarOpen   = useEdnaStore(s => s.sidebarOpen);
  const toggleSidebar = useEdnaStore(s => s.toggleSidebar);
  const setSettings   = useEdnaStore(s => s.setSettings);

  useEffect(() => {
    fetch('/api/settings')
      .then(res => res.json())
      .then(data => setSettings({
        llm_provider: data.llm_provider,
        ollama_model: data.ollama_model,
        lmstudio_model: data.lmstudio_model,
        ollama_base_url: data.ollama_base_url,
        lmstudio_base_url: data.lmstudio_base_url,
      }))
      .catch(() => {});
  }, [setSettings]);

  return (
    <div className="layout">
      <Topbar onToggleSidebar={toggleSidebar} />
      <div className="main">
        <Sidebar open={sidebarOpen} />
        <ChatContainer />
      </div>
    </div>
  );
}
