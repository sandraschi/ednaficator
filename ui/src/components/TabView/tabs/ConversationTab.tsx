import React, { useState, useRef, useEffect } from 'react';
import { useEdnaficatorChat } from '../../../services/EdnaficatorAPI';
import './ConversationTab.css';

export const ConversationTab: React.FC = () => {
  const { messages, sendMessage, isLoading, error } = useEdnaficatorChat();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (input.trim() && !isLoading) {
      await sendMessage(input);
      setInput('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Austrian greeting suggestions
  const suggestions = [
    "Hallo Edna, wie geht es dir?",
    "Kannst du mir bei der Hausautomation helfen?",
    "Zeig mir meine Wien-Services",
    "Wie ist das Wetter heute in Wien?",
    "Hilf mir beim Organisieren meines Tages",
    "Was gibt es Neues in meiner Medienbibliothek?"
  ];

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
  };

  return (
    <div className="conversation-tab">
      {/* Header with connection status */}
      <div className="chat-header">
        <div className="edna-title">
          <h2>🤖 Edna - Ihre österreichische KI-Assistentin</h2>
          <p className="edna-subtitle">
            Privacy-first AI Concierge für Wien • Lokal • GDPR-konform
          </p>
        </div>
        
        {error && (
          <div className="error-banner">
            <span className="error-icon">❌</span>
            <span className="error-text">{error}</span>
            <button 
              className="error-retry"
              onClick={() => window.location.reload()}
            >
              Neu laden
            </button>
          </div>
        )}
      </div>

      {/* Chat messages area */}
      <div className="chat-messages">
        {messages.length === 0 && !isLoading && (
          <div className="welcome-message">
            <div className="welcome-content">
              <h3>🇦🇹 Grüß Gott! Willkommen bei Edna</h3>
              <p>
                Ich bin Ihre persönliche österreichische KI-Assistentin. 
                Ich kann Ihnen bei Hausautomation, Wien-Services, 
                Medienmanagement und vielem mehr helfen.
              </p>
              
              <div className="suggestions">
                <h4>💡 Probieren Sie:</h4>
                <div className="suggestion-buttons">
                  {suggestions.map((suggestion, index) => (
                    <button
                      key={index}
                      className="suggestion-button"
                      onClick={() => handleSuggestionClick(suggestion)}
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.type}`}>
            <div className="message-avatar">
              {msg.type === 'user' ? '👤' : msg.type === 'assistant' ? '🤖' : '🔔'}
            </div>
            <div className="message-bubble">
              <div className="message-content">
                {msg.content}
              </div>
              <div className="message-meta">
                <span className="message-time">
                  {new Date(msg.timestamp).toLocaleTimeString('de-AT', {
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </span>
                {msg.type === 'assistant' && (
                  <span className="message-source">• Edna</span>
                )}
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="message assistant loading">
            <div className="message-avatar">🤖</div>
            <div className="message-bubble">
              <div className="typing-indicator">
                <span>Edna denkt nach</span>
                <div className="dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="chat-input-container">
        <div className="chat-input">
          <div className="input-wrapper">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Sprechen Sie mit Edna... (Enter zum Senden, Shift+Enter für neue Zeile)"
              disabled={isLoading}
              rows={1}
              className="message-input"
            />
            <div className="input-actions">
              <button
                onClick={handleSend}
                disabled={isLoading || !input.trim()}
                className="send-button"
                title="Nachricht senden"
              >
                {isLoading ? '⏳' : '🚀'}
              </button>
            </div>
          </div>
          
          <div className="input-footer">
            <span className="privacy-note">
              🔒 Alle Daten bleiben lokal auf Ihrem System • GDPR-konform
            </span>
            {input.length > 0 && (
              <span className="char-counter">
                {input.length} Zeichen
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConversationTab;
