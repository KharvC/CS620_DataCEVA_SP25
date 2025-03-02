import React, { useState } from 'react';
import './App.css';

const JustAskAI = () => {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setResponse(null);
    setTimeout(() => {
      setResponse(`AI Response for: "${query}"`);
    }, 1000);
  };

  return (
    <div className="fullscreen-container">
      <div className="content-box">
        <h1>Just Ask AI</h1>
        <p>Interact with AI to get real-time insights from your business data.</p>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question..."
            className="input-field"
          />
          <br />
          <button type="submit" className="submit-button">Ask</button>
        </form>
        {response && (
          <div className="response-box">
            <strong>Response:</strong>
            <p>{response}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default JustAskAI;
