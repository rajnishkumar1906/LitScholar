// src/App.jsx - UPDATED
import { Routes, Route } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import Dashboard from './pages/Dashboard.jsx';
import Auth from './pages/Auth.jsx';
import Profile from './pages/Profile.jsx';
import BookDetail from './pages/BookDetail.jsx';
import NotFound from './pages/NotFound.jsx';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <AppProvider>
      {/* Completely clean - no padding, no max-width constraints */}
      <Routes>
        <Route path="/" element={<Auth />} />
        <Route 
          path="/dashboard" 
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/profile" 
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/book/:bookId" 
          element={
            <ProtectedRoute>
              <BookDetail />
            </ProtectedRoute>
          } 
        />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </AppProvider>
  );
}

export default App;