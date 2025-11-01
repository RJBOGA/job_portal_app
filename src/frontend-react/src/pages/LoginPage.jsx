import { useState, useContext } from "react";
import { AuthContext } from "../context/AuthContext";
import axios from "axios";
import './Auth.css'; // <-- Import the new CSS file

const GRAPHQL_ENDPOINT = "http://localhost:8000/graphql";

const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const { login } = useContext(AuthContext);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError(null);
    const query = `mutation Login($email: String!, $password: String!) { login(email: $email, password: $password) { token } }`;
    try {
      const response = await axios.post(GRAPHQL_ENDPOINT, { query, variables: { email, password } });
      if (response.data.errors) {
        throw new Error(response.data.errors[0].message);
      }
      const token = response.data.data.login.token;
      if (token) {
        login(token);
      } else {
        throw new Error("Login failed: No token received.");
      }
    } catch (err) {
      setError(err.message || "An error occurred during login.");
    }
  };

  return (
    <div className="auth-form-container">
      <h2>Login</h2>
      <form onSubmit={handleLogin}>
        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>
        {error && <p className="auth-error">{error}</p>}
        <button type="submit" className="auth-button">
          Login
        </button>
      </form>
    </div>
  );
};

export default LoginPage;