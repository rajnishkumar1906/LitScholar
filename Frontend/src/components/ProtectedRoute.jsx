import { Navigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';

export default function ProtectedRoute({ children }) {
  const { user, loading, authChecked } = useApp();

  // 1. If we are still hitting microservices, show the loader
  if (loading || !authChecked) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-amber-50/30">
        <div className="bg-white/95 backdrop-blur-sm shadow-xl p-8 rounded-3xl border border-gray-200">
          <div className="w-16 h-16 border-4 border-amber-200 border-t-amber-800 rounded-full animate-spin"></div>
          <p className="mt-4 text-amber-900 font-medium">Syncing LitScholar...</p>
        </div>
      </div>
    );
  }

  // 2. Only redirect if the check is COMPLETE and there is no user
  if (!user) {
    return <Navigate to="/" replace />;
  }

  return children;
}