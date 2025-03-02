import { useState } from "react";

const ChatInterface = () => {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setResponse(`Processing: ${query}`);
  };

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-100 px-150">
      <h1 className="text-2xl font-bold mb-4 whitespace-nowrap">Just Ask AI</h1>
      <div className="w-full max-w-2xl bg-white shadow-md p-6 rounded-lg">
        <form onSubmit={handleSubmit} className="flex flex-col">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question..."
            className="p-2 border rounded-md mb-2"
          />
          <button
            type="submit"
            className="bg-blue-600 text-black p-2 rounded-md hover:bg-blue-700"
          >
            Ask
          </button>
        </form>
        {response && <p className="mt-4 text-gray-700">{response}</p>}
      </div>
    </div>
  );
};

export default ChatInterface;
