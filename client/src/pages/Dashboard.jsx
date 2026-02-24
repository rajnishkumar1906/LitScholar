import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import SearchBar from '../components/SearchBar';
import BookCard from '../components/BookCard';
import { useApp } from '../context/AppContext';

export default function Dashboard() {
  const navigate = useNavigate();
  const { searchBooks, searchResults, isSearching, lastQuery } = useApp();
  const [searchError, setSearchError] = useState('');

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
    if (book?.id) {
      navigate(`/book/${book.id}`, { state: { book } });
    }
  };

  const results = searchResults;
  const aiAnswer = results.length > 0 ? results[0]?.answer : null;

  const hasSearched = !!lastQuery;

  // Sample recommended books
  const recommendedBooks = [
    { id: 'rec1', title: 'The Midnight Library', author: 'Matt Haig', rating: 4.5, category: 'Fiction' },
    { id: 'rec2', title: 'Project Hail Mary', author: 'Andy Weir', rating: 4.7, category: 'Sci-Fi' },
    { id: 'rec3', title: 'Atomic Habits', author: 'James Clear', rating: 4.8, category: 'Self-Help' },
    { id: 'rec4', title: 'Dune', author: 'Frank Herbert', rating: 4.6, category: 'Sci-Fi' },
    { id: 'rec5', title: 'The Silent Patient', author: 'Alex Michaelides', rating: 4.5, category: 'Mystery' },
    { id: 'rec6', title: 'Educated', author: 'Tara Westover', rating: 4.7, category: 'Memoir' },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      <main className="flex-grow max-w-8xl mx-auto px-4 sm:px-6 lg:px-8 py-0 w-full">
        <div className="flex flex-col lg:flex-row gap-8">

          <div className="lg:w-1/2">
            <div className="bg-white/10 backdrop-blur-md rounded-0xl border border-amber-100 shadow-xl p-5 sticky top-20">
              <h2 className="text-xl font-bold text-amber-100 mb-4 flex items-center gap-2">
                <span className="text-2xl">📚</span>
                Recommended Books
              </h2>

              <div className="grid grid-cols-3 gap-10 max-h-[calc(100vh-180px)] overflow-y-auto pr-1 custom-scroll pb-2">
                {recommendedBooks.map((book) => (
                  <div
                    key={book.id}
                    onClick={() => handleBookClick(book)}
                    className="cursor-pointer bg-white/80 hover:bg-amber-50/80 rounded-lg p-2 border border-amber-100 transition-all hover:shadow-md group"
                  >
                    <div className="flex flex-col">
                      <div className="w-full aspect-[2/3] bg-gradient-to-br from-amber-100 to-amber-200 rounded-md mb-2 flex items-center justify-center">
                        <span className="text-amber-800/30 text-xl">📖</span>
                      </div>

                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-800 text-xs group-hover:text-amber-900 line-clamp-2 mb-0.5">
                          {book.title}
                        </h4>
                        <p className="text-xs text-gray-500 mb-1 truncate">{book.author}</p>
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] px-1.5 py-0.5 bg-amber-100 text-amber-800 rounded-full">
                            {book.category}
                          </span>
                          <span className="text-[10px] text-amber-700">★ {book.rating}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <button
                onClick={() => handleSearch('popular books')}
                className="w-full mt-4 px-3 py-2 bg-gradient-to-r from-amber-800 to-amber-900 text-white font-medium rounded-lg hover:shadow-lg transition-all text-xs"
              >
                More Recommendations →
              </button>
            </div>
          </div>

          <div className="lg:w-2/3">
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
        </div>
      </main>

      <Footer />

      <style>{`
        .custom-scroll::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scroll::-webkit-scrollbar-track {
          background: rgba(241, 245, 249, 0.3);
        }
        .custom-scroll::-webkit-scrollbar-thumb {
          background: rgba(180, 83, 9, 0.3);
          border-radius: 4px;
        }
      `}</style>
    </div>
  );
}