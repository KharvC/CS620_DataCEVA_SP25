import React, { useState } from 'react';
import PacmanLoader from 'react-spinners/PacmanLoader';
import './App.css';
import { sendUserQuery } from './api';

const JustAskAI = () => {
  let [loading, setLoading] = useState(false);
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setResponse(null);
    setLoading(true);

    const result = await sendUserQuery(query);
    console.log("Frontend received:", result); // Debugging

    if (result.error) {
      setResponse("Error storing query. Check console for details.");
    } else if (result.result) {
      setResponse(`SQL Query Result: ${JSON.stringify(result.result, null, 2)}`);
    } else if (result.response) {
      setResponse(result.response); // General AI response
    } else {
      setResponse("Unexpected response format.");
    }

    setLoading(false);
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
          <button type="submit" className="submit-button" disabled={loading}>
            {loading ? (
              <div className="pacman-container">
                <PacmanLoader color="#fff" size={12} />
              </div>
            ) : (
              "Ask"
            )}
          </button>
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
