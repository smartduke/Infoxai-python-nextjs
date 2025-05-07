'use client';

import React from 'react';
import { useEffect } from 'react';

interface ReadMoreItem {
  url: string;
  title: string;
}

interface AnswerProps {
  mainAnswer: string;
  followUpQuestions: string[];
  readMore: ReadMoreItem[];
  onFollowUpClick: (question: string) => void;
  visible: boolean;
}

export default function Answer({
  mainAnswer,
  followUpQuestions,
  readMore,
  onFollowUpClick,
  visible
}: AnswerProps) {
  
  // Format text with basic Markdown-like features
  const formatText = (text: string): string => {
    if (!text) return '';
    
    // Bold text **example**
    text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    
    // Italics *example*
    text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    
    // Source citation
    text = text.replace(/\[Source\s+(\d+)\]/g, '<span class="source">[Source $1]</span>');
    
    // Process paragraphs
    let paragraphs = text.split(/\n\n+/);
    let processedHtml = '';
    
    for (let p of paragraphs) {
      p = p.trim();
      if (!p) continue;
      
      // Check if this is a numbered list
      if (/^\d+\.\s/.test(p)) {
        const listItems = p.split(/\n/).filter(line => /^\d+\.\s/.test(line));
        if (listItems.length > 0) {
          let listHtml = '<ol>';
          for (const item of listItems) {
            const content = item.replace(/^\d+\.\s/, '').trim();
            listHtml += `<li>${content}</li>`;
          }
          listHtml += '</ol>';
          processedHtml += listHtml;
        } else {
          processedHtml += `<p>${p}</p>`;
        }
      } else {
        processedHtml += `<p>${p}</p>`;
      }
    }
    
    return processedHtml || text;
  };

  if (!visible) return null;

  return (
    <div id="answer-container">
      <div className="answer-header">
        <h2>Answer</h2>
      </div>
      
      <div className="answer-content">
        <div 
          id="answer-text"
          dangerouslySetInnerHTML={{ __html: formatText(mainAnswer) }}
        />
        
        {followUpQuestions.length > 0 && (
          <div className="section" id="follow-up-section">
            <h3>Follow-up questions</h3>
            <div id="follow-up-questions" className="follow-up">
              {followUpQuestions.map((question, idx) => (
                <button 
                  key={idx} 
                  onClick={() => onFollowUpClick(question)}
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}
        
        {readMore.length > 0 && (
          <div className="section" id="read-more-section">
            <h3>Read more</h3>
            <div id="read-more-links" className="read-more">
              {readMore.map((item, idx) => (
                <a 
                  key={idx} 
                  href={item.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                >
                  {item.title || item.url}
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}