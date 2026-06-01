import React, { useState } from 'react';
import { 
  Settings, 
  Globe, 
  FileText, 
  HelpCircle, 
  User, 
  Moon, 
  Sun, 
  Monitor,
  Shield,
  Heart
} from 'lucide-react';
import { EdnaConfig, UserProfile } from '../../types';
import './TopBar.css';

interface TopBarProps {
  config: EdnaConfig;
  user: UserProfile;
  onThemeChange: (theme: EdnaConfig['theme']) => void;
  onLanguageChange: (language: EdnaConfig['language']) => void;
  onShowLogs: () => void;
  onShowHelp: () => void;
  onShowUserProfile: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  config,
  user,
  onThemeChange,
  onLanguageChange,
  onShowLogs,
  onShowHelp,
  onShowUserProfile
}) => {
  const [showThemeMenu, setShowThemeMenu] = useState(false);
  const [showLanguageMenu, setShowLanguageMenu] = useState(false);

  const themeIcons = {
    light: Sun,
    dark: Moon,
    auto: Monitor
  };

  const ThemeIcon = themeIcons[config.theme];

  return (
    <header className="top-bar">
      {/* Austrian Flag Pattern */}
      <div className="austrian-stripe"></div>
      
      {/* Logo and Title */}
      <div className="top-bar__brand">
        <Heart className="logo-icon" size={24} />
        <h1 className="brand-title">Edna</h1>
        <span className="brand-subtitle">Ihr österreichischer KI-Assistent</span>
      </div>

      {/* Privacy Badge */}
      <div className="privacy-badge">
        <Shield size={16} />
        <span>100% Lokal</span>
      </div>

      {/* Control Buttons */}
      <div className="top-bar__controls">
        {/* Theme Toggle */}
        <div className="control-group">
          <button 
            className="control-btn"
            onClick={() => setShowThemeMenu(!showThemeMenu)}
            title="Design ändern"
          >
            <ThemeIcon size={20} />
          </button>
          {showThemeMenu && (
            <div className="dropdown-menu">
              <button onClick={() => onThemeChange('light')}>
                <Sun size={16} /> Hell
              </button>
              <button onClick={() => onThemeChange('dark')}>
                <Moon size={16} /> Dunkel
              </button>
              <button onClick={() => onThemeChange('auto')}>
                <Monitor size={16} /> Automatisch
              </button>
            </div>
          )}
        </div>

        {/* Language Toggle */}
        <div className="control-group">
          <button 
            className="control-btn"
            onClick={() => setShowLanguageMenu(!showLanguageMenu)}
            title="Sprache ändern"
          >
            <Globe size={20} />
            <span className="lang-indicator">{config.language.toUpperCase()}</span>
          </button>
          {showLanguageMenu && (
            <div className="dropdown-menu">
              <button onClick={() => onLanguageChange('de')}>
                🇦🇹 Deutsch
              </button>
              <button onClick={() => onLanguageChange('en')}>
                🇬🇧 English
              </button>
            </div>
          )}
        </div>

        {/* Log Viewer */}
        <button 
          className="control-btn"
          onClick={onShowLogs}
          title="System-Protokolle"
        >
          <FileText size={20} />
        </button>

        {/* Help */}
        <button 
          className="control-btn"
          onClick={onShowHelp}
          title="Hilfe & Dokumentation"
        >
          <HelpCircle size={20} />
        </button>

        {/* User Profile */}
        <button 
          className="control-btn user-btn"
          onClick={onShowUserProfile}
          title="Benutzerprofil"
        >
          <User size={20} />
          <span className="user-name">{user.name}</span>
        </button>

        {/* Settings */}
        <button 
          className="control-btn settings-btn"
          onClick={() => console.log('Settings clicked')}
          title="Einstellungen"
        >
          <Settings size={20} />
        </button>
      </div>
    </header>
  );
};