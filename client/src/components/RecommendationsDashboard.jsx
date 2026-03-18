import { useState, useEffect, useRef, useCallback } from 'react';
import { useApp } from '../context/AppContext';
import BookCard from '../components/BookCard';
import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline';

export default function RecommendationDashboard({ onBookClick }) {
  const {
    forYouBooks,
    popularBooks,
    genreBooks,
    similarBooks,
    similarHasMore,
    similarPage,
    fetchForYouBooks,
    fetchPopularBooks,
    fetchGenreBooks,
    fetchSimilarBooks,
    trackBook,
    user
  } = useApp();

  // State
  const [activeFilter, setActiveFilter] = useState('for-you');
  
  // Loading states
  const [loading, setLoading] = useState({
    forYou: false,
    popular: false,
    genre: false,
    similar: false,
    more: false
  });

  // Error states
  const [error, setError] = useState({
    forYou: '',
    popular: '',
    genre: '',
    similar: ''
  });

  // Search
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredBooks, setFilteredBooks] = useState([]);
  const [showSearchResults, setShowSearchResults] = useState(false);

  // ============ LOAD FUNCTIONS ============

  const loadForYouBooks = useCallback(async (forceRefresh = false) => {
    if (!user) return;
    
    // AppContext now handles the cache check internally
    setLoading(prev => ({ ...prev, forYou: true }));
    setError(prev => ({ ...prev, forYou: '' }));

    try {
      const result = await fetchForYouBooks(8, forceRefresh);
      if (!result?.success) {
        setError(prev => ({ ...prev, forYou: result?.error || 'Failed to load' }));
      }
    } catch (err) {
      setError(prev => ({ ...prev, forYou: 'Failed to load' }));
    } finally {
      setLoading(prev => ({ ...prev, forYou: false }));
    }
  }, [user, fetchForYouBooks]);

  const loadPopularBooks = useCallback(async (forceRefresh = false) => {
    if (!user) return;

    setLoading(prev => ({ ...prev, popular: true }));
    setError(prev => ({ ...prev, popular: '' }));

    try {
      const result = await fetchPopularBooks(8, forceRefresh);
      if (!result?.success) {
        setError(prev => ({ ...prev, popular: result?.error || 'Failed to load' }));
      }
    } catch (err) {
      setError(prev => ({ ...prev, popular: 'Failed to load' }));
    } finally {
      setLoading(prev => ({ ...prev, popular: false }));
    }
  }, [user, fetchPopularBooks]);

  const loadGenreBooks = useCallback(async (forceRefresh = false) => {
    if (!user) return;

    setLoading(prev => ({ ...prev, genre: true }));
    setError(prev => ({ ...prev, genre: '' }));

    try {
      const result = await fetchGenreBooks(4, forceRefresh);
      if (!result?.success) {
        setError(prev => ({ ...prev, genre: result?.error || 'Failed to load' }));
      }
    } catch (err) {
      setError(prev => ({ ...prev, genre: 'Failed to load' }));
    } finally {
      setLoading(prev => ({ ...prev, genre: false }));
    }
  }, [user, fetchGenreBooks]);

  const loadSimilarBooks = useCallback(async (page = 1, forceRefresh = false) => {
    if (!user) return;

    if (page === 1) {
      setLoading(prev => ({ ...prev, similar: true }));
      setError(prev => ({ ...prev, similar: '' }));
    } else {
      setLoading(prev => ({ ...prev, more: true }));
    }

    try {
      const result = await fetchSimilarBooks(page, 8, forceRefresh);
      if (!result?.success && page === 1) {
        setError(prev => ({ ...prev, similar: result?.error || 'Failed to load' }));
      }
    } catch (err) {
      if (page === 1) setError(prev => ({ ...prev, similar: 'Failed to load' }));
    } finally {
      setLoading(prev => ({ ...prev, similar: false, more: false }));
    }
  }, [user, fetchSimilarBooks]);

  // ============ EFFECTS ============

  useEffect(() => {
    if (!user) return;

    if (activeFilter === 'for-you') {
      loadForYouBooks();
    } else if (activeFilter === 'popular') {
      loadPopularBooks();
    } else if (activeFilter === 'genre') {
      loadGenreBooks();
    } else if (activeFilter === 'similar') {
      loadSimilarBooks(similarPage);
    }
  }, [activeFilter, user, loadForYouBooks, loadPopularBooks, loadGenreBooks, loadSimilarBooks, similarPage]);

  // ============ HANDLERS ============

  const handleLoadMore = async () => {
    if (loading.more || !similarHasMore || !user) return;
    await loadSimilarBooks(similarPage + 1);
  };

  const handleFilterChange = (filter) => {
    setActiveFilter(filter);
    setShowSearchResults(false);
    setSearchQuery('');
  };

  const handleBookClick = async (book) => {
    if (!user) return;
    const id = book.book_id || book.id;
    if (id) {
      await trackBook(id);
    }
    onBookClick(book);
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setShowSearchResults(false);
      return;
    }

    let booksToSearch = [];
    if (activeFilter === 'for-you') booksToSearch = forYouBooks;
    else if (activeFilter === 'popular') booksToSearch = popularBooks;
    else if (activeFilter === 'genre') {
      booksToSearch = genreBooks.flatMap(section => section.books || []);
    }
    else if (activeFilter === 'similar') booksToSearch = similarBooks;

    const query = searchQuery.toLowerCase();
    const filtered = booksToSearch.filter(book =>
      (book.title || book.book_title)?.toLowerCase().includes(query) ||
      book.author?.toLowerCase().includes(query)
    );

    setFilteredBooks(filtered);
    setShowSearchResults(true);
  };

  const clearSearch = () => {
    setSearchQuery('');
    setShowSearchResults(false);
    setFilteredBooks([]);
  };

  const refreshCurrentSection = () => {
    if (!user) return;
    if (activeFilter === 'for-you') loadForYouBooks(true);
    else if (activeFilter === 'popular') loadPopularBooks(true);
    else if (activeFilter === 'genre') loadGenreBooks(true);
    else if (activeFilter === 'similar') loadSimilarBooks(1, true);
  };

  // ============ HELPER FUNCTIONS ============

  const filterTitles = {
    'for-you': 'For You',
    'popular': 'Popular',
    'genre': 'By Genre',
    'similar': 'Similar'
  };

  const getCurrentLoading = () => {
    switch (activeFilter) {
      case 'for-you': return loading.forYou;
      case 'popular': return loading.popular;
      case 'genre': return loading.genre;
      case 'similar': return loading.similar;
      default: return false;
    }
  };

  const getCurrentError = () => {
    switch (activeFilter) {
      case 'for-you': return error.forYou;
      case 'popular': return error.popular;
      case 'genre': return error.genre;
      case 'similar': return error.similar;
      default: return '';
    }
  };

  return (
    <div className="space-y-8">
      {/* Search and Filters Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex flex-wrap gap-2">
          {Object.entries(filterTitles).map(([id, label]) => (
            <button
              key={id}
              onClick={() => handleFilterChange(id)}
              className={`px-6 py-2.5 rounded-2xl text-sm font-semibold transition-all duration-300 shadow-sm ${
                activeFilter === id
                  ? 'bg-gradient-to-r from-amber-800 to-amber-900 text-white shadow-md'
                  : 'bg-white/80 text-gray-600 hover:bg-white hover:text-amber-900 border border-gray-100'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        <form onSubmit={handleSearch} className="relative group w-full md:w-80">
          <input
            type="text"
            placeholder={`Search in ${filterTitles[activeFilter]}...`}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-white/90 backdrop-blur-sm border border-gray-200 rounded-2xl py-3 px-5 pr-12 focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500 transition-all shadow-sm group-hover:shadow-md"
          />
          <button
            type="submit"
            className="absolute right-3 top-1/2 -translate-y-1/2 p-2 text-gray-400 hover:text-amber-800 transition-colors"
          >
            <MagnifyingGlassIcon className="w-5 h-5" />
          </button>
          {searchQuery && (
            <button
              type="button"
              onClick={clearSearch}
              className="absolute right-10 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-red-500"
            >
              <XMarkIcon className="w-4 h-4" />
            </button>
          )}
        </form>
      </div>

      {/* Main Content Area */}
      <div className="relative min-h-[400px]">
        {/* Loading Overlay */}
        {getCurrentLoading() && (
          <div className="absolute inset-0 flex items-center justify-center bg-transparent z-10">
            <div className="flex flex-col items-center gap-4 bg-white/80 backdrop-blur-md p-8 rounded-3xl shadow-xl border border-white">
              <div className="w-12 h-12 border-4 border-amber-200 border-t-amber-800 rounded-full animate-spin" />
              <p className="text-amber-900 font-medium animate-pulse">Finding your next read...</p>
            </div>
          </div>
        )}

        {/* Error State */}
        {getCurrentError() && (
          <div className="flex flex-col items-center justify-center py-20 bg-red-50/50 backdrop-blur-sm rounded-3xl border border-red-100 text-center px-4">
            <div className="w-16 h-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center mb-4">
              <XMarkIcon className="w-8 h-8" />
            </div>
            <h3 className="text-xl font-bold text-red-900 mb-2">Oops! Something went wrong</h3>
            <p className="text-red-700 max-w-md mx-auto mb-6">{getCurrentError()}</p>
            <button
              onClick={refreshCurrentSection}
              className="px-8 py-3 bg-red-600 text-white font-bold rounded-2xl hover:bg-red-700 transition-all shadow-lg hover:shadow-red-200"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Search Results */}
        {showSearchResults ? (
          <section className="bg-white/40 backdrop-blur-sm rounded-3xl p-8 border border-white shadow-sm">
            <div className="flex items-center justify-between mb-8">
              <div>
                <h2 className="text-3xl font-bold text-gray-900">Search Results</h2>
                <p className="text-gray-500 mt-1">Found in {filterTitles[activeFilter]}</p>
              </div>
              <button
                onClick={clearSearch}
                className="px-4 py-2 text-sm font-medium text-amber-900 hover:bg-amber-100 rounded-xl transition-colors"
              >
                Clear results
              </button>
            </div>

            {filteredBooks.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {filteredBooks.map((book, idx) => (
                  <div
                    key={book.id || book.book_id}
                    onClick={() => handleBookClick(book)}
                    className="cursor-pointer"
                  >
                    <BookCard {...book} index={idx} />
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-20">
                <p className="text-gray-500 text-lg">No books matching "{searchQuery}" in this section.</p>
              </div>
            )}
          </section>
        ) : (
          /* Normal Sections */
          !getCurrentLoading() && !getCurrentError() && (
            <div className="space-y-12">
              {/* For You */}
              {activeFilter === 'for-you' && (
                <section>
                  <div className="flex items-center justify-between mb-8">
                    <h2 className="text-3xl font-bold text-white drop-shadow-sm">Personalized For You</h2>
                    <button onClick={() => loadForYouBooks(true)} className="text-sm text-white/80 hover:text-white underline underline-offset-4">Refresh</button>
                  </div>
                  {forYouBooks.length > 0 ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                      {forYouBooks.map((book, idx) => (
                        <div key={book.id || book.book_id} onClick={() => handleBookClick(book)} className="cursor-pointer">
                          <BookCard {...book} index={idx} />
                        </div>
                      ))}
                    </div>
                  ) : (
                    <EmptyState message="No personalized recommendations yet. Explore more books!" />
                  )}
                </section>
              )}

              {/* Popular */}
              {activeFilter === 'popular' && (
                <section>
                  <div className="flex items-center justify-between mb-8">
                    <h2 className="text-3xl font-bold text-white drop-shadow-sm">Trending Now</h2>
                    <button onClick={() => loadPopularBooks(true)} className="text-sm text-white/80 hover:text-white underline underline-offset-4">Refresh</button>
                  </div>
                  {popularBooks.length > 0 ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                      {popularBooks.map((book, idx) => (
                        <div key={book.id || book.book_id} onClick={() => handleBookClick(book)} className="cursor-pointer">
                          <BookCard {...book} index={idx} />
                        </div>
                      ))}
                    </div>
                  ) : (
                    <EmptyState message="No popular books found right now." />
                  )}
                </section>
              )}

              {/* Genres */}
              {activeFilter === 'genre' && (
                <div className="space-y-16">
                  {genreBooks.length > 0 ? (
                    genreBooks.map((section) => (
                      <section key={section.genre}>
                        <h2 className="text-2xl font-bold text-white mb-6 drop-shadow-sm flex items-center gap-3">
                          <span className="w-8 h-1 bg-amber-500 rounded-full" />
                          {section.genre}
                        </h2>
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                          {section.books?.map((book, idx) => (
                            <div key={book.id || book.book_id} onClick={() => handleBookClick(book)} className="cursor-pointer">
                              <BookCard {...book} index={idx} />
                            </div>
                          ))}
                        </div>
                      </section>
                    ))
                  ) : (
                    <EmptyState message="No genre recommendations available." />
                  )}
                </div>
              )}

              {/* Similar */}
              {activeFilter === 'similar' && (
                <section>
                  <div className="flex items-center justify-between mb-8">
                    <h2 className="text-3xl font-bold text-white drop-shadow-sm">Similar Suggestions</h2>
                    <button onClick={() => loadSimilarBooks(1, true)} className="text-sm text-white/80 hover:text-white underline underline-offset-4">Reset</button>
                  </div>
                  {similarBooks.length > 0 ? (
                    <>
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                        {similarBooks.map((book, idx) => (
                          <div key={book.id || book.book_id} onClick={() => handleBookClick(book)} className="cursor-pointer">
                            <BookCard {...book} index={idx} />
                          </div>
                        ))}
                      </div>
                      {similarHasMore && (
                        <div className="flex justify-center mt-12">
                          <button
                            onClick={handleLoadMore}
                            disabled={loading.more}
                            className="px-10 py-4 bg-white/90 backdrop-blur-sm text-amber-900 font-bold rounded-2xl shadow-lg hover:shadow-xl hover:bg-white transition-all disabled:opacity-50 flex items-center gap-3 border border-amber-100"
                          >
                            {loading.more ? (
                              <>
                                <div className="w-5 h-5 border-2 border-amber-200 border-t-amber-800 rounded-full animate-spin" />
                                Loading...
                              </>
                            ) : (
                              'Show More Books'
                            )}
                          </button>
                        </div>
                      )}
                    </>
                  ) : (
                    <EmptyState message="No similar suggestions found." />
                  )}
                </section>
              )}
            </div>
          )
        )}
      </div>
    </div>
  );
}

function EmptyState({ message }) {
  return (
    <div className="text-center py-24 bg-white/10 backdrop-blur-md rounded-[2.5rem] border border-white/20 shadow-inner">
      <div className="text-6xl mb-4">📚</div>
      <p className="text-white text-lg font-medium">{message}</p>
    </div>
  );
}
