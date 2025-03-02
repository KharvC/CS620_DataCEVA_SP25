import { useState } from "react";
import "./ChatInterface.css"; // Import the CSS file

const ChatInterface = () => {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setResponse(`Processing: ${query}`);
  };

  return (
    <div className="chat-container">
      <div className="chat-box">
        <h1 className="chat-title">Just Ask AI</h1>
        <form onSubmit={handleSubmit} className="chat-form">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question..."
            className="chat-input"
          />
          <button type="submit" className="chat-button">
            Ask
          </button>
        </form>
        {response && <p className="chat-response">{response}</p>}
      </div>
    </div>
  );
};

export default ChatInterface;
