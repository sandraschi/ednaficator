import React from 'react';
import { Brain, Cpu, Zap, Target } from 'lucide-react';

export const AIAssistantTab: React.FC = () => {
  return (
    <div className="tab-content-wrapper">
      <div className="tab-header">
        <Brain size={24} />
        <h2>KI-Assistent Einstellungen</h2>
        <span className="status-badge status-badge--success">Lokal aktiv</span>
      </div>
      
      <div className="ai-config">
        <div className="config-section">
          <Cpu size={24} />
          <h3>Lokales LLM</h3>
          <p>Modell: Austrian-German-7B</p>
          <p>Status: Geladen und bereit</p>
        </div>
        
        <div className="config-section">
          <Zap size={24} />
          <h3>Performance</h3>
          <p>Antwortzeit: ~2s</p>
          <p>Genauigkeit: 94%</p>
        </div>
        
        <div className="config-section">
          <Target size={24} />
          <h3>Spezialisierung</h3>
          <p>Österreichische Services</p>
          <p>Smart Home Automation</p>
        </div>
      </div>
    </div>
  );
};