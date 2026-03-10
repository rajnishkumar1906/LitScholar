import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import SearchBar from '../components/SearchBar';
import BookCard from '../components/BookCard';
import { useApp } from '../context/AppContext';
import ToggleButton from '../components/ToggleButton';
import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline';

function BookTile({ book, onClick }) {
  const getGenreDisplay = () => {
    if (book.genres) {
      if (typeof book.genres === 'string') {
        const genreList = book.genres.split(',').map(g => g.trim());
        return genreList.length > 0 ? genreList[0] : 'General';
      }
      if (Array.isArray(book.genres) && book.genres.length > 0) {
        return book.genres[0];
      }
    }
    return book.genre || book.category || 'General';
  };

  return (
    <div
      onClick={() => onClick(book)}
      className="group cursor-pointer flex-shrink-0 w-[150px] sm:w-[180px]"
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
            {getGenreDisplay()}
          </span>
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const { 
    searchBooks, 
    searchResults, 
    isSearching, 
    lastQuery, 
    fetchRecommendedSections, 
    fetchRecommendedBooks,
    trackBook,
    user 
  } = useApp();
  
  const [searchError, setSearchError] = useState('');
  const [showSearchSection, setShowSearchSection] = useState(false);
  const [isRotating, setIsRotating] = useState(false);
  const [activeFilter, setActiveFilter] = useState('for-you');
  
  // Sections state
  const [sections, setSections] = useState({ for_you: [], popular: [], by_genre: [] });
  const [loadingSections, setLoadingSections] = useState(true);
  const [sectionError, setSectionError] = useState('');
  
  // Paginated recommendations state
  const [recommendedBooks, setRecommendedBooks] = useState([]);
  const [loadingMore, setLoadingMore] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [recommendedError, setRecommendedError] = useState('');

  // Search within recommendations state
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchingRecs, setIsSearchingRecs] = useState(false);
  const [filteredBooks, setFilteredBooks] = useState([]);
  const [showSearchResults, setShowSearchResults] = useState(false);

  // Load sections on mount
  useEffect(() => {
    const loadSections = async () => {
      setLoadingSections(true);
      setSectionError('');
      
      try {
        const result = await fetchRecommendedSections();
        console.log("📥 Sections loaded:", result);
        
        if (result?.success) {
          setSections({
            for_you: result.for_you || [],
            popular: result.popular || [],
            by_genre: result.by_genre || [],
          });
        } else {
          setSectionError(result?.error || 'Failed to load recommendations');
        }
      } catch (error) {
        console.error("Error loading sections:", error);
        setSectionError('Failed to load recommendations');
      } finally {
        setLoadingSections(false);
      }
    };

    loadSections();
  }, [fetchRecommendedSections, user?.id]);

  // Load paginated recommendations
  useEffect(() => {
    const loadRecommendations = async () => {
      if (showSearchSection) return;
      
      setLoadingMore(true);
      setRecommendedError('');
      
      try {
        const result = await fetchRecommendedBooks(currentPage, 8);
        console.log(`📥 Page ${currentPage} loaded:`, result);
        
        if (result?.success) {
          if (currentPage === 1) {
            setRecommendedBooks(result.books || []);
          } else {
            setRecommendedBooks(prev => [...prev, ...(result.books || [])]);
          }
          setHasMore(result.hasMore || false);
        } else {
          setRecommendedError(result?.error || 'Failed to load recommendations');
        }
      } catch (error) {
        console.error("Error loading recommendations:", error);
        setRecommendedError('Failed to load recommendations');
      } finally {
        setLoadingMore(false);
      }
    };

    loadRecommendations();
  }, [fetchRecommendedBooks, user?.id, showSearchSection, currentPage]);

  const handleLoadMore = () => {
    if (loadingMore || !hasMore) return;
    setCurrentPage(prev => prev + 1);
  };

  const handleFilterChange = (filter) => {
    setActiveFilter(filter);
    setShowSearchResults(false);
    setSearchQuery('');
  };

  const handleRecommendationSearch = (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setShowSearchResults(false);
      setFilteredBooks([]);
      return;
    }

    setIsSearchingRecs(true);
    
    // Get books based on active filter
    let booksToSearch = [];
    if (activeFilter === 'for-you') {
      booksToSearch = sections.for_you || [];
    } else if (activeFilter === 'popular') {
      booksToSearch = sections.popular || [];
    } else if (activeFilter === 'genre') {
      booksToSearch = sections.by_genre.flatMap(g => g.books || []);
    } else if (activeFilter === 'similar') {
      booksToSearch = recommendedBooks;
    }

    // Filter by search query
    const query = searchQuery.toLowerCase().trim();
    const filtered = booksToSearch.filter(book => {
      const titleMatch = book.title?.toLowerCase().includes(query);
      const authorMatch = book.author?.toLowerCase().includes(query);
      
      let genreMatch = false;
      if (book.genres) {
        if (typeof book.genres === 'string') {
          genreMatch = book.genres.toLowerCase().includes(query);
        } else if (Array.isArray(book.genres)) {
          genreMatch = book.genres.some(g => g.toLowerCase().includes(query));
        }
      }
      
      return titleMatch || authorMatch || genreMatch;
    });

    setFilteredBooks(filtered);
    setShowSearchResults(true);
    setIsSearchingRecs(false);
  };

  const clearSearch = () => {
    setSearchQuery('');
    setShowSearchResults(false);
    setFilteredBooks([]);
  };

  const handleSearch = async (query) => {
    const trimmedQuery = query.trim();
    if (!trimmedQuery) return;

    setSearchError('');
    const result = await searchBooks(trimmedQuery, 6);
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

  const results = searchResults || [];
  const aiAnswer = results.length > 0 ? results[0]?.answer : null;
  const hasSearched = !!lastQuery;

  const filterTitles = {
    'for-you': 'For You',
    'popular': 'Popular',
    'genre': 'By Genre',
    'similar': 'Similar'
  };

  // Get current books based on filter
  const getCurrentBooks = () => {
    if (activeFilter === 'for-you') return sections.for_you;
    if (activeFilter === 'popular') return sections.popular;
    if (activeFilter === 'genre') return sections.by_genre;
    if (activeFilter === 'similar') return recommendedBooks;
    return [];
  };

  const currentBooks = getCurrentBooks();

  return (
    <div className="min-h-screen flex flex-col relative">
      <Navbar />

      <main className="flex-grow max-w-8xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        {/* Main Content */}
        {!showSearchSection ? (
          <div className="w-full animate-fadeIn space-y-6">
            {/* Search Bar */}
            <div className="bg-white/80 backdrop-blur-md rounded-xl shadow-lg p-4 border border-amber-100">
              <form onSubmit={handleRecommendationSearch} className="flex gap-2">
                <div className="relative flex-1">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search by title, author, or genre..."
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent bg-white/90"
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
                  disabled={isSearchingRecs}
                  className="px-6 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition disabled:opacity-50 flex items-center gap-2"
                >
                  <MagnifyingGlassIcon className="h-5 w-5" />
                  Search
                </button>
              </form>
            </div>

            {/* Filter Tabs */}
            <div className="flex flex-wrap gap-2 border-b border-white/20 pb-4">
              {Object.entries(filterTitles).map(([key, title]) => (
                <button
                  key={key}
                  onClick={() => handleFilterChange(key)}
                  className={`px-4 py-2 rounded-lg transition-all ${
                    activeFilter === key
                      ? 'bg-amber-600 text-white shadow-lg'
                      : 'bg-white/20 text-white hover:bg-white/30 backdrop-blur-sm'
                  }`}
                >
                  {title}
                </button>
              ))}
            </div>

            {loadingSections && activeFilter !== 'similar' ? (
              <div className="flex justify-center items-center py-16">
                <div className="w-10 h-10 border-2 border-amber-200 border-t-amber-800 rounded-full animate-spin" />
              </div>
            ) : showSearchResults ? (
              // Search Results
              <section className="bg-white/80 backdrop-blur-md rounded-xl p-6 shadow-lg border border-amber-100">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-2xl font-bold text-white">
                    Search Results
                  </h2>
                  <button
                    onClick={clearSearch}
                    className="text-sm text-amber-200 hover:text-amber-100"
                  >
                    Clear
                  </button>
                </div>
                
                {filteredBooks.length > 0 ? (
                  <>
                    <p className="text-white/80 mb-4">
                      Found {filteredBooks.length} {filteredBooks.length === 1 ? 'book' : 'books'}
                    </p>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
                      {filteredBooks.map((book) => (
                        <BookTile 
                          key={book.book_id || book.id} 
                          book={book} 
                          onClick={handleBookClick} 
                        />
                      ))}
                    </div>
                  </>
                ) : (
                  <p className="text-white/80 text-center py-8">No books found</p>
                )}
              </section>
            ) : (
              <>
                {/* For You Section */}
                {activeFilter === 'for-you' && (
                  <>
                    {sections.for_you.length > 0 ? (
                      <section>
                        <h2 className="text-2xl font-bold text-white mb-4">For You</h2>
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
                          {sections.for_you.map((book) => (
                            <BookTile key={book.book_id || book.id} book={book} onClick={handleBookClick} />
                          ))}
                        </div>
                      </section>
                    ) : (
                      <div className="text-center py-12 bg-white/20 backdrop-blur-sm rounded-xl">
                        <p className="text-white/80">No personalized recommendations yet. Start exploring books!</p>
                      </div>
                    )}
                  </>
                )}

                {/* Popular Section */}
                {activeFilter === 'popular' && (
                  <>
                    {sections.popular.length > 0 ? (
                      <section>
                        <h2 className="text-2xl font-bold text-white mb-4">Popular Now</h2>
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
                          {sections.popular.map((book) => (
                            <BookTile key={book.book_id || book.id} book={book} onClick={handleBookClick} />
                          ))}
                        </div>
                      </section>
                    ) : (
                      <div className="text-center py-12 bg-white/20 backdrop-blur-sm rounded-xl">
                        <p className="text-white/80">No popular books found</p>
                      </div>
                    )}
                  </>
                )}

                {/* Genre Sections */}
                {activeFilter === 'genre' && (
                  <>
                    {sections.by_genre.length > 0 ? (
                      <div className="space-y-8">
                        {sections.by_genre.map(({ genre, books }) => (
                          <section key={genre}>
                            <h2 className="text-xl font-bold text-white mb-3">{genre}</h2>
                            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                              {books.map((book) => (
                                <BookTile key={book.book_id || book.id} book={book} onClick={handleBookClick} />
                              ))}
                            </div>
                          </section>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-12 bg-white/20 backdrop-blur-sm rounded-xl">
                        <p className="text-white/80">No genre books found</p>
                      </div>
                    )}
                  </>
                )}

                {/* Similar Suggestions with Pagination */}
                {activeFilter === 'similar' && (
                  <section>
                    <h2 className="text-2xl font-bold text-white mb-4">Similar Suggestions</h2>
                    
                    {loadingMore && currentPage === 1 ? (
                      <div className="flex justify-center py-8">
                        <div className="w-8 h-8 border-2 border-amber-200 border-t-amber-800 rounded-full animate-spin" />
                      </div>
                    ) : (
                      <>
                        {recommendedBooks.length > 0 ? (
                          <>
                            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
                              {recommendedBooks.map((book) => (
                                <BookTile key={book.book_id || book.id} book={book} onClick={handleBookClick} />
                              ))}
                            </div>

                            {hasMore && (
                              <div className="flex justify-center mt-8">
                                <button
                                  onClick={handleLoadMore}
                                  disabled={loadingMore}
                                  className="px-6 py-3 bg-white/80 backdrop-blur-sm border border-amber-200 rounded-lg shadow-sm hover:shadow-md transition-all duration-200 text-gray-700 font-medium disabled:opacity-50"
                                >
                                  {loadingMore ? (
                                    <span className="flex items-center gap-2">
                                      <div className="w-4 h-4 border-2 border-amber-200 border-t-amber-800 rounded-full animate-spin" />
                                      Loading...
                                    </span>
                                  ) : (
                                    'Load More'
                                  )}
                                </button>
                              </div>
                            )}
                          </>
                        ) : (
                          <div className="text-center py-12 bg-white/20 backdrop-blur-sm rounded-xl">
                            <p className="text-white/80">No similar suggestions found</p>
                          </div>
                        )}
                      </>
                    )}

                    {recommendedError && (
                      <p className="text-red-200 text-sm mt-4 text-center">{recommendedError}</p>
                    )}
                  </section>
                )}
              </>
            )}
          </div>
        ) : (
          // Search Section with AI
          <div className="w-full max-w-7xl mx-auto animate-fadeIn">
            <div className="text-center mb-8">
              <h1 className="text-4xl md:text-5xl font-extrabold mb-4 tracking-tight">
                <span className="text-gray-900">Find Your</span>
                <br />
                <span className="bg-gradient-to-r from-amber-700 via-amber-100 to-amber-900 bg-clip-text text-transparent">
                  Next Great Read
                </span>
              </h1>
            </div>

            <div className="mb-6">
              <div className="bg-white/90 backdrop-blur-lg shadow-xl rounded-2xl p-6 border border-amber-100">
                <SearchBar onSearch={handleSearch} />
              </div>
            </div>

            <div className="flex flex-wrap justify-center gap-3 mb-8">
              {['Philosophical', 'Sci-Fi', 'Self-Help', 'Fantasy', 'Mystery'].map((cat) => (
                <button
                  key={cat}
                  onClick={() => handleSearch(cat)}
                  className="px-4 py-2 bg-white/80 backdrop-blur-sm shadow-md hover:shadow-lg rounded-full text-gray-700 transition-all border border-amber-200 hover:border-amber-400"
                >
                  {cat}
                </button>
              ))}
            </div>

            {searchError && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl">
                {searchError}
              </div>
            )}

            {isSearching ? (
              <div className="flex justify-center py-16">
                <div className="w-12 h-12 border-4 border-amber-200 border-t-amber-800 rounded-full animate-spin" />
              </div>
            ) : results.length > 0 ? (
              <section className="bg-white/80 backdrop-blur-md rounded-xl p-6 shadow-lg">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-2xl font-bold text-white">Results</h2>
                  <span className="px-3 py-1 bg-amber-50 text-amber-800 rounded-full text-sm">
                    {results.length} books
                  </span>
                </div>

                {aiAnswer && (
                  <div className="mb-6 p-4 bg-amber-50 rounded-lg border border-amber-200">
                    <p className="text-gray-800">{aiAnswer}</p>
                  </div>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {results.map((book) => (
                    <div
                      key={book.id}
                      onClick={() => handleBookClick(book)}
                      className="cursor-pointer transition-transform hover:-translate-y-1"
                    >
                      <BookCard {...book} />
                    </div>
                  ))}
                </div>
              </section>
            ) : hasSearched ? (
              <div className="text-center py-12 bg-white/70 backdrop-blur-md rounded-xl">
                <p className="text-gray-700">No books found</p>
              </div>
            ) : null}
          </div>
        )}
      </main>

      <ToggleButton
        showSearchSection={showSearchSection}
        onToggle={handleToggle}
        isRotating={isRotating}
      />

      <Footer />
    </div>
  );
}