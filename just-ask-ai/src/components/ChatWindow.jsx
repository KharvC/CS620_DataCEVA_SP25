import React, { useState } from "react";
import PacmanLoader from "react-spinners/PacmanLoader";
import { sendUserQuery } from "../api";

const ChatWindow = ({ messages, onSendMessage }) => {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const result = await sendUserQuery(query);
    const chatResponse = result.response || "Unexpected response format.";

    onSendMessage({ query, response: chatResponse });

    setQuery("");
    setLoading(false);
  };

  return (
    <div className="chat-window">
      <div className="messages">
        {messages.length === 0 ? <p className="empty-chat">No messages yet</p> : 
          messages.map((msg, index) => (
            <div key={index} className="chat-message">
              <strong>You:</strong> {msg.query}
              <br />
              <strong>AI:</strong> {msg.response}
            </div>
          ))
        }
      </div>

      <form onSubmit={handleSubmit} className="input-area">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question..."
          className="input-field"
        />
        <button type="submit" className="submit-button" disabled={loading}>
          {loading ? <PacmanLoader color="#fff" size={12} /> : "Ask"}
        </button>
      </form>
    </div>
  );
};

export default ChatWindow;
