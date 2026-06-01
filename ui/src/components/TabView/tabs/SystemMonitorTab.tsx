import React from 'react';
import { Activity, Monitor, HardDrive, Wifi } from 'lucide-react';

export const SystemMonitorTab: React.FC = () => {
  return (
    <div className="tab-content-wrapper">
      <div className="tab-header">
        <Activity size={24} />
        <h2>System Monitor</h2>
        <span className="status-badge status-badge--success">Alle Systeme OK</span>
      </div>
      
      <div className="monitor-grid">
        <div className="metric-card">
          <Monitor size={32} />
          <h3>CPU</h3>
          <div className="metric-value">23%</div>
          <div className="metric-bar">
            <div className="metric-fill" style={{width: '23%'}}></div>
          </div>
        </div>
        
        <div className="metric-card">
          <HardDrive size={32} />
          <h3>Speicher</h3>
          <div className="metric-value">67%</div>
          <div className="metric-bar">
            <div className="metric-fill" style={{width: '67%'}}></div>
          </div>
        </div>
        
        <div className="metric-card">
          <Wifi size={32} />
          <h3>Netzwerk</h3>
          <div className="metric-value">Optimal</div>
          <div className="metric-status">45 Mbps</div>
        </div>
      </div>
    </div>
  );
};