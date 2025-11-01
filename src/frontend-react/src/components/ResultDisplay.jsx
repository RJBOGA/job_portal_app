import './Chat.css';

// Custom parser to handle the specific format from the backend
const parseContent = (content) => {
  if (typeof content !== 'string') return { text: '', gql: '', json: '' };

  const gqlMatch = content.match(/```graphql([\s\S]*?)```/);
  const jsonMatch = content.match(/```json([\s\S]*?)```/);

  const gql = gqlMatch ? gqlMatch[1].trim() : '';
  let json = null;
  if (jsonMatch) {
    try {
      json = JSON.parse(jsonMatch[1].trim());
    } catch (e) {
      console.error("Failed to parse JSON content:", e);
      // Fallback to show raw string if JSON is malformed
      json = jsonMatch[1].trim(); 
    }
  }
  
  // Extract text that is NOT inside the code blocks
  const text = content
    .replace(/```graphql[\s\S]*?```/, '')
    .replace(/```json[\s\S]*?```/, '')
    .replace(/\*\*Generated GraphQL:\*\*/, '')
    .replace(/\*\*Result:\*\*/, '')
    .trim();
  
  return { text, gql, json };
};

const ResultDisplay = ({ content }) => {
  const { text, gql, json } = parseContent(content);

  // If there are no code blocks, it's just plain text
  if (!gql && !json) {
    return <p className="message-text">{content}</p>;
  }

  return (
    <div className="result-container">
      {text && <p className="message-text">{text}</p>}
      {gql && (
        <>
          <h4>Generated GraphQL:</h4>
          <pre><code>{gql}</code></pre>
        </>
      )}
      {json && (
        <>
          <h4>Result:</h4>
          <pre><code>{JSON.stringify(json, null, 2)}</code></pre>
        </>
      )}
    </div>
  );
};

export default ResultDisplay;