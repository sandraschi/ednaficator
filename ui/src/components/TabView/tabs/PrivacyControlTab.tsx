import React from 'react';
import { Shield, Lock, Eye, Database } from 'lucide-react';

export const PrivacyControlTab: React.FC = () => {
  return (
    <div className="tab-content-wrapper">
      <div className="tab-header">
        <Shield size={24} />
        <h2>Datenschutz & Sicherheit</h2>
        <span className="status-badge status-badge--success">🔒 DSGVO-konform</span>
      </div>
      
      <div className="privacy-grid">
        <div className="privacy-card">
          <Lock size={32} />
          <h3>Lokale Verschlüsselung</h3>
          <p>Alle Daten bleiben auf Ihrem Gerät</p>
          <div className="status-indicator status-indicator--active">Aktiv</div>
        </div>
        
        <div className="privacy-card">
          <Eye size={32} />
          <h3>Keine Überwachung</h3>
          <p>Keine Cloud-Verbindungen</p>
          <div className="status-indicator status-indicator--active">Bestätigt</div>
        </div>
        
        <div className="privacy-card">
          <Database size={32} />
          <h3>Datenhoheit</h3>
          <p>Sie kontrollieren Ihre Daten</p>
          <div className="status-indicator status-indicator--active">Garantiert</div>
        </div>
      </div>
    </div>
  );
};