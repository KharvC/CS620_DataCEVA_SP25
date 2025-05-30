import React, { useState, useEffect } from "react";
import Sidebar from "./components/sidebar";
import ChatWindow from "./components/chatwindow";
import { useNavigate } from "react-router-dom";
import "./App.css";

const App = () => {
  const [chats, setChats] = useState([]); // List of chat threads
  const [currentChatIndex, setCurrentChatIndex] = useState(null); // Active chat
  const navigate = useNavigate();
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setResponse(null);
    setLoading(true);

    const result = await sendUserQuery(query);

    if (result.error) {
      setResponse("Error storing query. Check console for details.");
    } else if (result.response) {
      setResponse(result.response); // General AI response
    } else {
      setResponse("Unexpected response format.");
    }

    setLoading(false);
  };

  // Start a new chat session
  const handleNewChat = () => {
    const newChat = { title: `Chat ${chats.length + 1}`, messages: [] };
    setChats([...chats, newChat]);
    setCurrentChatIndex(chats.length); // Select new chat
  };

  // Select an existing chat from history
  const handleSelectChat = (index) => {
    setCurrentChatIndex(index);
  };

  // Append new message to the current chat
  const handleSendMessage = (newMessage) => {
    if (currentChatIndex === null) {
      handleNewChat(); // Ensure there’s an active chat
    }
    const updatedChats = [...chats];
    updatedChats[currentChatIndex].messages.push(newMessage);
    setChats(updatedChats);
  };

  // Automatically start a new chat on initial load
  useEffect(() => {
    const verifyToken = async () => {
      const token = localStorage.getItem('token');
      if (!token) navigate("/login");
      try {
        const response = await fetch("http://localhost:8000/auth/verify-token",{
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        if (!response.ok) {
          throw new Error('Token verification failed');
        }
        if (chats.length === 0) {
          handleNewChat();
        }
      } catch (error) {
        localStorage.removeItem('token'); // Remove invalid token
        navigate('/login');
      }
    };
    verifyToken();
  }, []);

  return (
    <div className="app-container">
      <Sidebar chats={chats} onNewChat={handleNewChat} onSelectChat={handleSelectChat} />
      {currentChatIndex !== null ? (
        <ChatWindow messages={chats[currentChatIndex].messages} onSendMessage={handleSendMessage} />
      ) : null}
    </div>
  );
};

export default App;
