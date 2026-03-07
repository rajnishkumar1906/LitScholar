// components/BookDataCard.jsx
import { FaBook, FaStar, FaUser, FaLayerGroup, FaFileAlt, FaCalendar, FaBuilding, FaBarcode, FaRobot, FaBookOpen, FaChevronDown, FaChevronUp, FaSpinner } from 'react-icons/fa';
import { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';

const BookDataCard = ({ book, showFollowUp, setShowFollowUp }) => {
  const { getBookSummary } = useApp();
  const [showSummary, setShowSummary] = useState(false);
  const [summary, setSummary] = useState(book.summary || '');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');

  // Update summary if book prop changes (e.g. initial load)
  useEffect(() => {
    if (book.summary) {
      setSummary(book.summary);
    }
  }, [book.summary]);

  const handleSummaryClick = async () => {
    // Toggle off if already showing
    if (showSummary) {
      setShowSummary(false);
      return;
    }

    // If we already have a summary, just show it
    if (summary) {
      setShowSummary(true);
      return;
    }

    // Otherwise, generate it
    setIsGenerating(true);
    setError('');
    
    const result = await getBookSummary(book.id || book.book_id);
    
    if (result.success) {
      setSummary(result.summary);
      setShowSummary(true);
    } else {
      setError(result.error || 'Failed to generate summary');
      setShowSummary(true); // Show panel anyway to display error
    }
    
    setIsGenerating(false);
  };

  // Parse genres - handle both string and array formats and clean them
  const parseGenres = (genres) => {
    if (!genres) return [];
    
    let genreArray = [];
    
    // If it's already an array
    if (Array.isArray(genres)) {
      genreArray = genres;
    } 
    // If it's a string, try to parse it
    else if (typeof genres === 'string') {
      // Remove brackets, quotes, and clean up
      let cleaned = genres
        .replace(/[\[\]']/g, '') // Remove [, ], '
        .replace(/\s+/g, ' ') // Normalize spaces
        .trim();
      
      // Split by comma and clean each genre
      genreArray = cleaned.split(',').map(g => g.trim()).filter(g => g);
    }
    
    // Final cleaning - remove any remaining unwanted characters
    return genreArray.map(g => 
      g.replace(/[\[\]']/g, '') // Remove any stray brackets or quotes
       .trim()
    ).filter(g => g); // Remove empty strings
  };

  const genres = parseGenres(book.genres);

  // Inline styles for slide animation
  const slideDownStyle = {
    animation: 'slideDown 0.3s ease-out forwards',
  };

  // Add style tag for animations
  const animationStyle = `
    @keyframes slideDown {
      0% {
        opacity: 0;
        transform: translateY(-20px);
      }
      100% {
        opacity: 1;
        transform: translateY(0);
      }
    }
  `;

  return (
    <>
      <style>{animationStyle}</style>
      
      <div className="bg-white/95 backdrop-blur-sm rounded-3xl shadow-xl border border-gray-200 overflow-hidden mb-8">
        <div className="p-8">
          <div className="grid md:grid-cols-3 gap-8">
            {/* Book Cover */}
            <div className="md:col-span-1">
              <div className="bg-gradient-to-br from-amber-100 to-amber-200 rounded-2xl overflow-hidden shadow-lg aspect-[2/3] flex items-center justify-center">
                {book.image_url ? (
                  <img 
                    src={book.image_url} 
                    alt={book.title} 
                    className="w-full h-full object-cover hover:scale-105 transition-transform duration-500"
                    onError={(e) => {
                      e.target.onerror = null;
                      e.target.style.display = 'none';
                      e.target.parentNode.innerHTML = '<FaBook className="w-20 h-20 text-amber-800/30" />';
                    }}
                  />
                ) : (
                  <FaBook className="w-20 h-20 text-amber-800/30" />
                )}
              </div>
            </div>

            {/* Book Info */}
            <div className="md:col-span-2">
              {/* Rating */}
              <div className="flex justify-end mb-2">
                {book.rating && (
                  <div className="flex items-center gap-1 text-amber-600 bg-amber-50 px-3 py-1 rounded-full">
                    <FaStar className="w-4 h-4" />
                    <span className="text-sm font-medium">{book.rating}</span>
                  </div>
                )}
              </div>

              <h1 className="text-4xl font-bold text-gray-900 mb-2">{book.title}</h1>
              <p className="text-xl text-gray-600 mb-6">by {book.author}</p>

              {/* Genres - Clean display without symbols */}
              {genres.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-6">
                  {genres.map((genre, index) => (
                    <span
                      key={index}
                      className="px-3 py-1.5 bg-gradient-to-r from-amber-50 to-amber-100 text-amber-800 rounded-full text-xs font-medium border border-amber-200"
                    >
                      {genre}
                    </span>
                  ))}
                </div>
              )}

              {/* Meta Info Grid */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
                {book.num_pages && (
                  <div className="flex items-center gap-2 text-gray-600 bg-gray-50 p-3 rounded-xl">
                    <FaFileAlt className="w-4 h-4 text-amber-700" />
                    <div>
                      <p className="text-xs text-gray-500">Pages</p>
                      <p className="text-sm font-medium">{book.num_pages}</p>
                    </div>
                  </div>
                )}
                
                {book.published_year && (
                  <div className="flex items-center gap-2 text-gray-600 bg-gray-50 p-3 rounded-xl">
                    <FaCalendar className="w-4 h-4 text-amber-700" />
                    <div>
                      <p className="text-xs text-gray-500">Published</p>
                      <p className="text-sm font-medium">{book.published_year}</p>
                    </div>
                  </div>
                )}
                
                {book.publisher && (
                  <div className="flex items-center gap-2 text-gray-600 bg-gray-50 p-3 rounded-xl">
                    <FaBuilding className="w-4 h-4 text-amber-700" />
                    <div>
                      <p className="text-xs text-gray-500">Publisher</p>
                      <p className="text-sm font-medium">{book.publisher}</p>
                    </div>
                  </div>
                )}
                
                {book.isbn && (
                  <div className="flex items-center gap-2 text-gray-600 bg-gray-50 p-3 rounded-xl">
                    <FaBarcode className="w-4 h-4 text-amber-700" />
                    <div>
                      <p className="text-xs text-gray-500">ISBN</p>
                      <p className="text-sm font-medium">{book.isbn}</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Description */}
              {book.description && (
                <div className="mb-8">
                  <h2 className="text-lg font-semibold text-gray-800 mb-2">Description</h2>
                  <p className="text-gray-600 leading-relaxed">{book.description}</p>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex flex-wrap gap-4">
                <button
                  onClick={handleSummaryClick}
                  disabled={isGenerating}
                  className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-amber-600 to-amber-700 text-white font-medium rounded-xl hover:shadow-lg transition-all duration-300 transform hover:scale-105 disabled:opacity-70 disabled:cursor-not-allowed"
                >
                  {isGenerating ? (
                    <FaSpinner className="w-5 h-5 animate-spin" />
                  ) : (
                    <FaBookOpen className="w-5 h-5" />
                  )}
                  {isGenerating ? 'Generating...' : (showSummary ? 'Hide Summary' : 'View Summary')}
                  {!isGenerating && (showSummary ? <FaChevronUp className="w-4 h-4" /> : <FaChevronDown className="w-4 h-4" />)}
                </button>
                <button
                  onClick={() => setShowFollowUp(!showFollowUp)}
                  className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-amber-800 to-amber-900 text-white font-medium rounded-xl hover:shadow-lg transition-all duration-300 transform hover:scale-105"
                >
                  <FaRobot className="w-5 h-5" />
                  {showFollowUp ? 'Hide AI Librarian' : 'Ask AI Librarian'}
                </button>
                <button className="flex items-center gap-2 px-6 py-3 border border-gray-300 text-gray-700 font-medium rounded-xl hover:bg-gray-50 transition-all duration-300">
                  Add to Wishlist
                </button>
              </div>
            </div>
          </div>

          {/* Summary Panel */}
          {showSummary && (
            <div className="mt-8 pt-8 border-t border-amber-200" style={slideDownStyle}>
              <div className="bg-gradient-to-br from-amber-50 to-amber-100/50 rounded-2xl p-6 border border-amber-200">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 bg-amber-200 rounded-xl">
                    <FaBookOpen className="w-5 h-5 text-amber-800" />
                  </div>
                  <h3 className="text-lg font-semibold text-amber-900">Book Summary</h3>
                </div>
                <p className="text-gray-700 leading-relaxed">
                  {error ? (
                    <span className="text-red-600">{error}</span>
                  ) : (
                    summary || book.description || "No summary available for this book."
                  )}
                </p>
                <button
                  onClick={() => setShowSummary(false)}
                  className="mt-4 w-full md:hidden flex items-center justify-center gap-2 px-4 py-2 bg-amber-200 text-amber-800 rounded-xl text-sm font-medium"
                >
                  <FaChevronUp className="w-4 h-4" />
                  Close Summary
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default BookDataCard;