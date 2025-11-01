import { useContext } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { AuthContext } from "./context/AuthContext";
import AuthPage from "./pages/AuthPage"; // <-- Import the new AuthPage
import ChatPage from "./pages/ChatPage";

const ProtectedRoute = ({ children }) => {
  const { user } = useContext(AuthContext);
  if (!user) {
    return <Navigate to="/auth" replace />; // Redirect to the new auth page
  }
  return children;
};

function App() {
  const { user } = useContext(AuthContext);

  return (
    <Routes>
      {/* Route 1: The Authentication Page (Login & Register) */}
      <Route
        path="/auth"
        element={user ? <Navigate to="/chat" replace /> : <AuthPage />}
      />

      {/* Route 2: The Main Chat Page (Protected) */}
      <Route
        path="/chat"
        element={
          <ProtectedRoute>
            <ChatPage />
          </ProtectedRoute>
        }
      />

      {/* Route 3: Default Route */}
      <Route path="/" element={<Navigate to="/chat" replace />} />
    </Routes>
  );
}

export default App;