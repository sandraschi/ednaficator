import React, { useState } from 'react';
import { 
  Home, 
  Cog, 
  MapPin, 
  Shield, 
  Brain, 
  Activity,
  MessageSquare,
  Settings
} from 'lucide-react';
import { TabCategory } from '../../types';
import './TabView.css';

// Import tab components (will create these next)
import { HomeAutomationTab } from './tabs/HomeAutomationTab';
import { MCPOrchestrationTab } from './tabs/MCPOrchestrationTab';
import { ViennaServicesTab } from './tabs/ViennaServicesTab';
import { PrivacyControlTab } from './tabs/PrivacyControlTab';
import { AIAssistantTab } from './tabs/AIAssistantTab';
import { SystemMonitorTab } from './tabs/SystemMonitorTab';
import { ConversationTab } from './tabs/ConversationTab';
import { SettingsTab } from './tabs/SettingsTab';

interface TabViewProps {
  onTabChange?: (tabId: string) => void;
}

export const TabView: React.FC<TabViewProps> = ({ onTabChange }) => {
  const [activeTab, setActiveTab] = useState('conversation');

  const tabs: TabCategory[] = [
    {
      id: 'conversation',
      label: 'Edna Chat',
      icon: 'MessageSquare',
      component: ConversationTab
    },
    {
      id: 'home',
      label: 'Smart Home',
      icon: 'Home',
      component: HomeAutomationTab
    },
    {
      id: 'mcp',
      label: 'MCP-Server',
      icon: 'Cog',
      component: MCPOrchestrationTab
    },
    {
      id: 'vienna',
      label: 'Wien Services',
      icon: 'MapPin',
      component: ViennaServicesTab
    },
    {
      id: 'ai',
      label: 'KI-Assistent',
      icon: 'Brain',
      component: AIAssistantTab
    },
    {
      id: 'privacy',
      label: 'Datenschutz',
      icon: 'Shield',
      component: PrivacyControlTab
    },
    {
      id: 'monitor',
      label: 'System',
      icon: 'Activity',
      component: SystemMonitorTab
    },
    {
      id: 'settings',
      label: 'Einstellungen',
      icon: 'Settings',
      component: SettingsTab
    }
  ];

  const iconMap = {
    MessageSquare,
    Home,
    Cog,
    MapPin,
    Brain,
    Shield,
    Activity,
    Settings
  };

  const handleTabClick = (tabId: string) => {
    setActiveTab(tabId);
    onTabChange?.(tabId);
  };

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component || ConversationTab;

  return (
    <div className="tab-view">
      {/* Tab Navigation */}
      <nav className="tab-nav">
        <div className="tab-nav__container">
          {tabs.map((tab) => {
            const IconComponent = iconMap[tab.icon as keyof typeof iconMap];
            return (
              <button
                key={tab.id}
                className={`tab-nav__button ${
                  activeTab === tab.id ? 'tab-nav__button--active' : ''
                }`}
                onClick={() => handleTabClick(tab.id)}
                title={tab.label}
              >
                <IconComponent size={20} />
                <span className="tab-nav__label">{tab.label}</span>
                {tab.id === 'conversation' && (
                  <div className="tab-nav__badge">AI</div>
                )}
                {tab.id === 'privacy' && (
                  <div className="tab-nav__badge tab-nav__badge--green">🇦🇹</div>
                )}
              </button>
            );
          })}
        </div>
      </nav>

      {/* Tab Content */}
      <main className="tab-content">
        <div className="tab-content__container">
          <ActiveComponent />
        </div>
      </main>
    </div>
  );
};