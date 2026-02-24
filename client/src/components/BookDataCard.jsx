// components/BookDataCard.jsx
import { FaBook, FaStar, FaUser, FaLayerGroup, FaFileAlt, FaCalendar, FaBuilding, FaBarcode, FaRobot, FaBookOpen, FaChevronDown, FaChevronUp } from 'react-icons/fa';
import { useState } from 'react';

const BookDataCard = ({ book, showFollowUp, setShowFollowUp }) => {
  const [showSummary, setShowSummary] = useState(false);

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
      {/* Add animation styles to head */}
      <style>{animationStyle}</style>
      
      <div className="bg-white/95 backdrop-blur-sm rounded-3xl shadow-xl border border-gray-200 overflow-hidden mb-8">
        <div className="p-8">
          {/* Top Section - Book Cover and Details */}
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
              <div className="flex items-center gap-2 mb-2">
                <span className="px-3 py-1 bg-amber-100 text-amber-900 rounded-full text-xs font-medium">
                  {book.genres?.split(',')[0]?.trim() || 'General'}
                </span>
                {book.rating && (
                  <div className="flex items-center gap-1 text-amber-600">
                    <FaStar className="w-4 h-4" />
                    <span className="text-sm font-medium">{book.rating}</span>
                  </div>
                )}
              </div>

              <h1 className="text-4xl font-bold text-gray-900 mb-2">{book.title}</h1>
              <p className="text-xl text-gray-600 mb-6">by {book.author}</p>

              {/* Meta Info Grid */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
                <div className="flex items-center gap-2 text-gray-600 bg-gray-50 p-3 rounded-xl">
                  <FaUser className="w-4 h-4 text-amber-700" />
                  <div>
                    <p className="text-xs text-gray-500">Author</p>
                    <p className="text-sm font-medium">{book.author}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-gray-600 bg-gray-50 p-3 rounded-xl">
                  <FaLayerGroup className="w-4 h-4 text-amber-700" />
                  <div>
                    <p className="text-xs text-gray-500">Genre</p>
                    <p className="text-sm font-medium">{book.genres}</p>
                  </div>
                </div>
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
                  onClick={() => setShowSummary(!showSummary)}
                  className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-amber-600 to-amber-700 text-white font-medium rounded-xl hover:shadow-lg transition-all duration-300 transform hover:scale-105"
                >
                  <FaBookOpen className="w-5 h-5" />
                  {showSummary ? 'Hide Summary' : 'View Summary'}
                  {showSummary ? 
                    <FaChevronUp className="w-4 h-4" /> : 
                    <FaChevronDown className="w-4 h-4" />
                  }
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

          {/* Summary Panel - Shows at bottom when toggled */}
          {showSummary && (
            <div 
              className="mt-8 pt-8 border-t border-amber-200"
              style={slideDownStyle}
            >
              <div className="bg-gradient-to-br from-amber-50 to-amber-100/50 rounded-2xl p-6 border border-amber-200">
                {/* Summary Header */}
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 bg-amber-200 rounded-xl">
                    <FaBookOpen className="w-5 h-5 text-amber-800" />
                  </div>
                  <h3 className="text-lg font-semibold text-amber-900">Book Summary</h3>
                </div>

                {/* Summary Content */}
                <div className="space-y-4">
                  <p className="text-gray-700 leading-relaxed">
                    {book.summary || book.description || "No summary available for this book."}
                  </p>

                  {/* Reading Time Estimate */}
                  {(book.summary || book.description) && (
                    <div className="mt-4 pt-4 border-t border-amber-200 flex items-center gap-2 text-xs text-amber-700">
                      <FaBookOpen className="w-3 h-3" />
                      <span>~{Math.ceil((book.summary || book.description).split(' ').length / 200)} min read</span>
                    </div>
                  )}
                </div>

                {/* Close Summary Button (Mobile) */}
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