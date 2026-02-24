import { Link } from 'react-router-dom';
import { FaHome, FaSearch } from 'react-icons/fa';
import Footer from '../components/Footer';
import LitScholarLogo from '../components/LitScholarLogo';

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col">
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="relative text-center">
          <div className="mb-8 relative">
            <div className="text-8xl md:text-9xl font-bold bg-gradient-to-r from-amber-800 to-amber-900 bg-clip-text text-transparent opacity-30">
              404
            </div>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="bg-white/95 backdrop-blur-sm shadow-2xl p-6 rounded-3xl animate-float">
                <LitScholarLogo className="w-24 h-24" />
              </div>
            </div>
          </div>

          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            Page Not Found
          </h1>
          
          <p className="text-lg text-gray-600 mb-8 max-w-md mx-auto bg-white/95 backdrop-blur-sm shadow-lg px-6 py-3 rounded-2xl border border-gray-200">
            The page you're looking for doesn't exist or has been moved.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/dashboard"
              className="px-8 py-3 bg-white/95 backdrop-blur-sm shadow-md hover:shadow-xl rounded-xl text-gray-700 hover:text-amber-800 transition-all flex items-center justify-center gap-2 border border-gray-200"
            >
              <FaHome className="w-4 h-4" />
              <span>Dashboard</span>
            </Link>
            
            <Link
              to="/"
              className="px-8 py-3 bg-gradient-to-r from-amber-800 to-amber-900 text-white font-medium rounded-xl hover:shadow-lg transition-all flex items-center justify-center gap-2"
            >
              <FaSearch className="w-4 h-4" />
              <span>Search Books</span>
            </Link>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
}