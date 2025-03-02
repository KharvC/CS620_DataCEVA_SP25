import React, { useState } from 'react';

const JustAskAI = () => {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setResponse(null);
    // Placeholder for actual API call
    setTimeout(() => {
      setResponse(`AI Response for: "${query}"`);
    }, 1000);
  };

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      height: '100vh', 
      backgroundColor: '#f5f5f5' 
    }}>
      <div style={{ 
        width: '50%', 
        maxWidth: '600px', 
        padding: '500px', 
        backgroundColor: 'white', 
        boxShadow: '0px 4px 10px rgba(0, 0, 0, 0.1)', 
        borderRadius: '8px', 
        textAlign: 'center',
        fontFamily: 'Arial, sans-serif' 
      }}>
        <h1>Just Ask AI</h1>
        <p>Interact with AI to get real-time insights from your business data.</p>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question..."
            style={{ width: '80%', padding: '10px', marginBottom: '10px' }}
          />
          <br />
          <button type="submit" style={{ padding: '10px 15px' }}>Ask</button>
        </form>
        {response && (
          <div style={{ marginTop: '20px', padding: '10px', border: '1px solid #ccc', borderRadius: '4px' }}>
            <strong>Response:</strong>
            <p>{response}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default JustAskAI;
