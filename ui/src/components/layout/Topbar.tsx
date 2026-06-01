import React, { useState } from 'react';
import { useEdnaStore } from '../../store';
import { Menu, RotateCcw, Settings as SettingsIcon } from 'lucide-react';
import { SettingsModal } from '../settings/SettingsModal';

export const Topbar: React.FC<{ onToggleSidebar: () => void }> = ({ onToggleSidebar }) => {
  const connected = useEdnaStore(s => s.connected);
  const clear     = useEdnaStore(s => s.clearMessages);
  const settings  = useEdnaStore(s => s.settings);
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <header className="topbar glass">
      <div className="topbar__left">
        <button className="topbar__sidebar-btn" onClick={onToggleSidebar} title="MCP-Server ein-/ausblenden">
          <Menu size={20} />
        </button>
        <div className="topbar__logo">
          <span className="topbar__e">E</span>
          <span className="topbar__dna">DNA</span>
          <span className="topbar__suffix">FICATOR</span>
        </div>
        <div className="topbar__tagline">Wien Alsergrund · Lokal · Privat</div>
      </div>
      
      <div className="topbar__right">
        <div className="topbar__model-display">
          <span className="text-dim">{settings.llm_provider}:</span>
          <span className="text-gold">
            {settings.llm_provider === 'lmstudio'
              ? (settings.lmstudio_model || 'auto')
              : settings.ollama_model}
          </span>
        </div>
        
        <button className="topbar__icon-btn" onClick={() => setModalOpen(true)} title="Einstellungen">
          <SettingsIcon size={18} />
        </button>
        
        <button className="topbar__icon-btn" onClick={clear} title="Chat leeren">
          <RotateCcw size={18} />
        </button>
        
        <div className={`topbar__status ${connected ? 'topbar__status--on' : 'topbar__status--off'}`}>
          <span className="topbar__status-dot" />
          {connected ? 'verbunden' : 'getrennt'}
        </div>
      </div>

      <SettingsModal isOpen={modalOpen} onClose={() => setModalOpen(false)} />
    </header>
  );
};
