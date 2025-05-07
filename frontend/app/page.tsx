'use client';

import { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import Sidebar from '../components/Sidebar';
import Conversation, { MessageType } from '../components/Conversation';

// Backend API URL
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface AnswerResponse {
  main_answer: string;
  follow_up_questions: string[];
  read_more: {
    url: string;
    title: string;
  }[];
}

export default function Home() {
  const [searchMode, setSearchMode] = useState('search');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<MessageType[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);

  // Initialize dark mode based on user preference
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 
      (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    
    if (savedTheme === 'dark') {
      setIsDarkMode(true);
      document.body.classList.add('dark-mode');
    }
  }, []);

  // Toggle dark mode
  const toggleDarkMode = () => {
    const newMode = !isDarkMode;
    setIsDarkMode(newMode);
    
    if (newMode) {
      document.body.classList.add('dark-mode');
      localStorage.setItem('theme', 'dark');
    } else {
      document.body.classList.remove('dark-mode');
      localStorage.setItem('theme', 'light');
    }
  };

  // Start a new chat
  const handleStartNewChat = () => {
    setMessages([]);
    setSidebarOpen(false); // Close sidebar on mobile
  };

  // Handle mode change
  const handleModeChange = (mode: string) => {
    setSearchMode(mode);
    setSidebarOpen(false); // Close sidebar on mobile
  };

  // Convert read more links to sources format
  const convertToSources = (readMore: { url: string; title: string }[]) => {
    return readMore.map(item => ({
      title: item.title,
      url: item.url,
      snippet: ''
    }));
  };

  // Handle search
  const handleSearch = async (question: string) => {
    // Add user message
    const userMessage: MessageType = {
      id: uuidv4(),
      role: 'user',
      content: question,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    
    // Add loading assistant message
    const tempAssistantId = uuidv4();
    const tempAssistantMessage: MessageType = {
      id: tempAssistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true
    };
    setMessages(prev => [...prev, tempAssistantMessage]);
    
    setError(null);
    setIsLoading(true);
    
    try {
      const response = await fetch(`${API_URL}/api/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question })
      });
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status} ${response.statusText}`);
      }
      
      const data: AnswerResponse = await response.json();
      
      // Update assistant message with response
      setMessages(prev => 
        prev.map(msg => 
          msg.id === tempAssistantId 
            ? {
                ...msg,
                content: data.main_answer,
                isStreaming: false,
                sources: convertToSources(data.read_more)
              }
            : msg
        )
      );
    } catch (err) {
      console.error('Error fetching answer:', err);
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
      
      // Update assistant message with error
      setMessages(prev => 
        prev.map(msg => 
          msg.id === tempAssistantId 
            ? {
                ...msg,
                content: `Sorry, I encountered an error: ${err instanceof Error ? err.message : 'An unknown error occurred'}. Please try again.`,
                isStreaming: false
              }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Toggle mobile sidebar
  const toggleSidebar = () => {
    setSidebarOpen(prev => !prev);
  };

  return (
    <div className={`app-wrapper ${isDarkMode ? 'dark-mode' : ''}`}>
      {/* Mobile menu button */}
      <button className="mobile-menu-btn" onClick={toggleSidebar} aria-label="Menu">
        ☰
      </button>
      
      {/* Theme toggle button */}
      <button className="theme-toggle-btn" onClick={toggleDarkMode} aria-label="Toggle theme">
        {isDarkMode ? '☀️' : '🌙'}
      </button>
      
      {/* Sidebar */}
      <div className={`sidebar-wrapper ${sidebarOpen ? 'open' : ''}`}>
        <Sidebar 
          currentMode={searchMode} 
          onModeChange={handleModeChange}
          onStartNewChat={handleStartNewChat}
          isMobile={sidebarOpen}
          onCloseMobile={() => setSidebarOpen(false)}
        />
      </div>
      
      {/* Main content */}
      <main className="main-content">
        <div className="conversation-wrapper">
          <Conversation
            messages={messages}
            onAsk={handleSearch}
            isLoading={isLoading}
            onFollowUpClick={handleSearch}
          />
        </div>
      </main>
    </div>
  );
}