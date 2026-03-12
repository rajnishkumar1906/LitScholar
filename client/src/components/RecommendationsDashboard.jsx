import { useState, useEffect, useRef, useCallback } from 'react';
import { useApp } from '../context/AppContext';
import BookCard from '../components/BookCard';
import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline';

export default function RecommendationDashboard({ onBookClick }) {
  const {
    fetchForYouBooks,
    fetchPopularBooks,
    fetchGenreBooks,
    fetchSimilarBooks,
    trackBook,
    user
  } = useApp();

  // Refs for caching and initial mount tracking
  const isInitialMount = useRef(true);
  const forYouCacheRef = useRef({ data: null, timestamp: null });
  const popularCacheRef = useRef({ data: null, timestamp: null });
  const genreCacheRef = useRef({ data: null, timestamp: null });
  const similarCacheRef = useRef({ pages: {} });

  // State
  const [activeFilter, setActiveFilter] = useState('for-you');
  const [forYouBooks, setForYouBooks] = useState([]);
  const [popularBooks, setPopularBooks] = useState([]);
  const [genreBooks, setGenreBooks] = useState([]);
  const [similarBooks, setSimilarBooks] = useState([]);
  
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

  // Similar pagination
  const [similarPage, setSimilarPage] = useState(1);
  const [similarHasMore, setSimilarHasMore] = useState(true);
  const [totalSimilarBooks, setTotalSimilarBooks] = useState(0);

  // Search
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredBooks, setFilteredBooks] = useState([]);
  const [showSearchResults, setShowSearchResults] = useState(false);

  // ============ LOAD FUNCTIONS ============

  const loadForYouBooks = useCallback(async (forceRefresh = false) => {
    // Check cache
    if (!forceRefresh && forYouCacheRef.current.data) {
      const cacheAge = Date.now() - forYouCacheRef.current.timestamp;
      if (cacheAge < 5 * 60 * 1000) {
        setForYouBooks(forYouCacheRef.current.data);
        return;
      }
    }

    setLoading(prev => ({ ...prev, forYou: true }));
    setError(prev => ({ ...prev, forYou: '' }));

    try {
      const result = await fetchForYouBooks(8);
      if (result?.success) {
        const books = result.books || [];
        setForYouBooks(books);
        forYouCacheRef.current = { data: books, timestamp: Date.now() };
      } else {
        setError(prev => ({ ...prev, forYou: result?.error || 'Failed to load' }));
      }
    } catch (err) {
      setError(prev => ({ ...prev, forYou: 'Failed to load' }));
    } finally {
      setLoading(prev => ({ ...prev, forYou: false }));
    }
  }, []); // Empty deps - fetchForYouBooks is stable from context

  const loadPopularBooks = useCallback(async (forceRefresh = false) => {
    if (!forceRefresh && popularCacheRef.current.data) {
      const cacheAge = Date.now() - popularCacheRef.current.timestamp;
      if (cacheAge < 5 * 60 * 1000) {
        setPopularBooks(popularCacheRef.current.data);
        return;
      }
    }

    setLoading(prev => ({ ...prev, popular: true }));
    setError(prev => ({ ...prev, popular: '' }));

    try {
      const result = await fetchPopularBooks(8);
      if (result?.success) {
        const books = result.books || [];
        setPopularBooks(books);
        popularCacheRef.current = { data: books, timestamp: Date.now() };
      } else {
        setError(prev => ({ ...prev, popular: result?.error || 'Failed to load' }));
      }
    } catch (err) {
      setError(prev => ({ ...prev, popular: 'Failed to load' }));
    } finally {
      setLoading(prev => ({ ...prev, popular: false }));
    }
  }, []);

  const loadGenreBooks = useCallback(async (forceRefresh = false) => {
    if (!forceRefresh && genreCacheRef.current.data) {
      const cacheAge = Date.now() - genreCacheRef.current.timestamp;
      if (cacheAge < 5 * 60 * 1000) {
        setGenreBooks(genreCacheRef.current.data);
        return;
      }
    }

    setLoading(prev => ({ ...prev, genre: true }));
    setError(prev => ({ ...prev, genre: '' }));

    try {
      const result = await fetchGenreBooks(4);
      if (result?.success) {
        const books = result.books || [];
        setGenreBooks(books);
        genreCacheRef.current = { data: books, timestamp: Date.now() };
      } else {
        setError(prev => ({ ...prev, genre: result?.error || 'Failed to load' }));
      }
    } catch (err) {
      setError(prev => ({ ...prev, genre: 'Failed to load' }));
    } finally {
      setLoading(prev => ({ ...prev, genre: false }));
    }
  }, []);

  const loadSimilarBooks = useCallback(async (page = 1, forceRefresh = false) => {
    const cacheKey = `page-${page}`;
    const limit = 8;

    // Check cache
    if (!forceRefresh && similarCacheRef.current.pages[cacheKey]) {
      const cached = similarCacheRef.current.pages[cacheKey];
      const cacheAge = Date.now() - cached.timestamp;

      if (cacheAge < 5 * 60 * 1000) {
        console.log(`📦 Using cached similar books for page ${page}`);
        if (page === 1) {
          setSimilarBooks(cached.books);
        } else {
          setSimilarBooks(prev => [...prev, ...cached.books]);
        }
        setSimilarHasMore(cached.hasMore);
        setTotalSimilarBooks(cached.total || 0);
        return;
      }
    }

    if (page === 1) {
      setLoading(prev => ({ ...prev, similar: true }));
    } else {
      setLoading(prev => ({ ...prev, more: true }));
    }
    setError(prev => ({ ...prev, similar: '' }));

    try {
      console.log(`📡 Loading similar books - page ${page}, limit ${limit}`);
      const result = await fetchSimilarBooks(page, limit);

      if (result?.success) {
        const books = result.books || [];
        const hasMore = result.hasMore || false;
        const total = result.total || books.length;

        console.log(`✅ Loaded ${books.length} books for page ${page}, hasMore: ${hasMore}`);

        if (page === 1) {
          setSimilarBooks(books);
        } else {
          setSimilarBooks(prev => [...prev, ...books]);
        }

        setSimilarHasMore(hasMore);
        setSimilarPage(page);
        setTotalSimilarBooks(total);

        // Update cache
        similarCacheRef.current.pages[cacheKey] = {
          books,
          hasMore,
          total,
          timestamp: Date.now()
        };
      } else {
        setError(prev => ({ ...prev, similar: result?.error || 'Failed to load' }));
      }
    } catch (err) {
      console.error('Error loading similar books:', err);
      setError(prev => ({ ...prev, similar: 'Failed to load' }));
    } finally {
      setLoading(prev => ({ ...prev, similar: false, more: false }));
    }
  }, []);

  // ============ EFFECTS ============

  // Load data based on active filter
  useEffect(() => {
    // Skip initial mount if we already have data
    if (isInitialMount.current) {
      isInitialMount.current = false;

      // Only load if we have no data for the current filter
      if (activeFilter === 'for-you' && forYouBooks.length === 0) {
        loadForYouBooks();
      } else if (activeFilter === 'popular' && popularBooks.length === 0) {
        loadPopularBooks();
      } else if (activeFilter === 'genre' && genreBooks.length === 0) {
        loadGenreBooks();
      } else if (activeFilter === 'similar' && similarBooks.length === 0) {
        loadSimilarBooks(1);
      }
      return;
    }

    // For filter changes, always load
    if (activeFilter === 'for-you') {
      loadForYouBooks();
    } else if (activeFilter === 'popular') {
      loadPopularBooks();
    } else if (activeFilter === 'genre') {
      loadGenreBooks();
    } else if (activeFilter === 'similar') {
      setSimilarPage(1);
      setSimilarBooks([]);
      setSimilarHasMore(true);
      setTotalSimilarBooks(0);
      loadSimilarBooks(1);
    }
  }, [activeFilter]); // Only activeFilter triggers re-runs

  // ============ HANDLERS ============

  const handleLoadMore = async () => {
    if (loading.more || !similarHasMore) return;
    const nextPage = similarPage + 1;
    await loadSimilarBooks(nextPage);
  };

  const handleFilterChange = (filter) => {
    setActiveFilter(filter);
    setShowSearchResults(false);
    setSearchQuery('');
  };

  const handleBookClick = async (book) => {
    if (book?.book_id || book?.id) {
      await trackBook(book.book_id || book.id);
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
      book.title?.toLowerCase().includes(query) ||
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
    <div className="w-full space-y-6">
      {/* Header with Refresh */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-white">Recommendations</h1>
        <button
          onClick={refreshCurrentSection}
          className="px-3 py-1 bg-white/20 text-white rounded-lg hover:bg-white/30 transition"
          disabled={getCurrentLoading()}
        >
          {getCurrentLoading() ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {/* Search */}
      <div className="bg-white/80 rounded-xl p-4">
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={`Search in ${filterTitles[activeFilter]}...`}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={clearSearch}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            )}
          </div>
          <button
            type="submit"
            className="px-6 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition disabled:opacity-50"
            disabled={!searchQuery.trim()}
          >
            Search
          </button>
        </form>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap gap-2 border-b pb-4">
        {Object.entries(filterTitles).map(([key, title]) => (
          <button
            key={key}
            onClick={() => handleFilterChange(key)}
            className={`px-4 py-2 rounded-lg transition ${
              activeFilter === key
                ? 'bg-amber-600 text-white'
                : 'bg-white/20 text-white hover:bg-white/30'
            }`}
          >
            {title}
          </button>
        ))}
      </div>

      {/* Loading State */}
      {getCurrentLoading() && !showSearchResults && (
        <div className="flex justify-center items-center py-16">
          <div className="w-10 h-10 border-2 border-amber-200 border-t-amber-800 rounded-full animate-spin" />
        </div>
      )}

      {/* Error State */}
      {getCurrentError() && !showSearchResults && (
        <div className="text-center py-12 bg-white/20 rounded-xl">
          <p className="text-red-200">{getCurrentError()}</p>
          <button
            onClick={refreshCurrentSection}
            className="mt-4 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Search Results */}
      {showSearchResults ? (
        <section className="bg-white/80 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold">
              Search Results in {filterTitles[activeFilter]}
            </h2>
            <button
              onClick={clearSearch}
              className="text-sm text-amber-600 hover:text-amber-800"
            >
              Clear
            </button>
          </div>

          {filteredBooks.length > 0 ? (
            <>
              <p className="text-gray-600 mb-4">
                Found {filteredBooks.length} {filteredBooks.length === 1 ? 'book' : 'books'}
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {filteredBooks.map((book) => (
                  <div
                    key={book.book_id || book.id}
                    onClick={() => handleBookClick(book)}
                    className="cursor-pointer transition-transform hover:-translate-y-1"
                  >
                    <BookCard {...book} />
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="text-center py-8 text-gray-600">No books found</p>
          )}
        </section>
      ) : (
        /* Main Content */
        !getCurrentLoading() && !getCurrentError() && (
          <>
            {/* For You Section */}
            {activeFilter === 'for-you' && (
              <>
                {forYouBooks.length > 0 ? (
                  <section>
                    <h2 className="text-2xl font-bold text-white mb-4">For You</h2>
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                      {forYouBooks.map((book) => (
                        <div
                          key={book.book_id || book.id}
                          onClick={() => handleBookClick(book)}
                          className="cursor-pointer transition-transform hover:-translate-y-1"
                        >
                          <BookCard {...book} />
                        </div>
                      ))}
                    </div>
                  </section>
                ) : (
                  <div className="text-center py-12 bg-white/20 rounded-xl">
                    <p className="text-white/80">No personalized recommendations yet. Start exploring books!</p>
                  </div>
                )}
              </>
            )}

            {/* Popular Section */}
            {activeFilter === 'popular' && (
              <>
                {popularBooks.length > 0 ? (
                  <section>
                    <h2 className="text-2xl font-bold text-white mb-4">Popular Now</h2>
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                      {popularBooks.map((book) => (
                        <div
                          key={book.book_id || book.id}
                          onClick={() => handleBookClick(book)}
                          className="cursor-pointer transition-transform hover:-translate-y-1"
                        >
                          <BookCard {...book} />
                        </div>
                      ))}
                    </div>
                  </section>
                ) : (
                  <div className="text-center py-12 bg-white/20 rounded-xl">
                    <p className="text-white/80">No popular books found</p>
                  </div>
                )}
              </>
            )}

            {/* Genre Sections */}
            {activeFilter === 'genre' && (
              <>
                {genreBooks.length > 0 ? (
                  <div className="space-y-8">
                    {genreBooks.map((section) => (
                      <section key={section.genre}>
                        <h2 className="text-xl font-bold text-white mb-3">{section.genre}</h2>
                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                          {section.books?.map((book) => (
                            <div
                              key={book.book_id || book.id}
                              onClick={() => handleBookClick(book)}
                              className="cursor-pointer transition-transform hover:-translate-y-1"
                            >
                              <BookCard {...book} />
                            </div>
                          ))}
                        </div>
                      </section>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 bg-white/20 rounded-xl">
                    <p className="text-white/80">No genre books found</p>
                  </div>
                )}
              </>
            )}

            {/* Similar Section with Pagination */}
            {activeFilter === 'similar' && (
              <section>
                <h2 className="text-2xl font-bold text-white mb-4">Similar Suggestions</h2>

                {similarBooks.length > 0 ? (
                  <>
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                      {similarBooks.map((book) => (
                        <div
                          key={book.book_id || book.id}
                          onClick={() => handleBookClick(book)}
                          className="cursor-pointer transition-transform hover:-translate-y-1"
                        >
                          <BookCard {...book} />
                        </div>
                      ))}
                    </div>

                    {/* Load More Button */}
                    {similarHasMore && (
                      <div className="flex justify-center mt-8">
                        <button
                          onClick={handleLoadMore}
                          disabled={loading.more}
                          className="px-6 py-3 bg-white text-gray-700 rounded-lg shadow-sm hover:shadow-md transition-all duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                        >
                          {loading.more ? (
                            <span className="flex items-center gap-2">
                              <div className="w-4 h-4 border-2 border-amber-200 border-t-amber-800 rounded-full animate-spin" />
                              Loading...
                            </span>
                          ) : (
                            'Load More Books'
                          )}
                        </button>
                      </div>
                    )}

                    {/* End of list message */}
                    {!similarHasMore && similarBooks.length > 0 && (
                      <p className="text-center text-white/60 mt-6">
                        You've reached the end of the list ({similarBooks.length} books loaded)
                      </p>
                    )}
                  </>
                ) : (
                  <div className="text-center py-12 bg-white/20 rounded-xl">
                    <p className="text-white/80">No similar suggestions found</p>
                  </div>
                )}
              </section>
            )}
          </>
        )
      )}
    </div>
  );
}