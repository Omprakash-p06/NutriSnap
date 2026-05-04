import React from "react";
import "./App.css";
import { ThemeProvider } from "./context/ThemeContext";
import { AuthProvider } from "./context/AuthContext";
import Navbar from "./components/layout/Navbar";
import Footer from "./components/Footer";
import Home from "./pages/Home";

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  render() {
    if (this.state.hasError) {
      return (
        <div
          className="error-screen"
          style={{ padding: "40px", textAlign: "center" }}
        >
          <h2>Something went wrong.</h2>
          <button onClick={() => window.location.reload()} className="clay-btn">
            Reload App
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ErrorBoundary>
          <div id="app-container">
            <Navbar />
            <main>
              <Home />
            </main>
            <Footer />
          </div>
        </ErrorBoundary>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
