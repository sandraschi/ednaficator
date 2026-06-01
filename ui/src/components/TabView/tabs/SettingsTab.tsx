import React from 'react';
import { Settings, User, Bell, Palette, Globe } from 'lucide-react';

export const SettingsTab: React.FC = () => {
  return (
    <div className="tab-content-wrapper">
      <div className="tab-header">
        <Settings size={24} />
        <h2>Einstellungen</h2>
      </div>
      
      <div className="settings-sections">
        <div className="settings-section">
          <User size={20} />
          <h3>Benutzerprofil</h3>
          <p>Name, Präferenzen, Sprache</p>
          <button className="btn btn--outline">Bearbeiten</button>
        </div>
        
        <div className="settings-section">
          <Palette size={20} />
          <h3>Design</h3>
          <p>Hell, Dunkel, Automatisch</p>
          <button className="btn btn--outline">Anpassen</button>
        </div>
        
        <div className="settings-section">
          <Bell size={20} />
          <h3>Benachrichtigungen</h3>
          <p>System-Alerts, Updates</p>
          <button className="btn btn--outline">Konfigurieren</button>
        </div>
        
        <div className="settings-section">
          <Globe size={20} />
          <h3>Lokalisierung</h3>
          <p>Österreich, Wien, Deutsch</p>
          <button className="btn btn--outline">Ändern</button>
        </div>
      </div>
    </div>
  );
};