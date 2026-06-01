import React from 'react';
import { MapPin, Train, Bus, Phone } from 'lucide-react';

export const ViennaServicesTab: React.FC = () => {
  return (
    <div className="tab-content-wrapper">
      <div className="tab-header">
        <MapPin size={24} />
        <h2>Wien Services</h2>
        <span className="status-badge status-badge--info">🇦🇹 Lokal</span>
      </div>
      
      <div className="content-grid">
        <div className="service-card">
          <Train size={32} />
          <h3>Wiener Linien</h3>
          <p>Echtzeitinformationen</p>
          <button className="btn btn--primary">Fahrplan</button>
        </div>
        
        <div className="service-card">
          <Bus size={32} />
          <h3>Öffentlicher Verkehr</h3>
          <p>U-Bahn, Bus, Straßenbahn</p>
          <button className="btn btn--primary">Verbindungen</button>
        </div>
        
        <div className="service-card">
          <Phone size={32} />
          <h3>Notdienste</h3>
          <p>Wichtige Nummern</p>
          <button className="btn btn--secondary">Kontakte</button>
        </div>
      </div>
    </div>
  );
};