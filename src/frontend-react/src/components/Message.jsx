import './Chat.css';
import ResultDisplay from './ResultDisplay';

const Message = ({ message }) => {
  const isUser = message.role === 'user';
  
  return (
    <div className={`message ${isUser ? 'user' : 'assistant'}`}>
      <div className="message-avatar">
        {isUser ? 'You' : 'AI'}
      </div>
      <div className="message-content">
        {isUser ? (
          <p className="message-text">{message.content}</p>
        ) : (
          <ResultDisplay content={message.content} />
        )}
      </div>
    </div>
  );
};

export default Message;