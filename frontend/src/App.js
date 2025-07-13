import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send, User, Bot, Train } from 'lucide-react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || (
  process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:8000'
);

function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (message = inputMessage) => {
    if (!message.trim() || isLoading) return;

    const userMessage = { type: 'user', content: message, timestamp: new Date() };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/chat`, {
        message: message.trim(),
        user_id: 'web-user'
      });

      const botMessage = {
        type: 'bot',
        content: response.data.response,
        stations: response.data.stations,
        subway_data: response.data.subway_data,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        type: 'bot',
        content: '죄송합니다. 서버와 연결할 수 없습니다. 잠시 후 다시 시도해주세요. 🙏',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage();
  };

  const handleExampleClick = (exampleMessage) => {
    sendMessage(exampleMessage);
  };

  const exampleMessages = [
    '강남역 도착정보 알려줘',
    '홍대입구역 언제 와?',
    '신촌역 실시간 정보',
    '건대입구역 지하철 정보'
  ];

  return (
    <div className="App">
      <header className="header">
        <h1>🚇 CommuteCare</h1>
        <p>출퇴근 도우미 챗봇 - 지하철 실시간 도착정보</p>
      </header>

      <div className="chat-container">
        <div className="chat-messages">
          {messages.length === 0 ? (
            <div className="welcome-message">
              <h3>안녕하세요! 지하철 실시간 도착정보를 알려드릴게요</h3>
              <p>궁금한 역의 이름을 말씀해 주세요</p>
              <div className="welcome-examples">
                {exampleMessages.map((example, index) => (
                  <button
                    key={index}
                    className="example-button"
                    onClick={() => handleExampleClick(example)}
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((message, index) => (
              <div key={index} className={`message ${message.type}`}>
                <div className="message-icon">
                  {message.type === 'user' ? (
                    <User size={18} />
                  ) : (
                    <Bot size={18} />
                  )}
                </div>
                <div className="message-bubble">
                  {message.content}
                </div>
              </div>
            ))
          )}
          
          {isLoading && (
            <div className="message bot">
              <div className="message-icon">
                <Bot size={18} />
              </div>
              <div className="message-bubble">
                <div className="loading">
                  <Train size={16} />
                  <span>정보를 가져오는 중...</span>
                  <div className="loading-dots">
                    <div className="loading-dot"></div>
                    <div className="loading-dot"></div>
                    <div className="loading-dot"></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSubmit} className="chat-input">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="예: 강남역 도착정보 알려줘"
            disabled={isLoading}
          />
          <button type="submit" disabled={isLoading || !inputMessage.trim()}>
            <Send size={16} />
            전송
          </button>
        </form>
      </div>
    </div>
  );
}

export default App; 