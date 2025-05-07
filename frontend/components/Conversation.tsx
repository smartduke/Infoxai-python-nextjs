'use client';

import React from 'react';
import Search from './Search';

export interface MessageType {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: {
    title: string;
    url: string;
    snippet?: string;
  }[];
  isStreaming?: boolean;
}

export interface ConversationProps {
  messages: MessageType[];
  onAsk: (question: string) => void;
  isLoading: boolean;
  onFollowUpClick: (question: string) => void;
}

export default function Conversation({ 
  messages, 
  onAsk, 
  isLoading, 
  onFollowUpClick 
}: ConversationProps) {
  
  // Function to format links and citations in messages
  const formatMessage = (message: string) => {
    if (!message) return '';
    
    // Format citation markers [1], [2], etc.
    const withCitations = message.replace(/\[(\d+)\]/g, '<span class="citation-marker" data-citation="$1">[$1]</span>');
    
    // Format paragraphs
    const paragraphs = withCitations.split(/\n\n+/).map(p => `<p>${p}</p>`).join('');
    
    return paragraphs;
  };

  // Function to render sources with expandable snippets
  const renderSources = (sources: any[]) => {
    if (!sources || sources.length === 0) return null;
    
    return (
      <div className="message-sources">
        <h4>Sources</h4>
        <div className="sources-list">
          {sources.map((source, idx) => (
            <div key={idx} className="source-item">
              <div className="source-header">
                <span className="source-number">{idx + 1}</span>
                <a href={source.url} target="_blank" rel="noopener noreferrer" className="source-link">
                  {source.title || source.url}
                </a>
              </div>
              {source.snippet && (
                <div className="source-snippet">
                  {source.snippet}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="conversation-container">
      {messages.length === 0 ? (
        <div className="empty-conversation">
          <div className="welcome-message">
            <h2>Welcome to InfoX AI</h2>
            <p>Ask any question to get comprehensive, reliable answers with sources</p>
          </div>
        </div>
      ) : (
        <div className="messages-container">
          {messages.map((message) => (
            <div 
              key={message.id} 
              className={`message ${message.role} ${message.isStreaming ? 'streaming' : ''}`}
            >
              <div className="message-avatar">
                {message.role === 'user' ? '🧑' : '🤖'}
              </div>
              <div className="message-content">
                {message.role === 'user' ? (
                  <div className="user-message">{message.content}</div>
                ) : (
                  <div 
                    className="assistant-message"
                    dangerouslySetInnerHTML={{__html: formatMessage(message.content)}}
                  />
                )}
                {message.role === 'assistant' && message.sources && renderSources(message.sources)}
              </div>
              {message.isStreaming && (
                <div className="message-loading">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
      
      <div className="conversation-input">
        <Search onSearch={onAsk} isLoading={isLoading} />
      </div>
    </div>
  );
}