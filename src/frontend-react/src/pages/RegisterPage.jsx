import { useState, useContext } from "react";
import { AuthContext } from "../context/AuthContext";
import axios from "axios";
import './Auth.css'; // <-- Import the new CSS file

const GRAPHQL_ENDPOINT = "http://localhost:8000/graphql";

const RegisterPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("user");
  const [error, setError] = useState(null);
  const { login } = useContext(AuthContext);

  const handleRegister = async (e) => {
    e.preventDefault();
    setError(null);
    const query = `mutation Register($email: String!, $password: String!, $role: String!) { register(email: $email, password: $password, role: $role) { token } }`;
    try {
      const response = await axios.post(GRAPHQL_ENDPOINT, { query, variables: { email, password, role } });
      if (response.data.errors) {
        throw new Error(response.data.errors[0].message);
      }
      const token = response.data.data.register.token;
      if (token) {
        login(token);
      } else {
        throw new Error("Registration failed: No token received.");
      }
    } catch (err) {
      setError(err.message || "An error occurred during registration.");
    }
  };

  return (
    <div className="auth-form-container">
      <h2>Register</h2>
      <form onSubmit={handleRegister}>
        <div className="form-group">
          <label htmlFor="register-email">Email</label>
          <input id="register-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>
        <div className="form-group">
          <label htmlFor="register-password">Password</label>
          <input id="register-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>
        <div className="form-group">
          <label htmlFor="role">I am a...</label>
          <select id="role" value={role} onChange={(e) => setRole(e.target.value)}>
            <option value="user">Job Seeker</option>
            <option value="recruiter">Recruiter</option>
          </select>
        </div>
        {error && <p className="auth-error">{error}</p>}
        <button type="submit" className="auth-button">
          Register
        </button>
      </form>
    </div>
  );
};

export default RegisterPage;