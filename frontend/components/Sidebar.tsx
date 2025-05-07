'use client';

import { useState } from 'react';

interface SearchMode {
  id: string;
  name: string;
  icon: string;
  description: string;
}

interface SidebarProps {
  currentMode: string;
  onModeChange: (mode: string) => void;
  onStartNewChat: () => void;
  isMobile?: boolean;
  onCloseMobile?: () => void;
}

export default function Sidebar({ 
  currentMode, 
  onModeChange, 
  onStartNewChat,
  isMobile = false,
  onCloseMobile
}: SidebarProps) {
  
  const searchModes: SearchMode[] = [
    {
      id: 'search',
      name: 'Web Search',
      icon: '🔍',
      description: 'Search the web for information'
    },
    {
      id: 'focus',
      name: 'Focus Mode',
      icon: '🎯',
      description: 'Detailed answers with fewer results'
    },
    {
      id: 'scholar',
      name: 'Academic',
      icon: '📚',
      description: 'Search academic papers and journals'
    },
    {
      id: 'youtube',
      name: 'YouTube',
      icon: '📺',
      description: 'Search and summarize YouTube videos'
    },
  ];

  return (
    <aside className={`sidebar ${isMobile ? 'mobile' : ''}`}>
      <div className="sidebar-header">
        <button className="new-chat-btn" onClick={onStartNewChat}>
          + New Chat
        </button>
        {isMobile && (
          <button className="close-sidebar-btn" onClick={onCloseMobile}>
            ×
          </button>
        )}
      </div>
      
      <nav className="sidebar-nav">
        <div className="search-modes">
          <h3>Search Modes</h3>
          <ul>
            {searchModes.map((mode) => (
              <li 
                key={mode.id} 
                className={currentMode === mode.id ? 'active' : ''}
                onClick={() => onModeChange(mode.id)}
              >
                <span className="mode-icon">{mode.icon}</span>
                <div className="mode-info">
                  <span className="mode-name">{mode.name}</span>
                  <span className="mode-description">{mode.description}</span>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </nav>
      
      <div className="sidebar-footer">
        <div className="user-options">
          <button className="settings-btn">
            ⚙️ Settings
          </button>
        </div>
      </div>
    </aside>
  );
}