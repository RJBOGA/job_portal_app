import { createContext, useState, useEffect } from "react";
import { jwtDecode } from "jwt-decode";

const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [user, setUser] = useState(null);

  useEffect(() => {
    if (token) {
      try {
        const decodedUser = jwtDecode(token);
        const isTokenExpired = decodedUser.exp * 1000 < Date.now();

        if (isTokenExpired) {
          logout();
        } else {
          localStorage.setItem("token", token);
          setUser({
            id: decodedUser.sub,
            email: decodedUser.email,
            role: decodedUser.role,
          });
        }
      } catch (error) {
        logout();
      }
    } else {
      localStorage.removeItem("token");
      setUser(null);
    }
  }, [token]);

  const login = (newToken) => {
    setToken(newToken);
  };

  const logout = () => {
    setToken(null);
  };

  const contextValue = {
    token,
    user,
    login,
    logout,
  };

  return (
    <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>
  );
};

export { AuthContext, AuthProvider };