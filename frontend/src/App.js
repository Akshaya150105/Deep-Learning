import React, { useState, useRef, useEffect } from 'react';
import './styles.css';
import axios from 'axios';

function App() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hello! I'm your medical assistant. Describe your symptoms and I'll try to help identify possible conditions.",
      sender: 'bot',
    }
  ]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const [theme, setTheme] = useState('light');

  // Auto-scroll to bottom when new messages appear
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleInputChange = (e) => {
    setInput(e.target.value);
  };

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    // Add user message to chat
    const userMessage = {
      id: messages.length + 1,
      text: input,
      sender: 'user',
    };
    
    setMessages([...messages, userMessage]);
    setInput('');
    setLoading(true);

    // Add typing indicator
    setMessages(prevMessages => [...prevMessages, {
      id: 'typing',
      text: '',
      sender: 'bot',
      isTyping: true
    }]);

    try {
      // Make API request
      const res = await axios.get(`http://localhost:8000/query?symptoms=${input}`);
      
      // Remove typing indicator
      setMessages(prevMessages => prevMessages.filter(m => m.id !== 'typing'));
      
      // Add response message
      const botMessage = {
        id: messages.length + 2,
        text: res.data.response,
        sender: 'bot',
      };
      
      setMessages(prevMessages => [...prevMessages, botMessage]);
      
      // If there are conditions, add them as a separate message
      if (res.data.conditions && res.data.conditions.length > 0) {
        const conditionsText = formatConditions(res.data.conditions);
        const conditionsMessage = {
          id: messages.length + 3,
          text: conditionsText,
          sender: 'bot',
          isConditions: true,
        };
        
        setMessages(prevMessages => [...prevMessages, conditionsMessage]);
      }
    } catch (error) {
      // Remove typing indicator
      setMessages(prevMessages => prevMessages.filter(m => m.id !== 'typing'));
      
      // Add error message
      const errorMessage = {
        id: messages.length + 2,
        text: 'Sorry, I encountered an error while processing your symptoms. Please try again.',
        sender: 'bot',
        isError: true,
      };
      
      setMessages(prevMessages => [...prevMessages, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const formatConditions = (conditions) => {
    let formattedText = "**Possible conditions:**\n\n";
    conditions.forEach((cond, index) => {
      formattedText += `- **${cond.condition}**: ${cond.text}\n`;
    });
    return formattedText;
  };

  const handleClearChat = () => {
    setMessages([
      {
        id: 1,
        text: "Hello! I'm your medical assistant. Describe your symptoms and I'll try to help identify possible conditions.",
        sender: 'bot',
      }
    ]);
  };

  const renderMessageContent = (message) => {
    if (message.isTyping) {
      return (
        <div className="typing-indicator">
          <span></span>
          <span></span>
          <span></span>
        </div>
      );
    }
    
    if (message.isConditions) {
      return (
        <div className="conditions-container">
          {message.text.split('\n').map((line, index) => {
            if (line.startsWith('**Possible conditions:**')) {
              return <h4 key={index} className="conditions-title">Possible Conditions:</h4>;
            } else if (line.startsWith('- **')) {
              const conditionName = line.match(/\*\*(.*?)\*\*/)[1];
              const conditionText = line.replace(`- **${conditionName}**: `, '');
              return (
                <div key={index} className="condition-item">
                  <div className="condition-badge">{index + 1}</div>
                  <div className="condition-content">
                    <span className="condition-name">{conditionName}</span>
                    <span className="condition-text">{conditionText}</span>
                  </div>
                </div>
              );
            }
            return line ? <p key={index}>{line}</p> : null;
          })}
        </div>
      );
    }
    
    return message.text;
  };

  const renderTimestamp = () => {
    const now = new Date();
    const hours = now.getHours();
    const minutes = now.getMinutes().toString().padStart(2, '0');
    const ampm = hours >= 12 ? 'PM' : 'AM';
    const formattedHours = hours % 12 || 12;
    
    return `${formattedHours}:${minutes} ${ampm}`;
  };

  const Header = () => (
    <div className="chat-header">
      <div className="header-left">
        <div className="bot-avatar">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="7" r="5"/>
            <path d="M17 14h.01"/>
            <path d="M7 14h.01"/>
            <path d="M12 21v-4"/>
            <path d="M3 21h18"/>
            <path d="M19 14a7 7 0 0 0-14 0"/>
          </svg>
        </div>
        <div className="header-info">
          <h1>Medical Assistant</h1>
          <div className="status">
            <span className="status-dot"></span>
            <span>Online</span>
          </div>
        </div>
      </div>
      <div className="header-actions">
        <button className="theme-toggle" onClick={toggleTheme} title="Toggle theme">
          {theme === 'light' ? (
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="5"></circle>
              <line x1="12" y1="1" x2="12" y2="3"></line>
              <line x1="12" y1="21" x2="12" y2="23"></line>
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
              <line x1="1" y1="12" x2="3" y2="12"></line>
              <line x1="21" y1="12" x2="23" y2="12"></line>
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
            </svg>
          )}
        </button>
        <button className="clear-chat" onClick={handleClearChat} title="Clear chat">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 6h18"></path>
            <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
            <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
            <line x1="10" y1="11" x2="10" y2="17"></line>
            <line x1="14" y1="11" x2="14" y2="17"></line>
          </svg>
        </button>
      </div>
    </div>
  );
  
  const WelcomeBanner = () => (
    <div className="welcome-banner">
      <div className="welcome-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path>
          <rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect>
          <path d="M9 14h.01"></path>
          <path d="M12 16h.01"></path>
          <path d="M15 14h.01"></path>
          <path d="M12 12h.01"></path>
        </svg>
      </div>
      <div className="welcome-text">
        <h2>Medical Symptom Checker</h2>
        <p>Describe your symptoms in detail, and I'll help identify possible conditions.</p>
        <div className="disclaimer">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
          <span>This tool is for informational purposes only and is not a substitute for professional medical advice.</span>
        </div>
      </div>
    </div>
  );  

  return (
    <div className={`app-container ${theme}`}>
      <div className="chat-container">
        <Header />
        <div className="messages-container">
          <WelcomeBanner />
          
          {messages.map((message) => (
            <div 
              key={message.id} 
              className={`message-wrapper ${message.sender === 'user' ? 'user-wrapper' : 'bot-wrapper'}`}
            >
              {message.sender === 'bot' && !message.isTyping && (
                <div className="avatar bot-avatar">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="7" r="5"/>
                    <path d="M17 14h.01"/>
                    <path d="M7 14h.01"/>
                    <path d="M12 21v-4"/>
                    <path d="M3 21h18"/>
                    <path d="M19 14a7 7 0 0 0-14 0"/>
                  </svg>
                </div>
              )}
              <div 
                className={`message ${message.sender === 'user' ? 'user-message' : 'bot-message'} ${message.isError ? 'error-message' : ''}`}
              >
                {renderMessageContent(message)}
                {!message.isTyping && <span className="message-time">{renderTimestamp()}</span>}
              </div>
              {message.sender === 'user' && (
                <div className="avatar user-avatar">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                    <circle cx="12" cy="7" r="4"></circle>
                  </svg>
                </div>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
        
        <div className="suggestion-chips">
          <button className="suggestion-chip" onClick={() => setInput("Headache and fever")}>Headache and fever</button>
          <button className="suggestion-chip" onClick={() => setInput("Cough and sore throat")}>Cough and sore throat</button>
          <button className="suggestion-chip" onClick={() => setInput("Stomach pain and nausea")}>Stomach pain and nausea</button>
        </div>
        
        <form className="input-form" onSubmit={handleSubmit}>
          <input
            type="text"
            value={input}
            onChange={handleInputChange}
            placeholder="Describe your symptoms (e.g., headache, fever, cough)"
            disabled={loading}
            className="message-input"
          />
          <button 
            type="submit" 
            className="send-button"
            disabled={loading || !input.trim()}
            title="Send message"
          >
            {loading ? 
              <span className="loader"></span> : 
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            }
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;