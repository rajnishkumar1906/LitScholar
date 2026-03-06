import { Link } from 'react-router-dom';
import { FaHeart } from 'react-icons/fa';
import LitScholarLogo from '../components/LitScholarLogo';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-white/20 backdrop-blur-sm border-t border-gray-200 mt-10 py-3">
      <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row justify-between items-center gap-2">
        {/* Logo and copyright */}
        <div className="flex items-center gap-2">
          <div className="p-1 bg-gradient-to-r from-amber-800 to-amber-900 rounded">
            <LitScholarLogo className="w-4 h-4 text-white" />
          </div>
          <span className="text-xs text-white">
            © {currentYear} LitScholar
          </span>
        </div>

        {/* Made with love */}
        <div className="flex items-center gap-1 text-xs text-white">
          <span>Made with</span>
          <FaHeart className="w-3 h-3 text-red-500" />
          <span>for readers</span>
        </div>

        {/* Simple links */}
        <div className="flex gap-3 text-xs">
          <Link to="/" className="text-white hover:text-amber-800 transition-colors">
            Privacy
          </Link>
          <Link to="/" className="text-white hover:text-amber-900 transition-colors">
            Terms
          </Link>
        </div>
      </div>
    </footer>
  );
}