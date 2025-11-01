import { useState } from 'react';
import LoginPage from './LoginPage';
import RegisterPage from './RegisterPage';
import './Auth.css'; // <-- Import the new CSS file

const AuthPage = () => {
  const [activeTab, setActiveTab] = useState('login');

  return (
    <div className="auth-container">
      <div className="auth-tabs">
        <button 
          className={`auth-tab ${activeTab === 'login' ? 'active' : ''}`}
          onClick={() => setActiveTab('login')}
        >
          Login
        </button>
        <button 
          className={`auth-tab ${activeTab === 'register' ? 'active' : ''}`}
          onClick={() => setActiveTab('register')}
        >
          Register
        </button>
      </div>
      <div>
        {activeTab === 'login' ? <LoginPage /> : <RegisterPage />}
      </div>
    </div>
  );
};

export default AuthPage;