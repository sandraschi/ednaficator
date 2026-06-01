import React from 'react';
import { Cog, Activity, AlertCircle, CheckCircle } from 'lucide-react';

export const MCPOrchestrationTab: React.FC = () => {
  return (
    <div className="tab-content-wrapper">
      <div className="tab-header">
        <Cog size={24} />
        <h2>MCP Server Orchestration</h2>
        <span className="status-badge status-badge--success">5 Server online</span>
      </div>
      
      <div className="server-list">
        <div className="server-item">
          <CheckCircle className="status-icon status-icon--success" size={20} />
          <div className="server-info">
            <h3>local-llm-mcp</h3>
            <p>Lokale KI-Verarbeitung</p>
          </div>
          <Activity size={16} />
        </div>
        
        <div className="server-item">
          <CheckCircle className="status-icon status-icon--success" size={20} />
          <div className="server-info">
            <h3>wien-services-mcp</h3>
            <p>Wiener Linien & Services</p>
          </div>
          <Activity size={16} />
        </div>
        
        <div className="server-item">
          <AlertCircle className="status-icon status-icon--warning" size={20} />
          <div className="server-info">
            <h3>homecontrol-mcp</h3>
            <p>Smart Home Integration</p>
          </div>
          <Activity size={16} />
        </div>
      </div>
    </div>
  );
};