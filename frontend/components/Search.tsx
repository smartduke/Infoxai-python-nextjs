'use client';

import { useState } from 'react';

interface SearchProps {
  onSearch: (question: string) => void;
  isLoading: boolean;
}

export default function Search({ onSearch, isLoading }: SearchProps) {
  const [question, setQuestion] = useState('');

  const handleSearch = () => {
    if (question.trim() && !isLoading) {
      onSearch(question);
      setQuestion('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  return (
    <div className="search-input-container">
      <textarea
        className="search-input"
        placeholder="Ask any question..."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        onKeyDown={handleKeyPress}
        disabled={isLoading}
        rows={1}
        autoFocus
      />
      <button 
        className="search-button"
        onClick={handleSearch}
        disabled={isLoading || !question.trim()}
        aria-label="Search"
      >
        {isLoading ? (
          <div className="button-loader"></div>
        ) : (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" fill="currentColor" />
          </svg>
        )}
      </button>
    </div>
  );
}