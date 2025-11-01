import { useState } from 'react';
import './Chat.css';

const MessageInput = ({ onSend, isLoading }) => {
  const [prompt, setPrompt] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (prompt.trim() && !isLoading) {
      onSend(prompt);
      setPrompt('');
    }
  };

  return (
    <form className="message-input-form" onSubmit={handleSubmit}>
      <input
        type="text"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Ask me anything..."
        disabled={isLoading}
      />
      <button type="submit" disabled={isLoading}>
        {isLoading ? '...' : 'Send'}
      </button>
    </form>
  );
};

export default MessageInput;