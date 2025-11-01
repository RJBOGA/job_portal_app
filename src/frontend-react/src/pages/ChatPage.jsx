import { useState, useContext, useEffect, useRef } from "react";
import { AuthContext } from "../context/AuthContext";
import { sendNlQuery } from "../services/api"; // Import our new API service
import Message from "../components/Message";
import MessageInput from "../components/MessageInput";
import '../components/Chat.css'; // Import the shared chat styles

const ChatPage = () => {
  const { user, logout } = useContext(AuthContext);
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hi! How can I help you today? Try asking to 'show all jobs' or 'update my profile'." }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const messageListRef = useRef(null); // Ref for the message list container
  
  // This effect runs whenever the `messages` array changes.
  // It automatically scrolls the message list to the bottom.
  useEffect(() => {
    if (messageListRef.current) {
        messageListRef.current.scrollTop = messageListRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async (prompt) => {
    if (!prompt) return;

    setIsLoading(true);
    // Immediately add the user's message to the chat for a responsive feel
    setMessages(prevMessages => [...prevMessages, { role: "user", content: prompt }]);

    try {
      const response = await sendNlQuery(prompt);
      
      const data = response.data;
      let assistantContent;

      if (response.status !== 200 || data.error) {
        // Handle application-level errors returned from the backend
        assistantContent = `**Error:** ${data.error?.message || 'An unknown error occurred.'}`;
      } else {
        // On success, format the content just like we did in Streamlit
        const gql = data.graphql || 'No GraphQL generated.';
        const result = data.result || {};
        assistantContent = `**Generated GraphQL:**\n\n\`\`\`graphql\n${gql}\n\`\`\`\n\n**Result:**\n\n\`\`\`json\n${JSON.stringify(result, null, 2)}\n\`\`\``;
      }
      // Add the assistant's response to the chat
      setMessages(prevMessages => [...prevMessages, { role: "assistant", content: assistantContent }]);

    } catch (error) {
      // Handle network errors (e.g., backend is down, CORS issues)
      const errorMsg = error.response?.data?.error?.message || error.message;
      setMessages(prevMessages => [...prevMessages, { role: "assistant", content: `**Error:** ${errorMsg}` }]);
    } finally {
      // Re-enable the input form regardless of success or failure
      setIsLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '1000px', margin: 'auto', padding: '1rem', color: 'white' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h1>AI Job Assistant</h1>
        {user && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <span>Welcome, <strong>{user.email}</strong>!</span>
            <button onClick={logout} style={{ background: '#444', border: 'none', padding: '8px 12px', borderRadius: '6px', cursor: 'pointer' }}>Logout</button>
          </div>
        )}
      </header>

      <main className="chat-container">
        <div className="message-list" ref={messageListRef}>
          {messages.map((msg, index) => (
            <Message key={index} message={msg} />
          ))}
        </div>
        <MessageInput onSend={handleSend} isLoading={isLoading} />
      </main>
    </div>
  );
};

export default ChatPage;