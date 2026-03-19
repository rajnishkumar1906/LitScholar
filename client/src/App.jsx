// src/App.jsx - CORRECT single function version
import { Routes, Route } from 'react-router-dom';
import { AppProvider } from './context/AppContext';  // Remove useApp import
import Dashboard from './pages/Dashboard.jsx';
import Auth from './pages/Auth.jsx';
import Profile from './pages/Profile.jsx';
import BookDetail from './pages/BookDetail.jsx';
import NotFound from './pages/NotFound.jsx';
import ProtectedRoute from './components/ProtectedRoute';
// Remove LogoutConfirmationModal import since it's already in AppContext

function App() {
  return (
    <AppProvider>
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