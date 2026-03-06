import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import SearchBar from '../components/SearchBar';
import BookCard from '../components/BookCard';
import { useApp } from '../context/AppContext';
import ToggleButton from '../components/ToggleButton';

function BookTile({ book, onClick }) {
  return (
    <div
      onClick={() => onClick(book)}
      className="group cursor-pointer"
    >
      <div className="bg-white/90 rounded-lg shadow hover:shadow-md transition-all duration-300 overflow-hidden">
        <div className="relative w-full aspect-[3/4] bg-gradient-to-br from-amber-100 to-amber-200">
          {book.image_url ? (
            <img src={book.image_url} alt={book.title} className="w-full h-full object-cover" />
          ) : (
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-3xl mb-1">📖</span>
            </div>
          )}
          <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
            <span className="bg-white text-amber-700 px-2 py-1 rounded-full font-medium text-[10px]">View</span>
          </div>
        </div>
        <div className="p-2">
          <h3 className="font-bold text-gray-800 text-xs mb-0.5 line-clamp-1 group-hover:text-amber-700 transition">{book.title}</h3>
          <p className="text-[10px] text-gray-600 mb-1 truncate">{book.author}</p>
          <span className="text-[8px] px-1.5 py-0.5 bg-amber-100 text-amber-800 rounded-full font-medium">
            {book.genres?.split(',')[0]?.trim() || book.genre || book.category || 'General'}
          </span>
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const { searchBooks, searchResults, isSearching, lastQuery, fetchRecommendedSections, trackBook } = useApp();
  const [searchError, setSearchError] = useState('');
  const [showSearchSection, setShowSearchSection] = useState(false);
  const [isRotating, setIsRotating] = useState(false);

  const [sections, setSections] = useState({ for_you: [], popular: [], by_genre: [] });
  const [loading, setLoading] = useState(false);

  const handleSearch = async (query) => {
    const trimmedQuery = query.trim();
    if (!trimmedQuery) return;

    setSearchError('');
    const result = await searchBooks(trimmedQuery, 6);
    console.log("[Dashboard] Results updated:", searchResults.length, " | Query:", lastQuery);

    if (!result.success) {
      setSearchError(result.error || 'Something went wrong. Please try again.');
    }
  };

  const handleBookClick = (book) => {
    const id = book?.id || book?.book_id;
    if (!id) return;

    trackBook(id);
    navigate(`/book/${id}`, { state: { book } });
  };

  const handleToggle = () => {
    setIsRotating(true);

    setTimeout(() => {
      setShowSearchSection(!showSearchSection);
    }, 150);

    setTimeout(() => {
      setIsRotating(false);
    }, 600);
  };

  useEffect(() => {
    const loadSections = async () => {
      setLoading(true);
      const result = await fetchRecommendedSections();
      if (result?.success) {
        setSections({
          for_you: result.for_you || [],
          popular: result.popular || [],
          by_genre: result.by_genre || [],
        });
      }
      setLoading(false);
    };
    loadSections();
  }, [fetchRecommendedSections]);

  const results = searchResults;
  const aiAnswer = results.length > 0 ? results[0]?.answer : null;
  const hasSearched = !!lastQuery;

  return (
    <div className="min-h-screen flex flex-col relative">
      <Navbar />

      <main className="flex-grow max-w-8xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        {/* Recommendations Section */}
        {!showSearchSection && (
          <div className="w-full animate-fadeIn space-y-10">
            {loading ? (
              <div className="flex justify-center items-center py-16">
                <div className="w-10 h-10 border-2 border-amber-200 border-t-amber-800 rounded-full animate-spin" />
              </div>
            ) : (
              <>
                {sections.for_you.length > 0 && (
                  <section>
                    <h2 className="text-2xl font-bold text-white mb-3">
                      <span className="bg-gradient-to-r from-amber-600 to-amber-800 bg-clip-text text-transparent">Recommended for you</span>
                    </h2>
                    <p className="text-white/80 text-sm mb-4">Based on your reading</p>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4 sm:gap-5">
                      {sections.for_you.map((book) => (
                        <BookTile key={book.book_id || book.id} book={book} onClick={handleBookClick} />
                      ))}
                    </div>
                  </section>
                )}

                <section>
                  <h2 className="text-2xl font-bold text-white mb-3">
                    <span className="bg-gradient-to-r from-amber-600 to-amber-800 bg-clip-text text-transparent">Popular</span>
                  </h2>
                  <p className="text-white/80 text-sm mb-4">Most viewed by readers</p>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4 sm:gap-5">
                    {sections.popular.map((book) => (
                      <BookTile key={book.book_id || book.id} book={book} onClick={handleBookClick} />
                    ))}
                  </div>
                </section>

                {sections.by_genre.map(({ genre, books: genreBooks }) => (
                  <section key={genre}>
                    <h2 className="text-xl font-bold text-white mb-3">{genre}</h2>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-5">
                      {genreBooks.map((book) => (
                        <BookTile key={book.book_id || book.id} book={book} onClick={handleBookClick} />
                      ))}
                    </div>
                  </section>
                ))}
              </>
            )}
          </div>
        )}

        {/* Search Section */}
        {showSearchSection && (
          <div className="w-full max-w-7xl mx-auto animate-fadeIn">
            {/* Hero Text */}
            <div className="text-center mb-8">
              <h1 className="text-4xl md:text-5xl font-extrabold mb-4 tracking-tight">
                <span className="text-gray-900">Find Your</span>
                <br />
                <span className="bg-gradient-to-r from-amber-700 via-amber-100 to-amber-900 bg-clip-text text-transparent">
                  Next Great Read
                </span>
              </h1>
              <div className="bg-white/80 backdrop-blur-md shadow-xl px-6 py-4 rounded-2xl border border-amber-100">
                <p className="text-gray-700">
                  Tell me what mood you're in or what kind of story you're craving — get AI-powered book recommendations tailored just for you.
                </p>
              </div>
            </div>

            <div className="mb-6">
              <div className="bg-white/90 backdrop-blur-lg shadow-xl rounded-2xl p-6 border border-amber-100">
                <SearchBar onSearch={handleSearch} />
              </div>
            </div>

            <div className="flex flex-wrap justify-center gap-3 mb-8">
              {['🤔 Philosophical', '🚀 Sci-Fi', '📚 Self-Help', '⚔️ Fantasy', '🔍 Mystery'].map((cat) => (
                <button
                  key={cat}
                  onClick={() => handleSearch(cat.split(' ')[1])}
                  className="px-4 py-2 bg-white/80 backdrop-blur-sm shadow-md hover:shadow-lg rounded-full text-gray-700 transition-all border border-amber-200 hover:border-amber-400"
                >
                  {cat}
                </button>
              ))}
            </div>

            <p className="text-center text-white font-bold text-m mb-8">
              Try: "Books to build better habits" or "Space adventure with real science"
            </p>

            {searchError && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl">
                {searchError}
              </div>
            )}

            {isSearching ? (
              <div className="flex flex-col items-center justify-center py-16 text-gray-600">
                <div className="relative mb-4">
                  <div className="w-16 h-16 border-4 border-amber-200 border-t-amber-800 rounded-full animate-spin"></div>
                </div>
                <p className="text-lg font-medium text-amber-900">Looking for the perfect books...</p>
              </div>
            ) : results.length > 0 ? (
              <section>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6">
                  <div>
                    <h2 className="text-2xl font-bold text-white">
                      Books Picked for You
                    </h2>
                    {lastQuery && (
                      <p className="text-white/80 text-sm mt-1">
                        Based on: <span className="font-semibold text-amber-200">"{lastQuery}"</span>
                      </p>
                    )}
                  </div>
                  <div className="mt-2 sm:mt-0 px-4 py-2 bg-amber-50 text-amber-800 rounded-full text-sm font-medium border border-amber-200">
                    {results.length} {results.length === 1 ? 'book' : 'books'}
                  </div>
                </div>

                {aiAnswer && (
                  <div className="mb-6 p-5 bg-gradient-to-br from-amber-50 to-amber-100 rounded-xl border border-amber-200">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xl">📚</span>
                      <h3 className="text-base font-semibold text-amber-900">Your AI Librarian recommends:</h3>
                    </div>
                    <p className="text-gray-800 text-sm leading-relaxed">
                      {aiAnswer}
                    </p>
                  </div>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {results.map((book, index) => (
                    <div
                      key={book.id || `book-${index}`}
                      onClick={() => handleBookClick(book)}
                      className="cursor-pointer transition-all duration-300 hover:-translate-y-2 hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-amber-500 rounded-xl overflow-hidden"
                    >
                      <BookCard {...book} index={index} />
                    </div>
                  ))}
                </div>
              </section>
            ) : hasSearched ? (
              <div className="text-center py-12 bg-white/70 backdrop-blur-md rounded-xl border border-amber-100">
                <h3 className="text-xl font-bold text-gray-800 mb-3">
                  No matches found
                </h3>
                <p className="text-gray-700 mb-6">
                  Couldn't find books matching <span className="font-semibold">"{lastQuery}"</span>
                </p>
                <button
                  onClick={() => setShowSearchSection(false)}
                  className="px-6 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition"
                >
                  Browse Recommendations Instead
                </button>
              </div>
            ) : (
              <div className="text-center">
                <h3 className="text-xl font-bold text-gray-800 mb-6">
                  Start Exploring
                </h3>
                <div className="flex flex-wrap justify-center gap-3 max-w-2xl mx-auto">
                  {['Fantasy', 'Romance', 'Mystery & Thriller', 'Science Fiction', 'Self-Help', 'Historical Fiction', 'Young Adult', 'Non-Fiction'].map((cat) => (
                    <button
                      key={cat}
                      onClick={() => handleSearch(cat)}
                      className="px-5 py-2.5 bg-white/90 backdrop-blur-sm shadow-md hover:shadow-lg rounded-full text-gray-700 transition-all border border-amber-200 hover:border-amber-400"
                    >
                      {cat}
                    </button>
                  ))}
                </div>
                <p className="mt-6 text-gray-600 text-sm">
                  Or just describe the kind of story you're in the mood for above ↑
                </p>
              </div>
            )}
          </div>
        )}
      </main>

      <ToggleButton
        showSearchSection={showSearchSection}
        onToggle={handleToggle}
        isRotating={isRotating}
      />

      <Footer />

      <style>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-fadeIn {
          animation: fadeIn 0.5s ease-out;
        }
        
        @keyframes spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }
        
        @keyframes spin-reverse {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(-360deg);
          }
        }
        
        .animate-spin {
          animation: spin 0.6s linear;
        }
        
        .animate-spin-reverse {
          animation: spin-reverse 0.6s linear;
        }
      `}</style>
    </div>
  );
}