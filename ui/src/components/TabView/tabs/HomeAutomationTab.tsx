import React from 'react';
import { Home, Lightbulb, Thermometer, Shield, Wifi } from 'lucide-react';

export const HomeAutomationTab: React.FC = () => {
  return (
    <div className="tab-content-wrapper">
      <div className="tab-header">
        <Home size={24} />
        <h2>Smart Home Steuerung</h2>
        <span className="status-badge status-badge--success">3 Geräte aktiv</span>
      </div>
      
      <div className="content-grid">
        <div className="device-card">
          <Lightbulb size={32} />
          <h3>Beleuchtung</h3>
          <p>Wohnzimmer, Schlafzimmer</p>
          <button className="btn btn--primary">Steuerung</button>
        </div>
        
        <div className="device-card">
          <Thermometer size={32} />
          <h3>Heizung</h3>
          <p>21°C • Automatik</p>
          <button className="btn btn--primary">Einstellungen</button>
        </div>
        
        <div className="device-card">
          <Shield size={32} />
          <h3>Sicherheit</h3>
          <p>Alle Sensoren OK</p>
          <button className="btn btn--primary">Status</button>
        </div>
        
        <div className="device-card">
          <Wifi size={32} />
          <h3>Netzwerk</h3>
          <p>Verbunden • Stark</p>
          <button className="btn btn--primary">Details</button>
        </div>
      </div>
    </div>
  );
};