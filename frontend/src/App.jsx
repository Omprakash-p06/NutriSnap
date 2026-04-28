import React from 'react';
import './App.css';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/layout/Navbar';
import Footer from './components/Footer';
import Home from './pages/Home';
import AuthModal from './components/AuthModal';
import { UpdateToast } from './components/common/UpdateToast';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError() { return { hasError: true }; }
  render() {
    if (this.state.hasError) {
      return (
        <div className="error-screen" style={{ padding: '40px', textAlign: 'center' }}>
          <h2>Something went wrong.</h2>
          <button onClick={() => window.location.reload()} className="clay-btn">Reload App</button>
        </div>
      );
    }
    return this.props.children;
  }
}

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

function App() {
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <ThemeProvider>
        <AuthProvider>
          <ErrorBoundary>
            <div id="app-container">
              <Navbar />
              <main>
                <Home />
              </main>
              <Footer />
              <AuthModal />
              <UpdateToast />
            </div>
          </ErrorBoundary>
        </AuthProvider>
      </ThemeProvider>
    </GoogleOAuthProvider>
  );
}

export default App;