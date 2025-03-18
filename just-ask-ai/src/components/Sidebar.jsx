import React from "react";

const Sidebar = ({ chats, onNewChat, onSelectChat }) => {
  return (
    <div className="sidebar">
      <h2>Chat History</h2>
      <button className="new-chat-button" onClick={onNewChat}>+ New Chat</button>
      <ul>
        {chats.map((chat, index) => (
          <li key={index} onClick={() => onSelectChat(index)}>
            {chat.title}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Sidebar;
