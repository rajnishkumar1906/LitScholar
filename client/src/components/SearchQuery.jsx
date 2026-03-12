import { useState } from 'react';
import SearchBar from '../components/SearchBar';
import { useApp } from '../context/AppContext';

// Tiny Book Tile for search results (even smaller, no image)
function TinyBookTile({ book, onClick }) {
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
      className="group cursor-pointer bg-white/90 rounded-lg shadow hover:shadow-md transition-all duration-300 overflow-hidden"
    >
      <div className="p-2">
        <h3 className="font-bold text-gray-800 text-xs mb-0.5 line-clamp-1 group-hover:text-amber-700 transition">
          {book.title}
        </h3>
        <p className="text-[10px] text-gray-600 mb-1 truncate">{book.author}</p>
        <span className="text-[8px] px-1.5 py-0.5 bg-amber-100 text-amber-800 rounded-full font-medium">
          {getGenreDisplay()}
        </span>
      </div>
    </div>
  );
}

export default function SearchQuery({ onBookClick }) {
  const { 
    searchBooks, 
    searchResults, 
    isSearching, 
    lastQuery 
  } = useApp();
  
  const [searchError, setSearchError] = useState('');

  const handleSearch = async (query) => {
    const trimmedQuery = query.trim();
    if (!trimmedQuery) return;

    setSearchError('');
    const result = await searchBooks(trimmedQuery, 12);
    if (!result.success) {
      setSearchError(result.error || 'Something went wrong. Please try again.');
    }
  };

  const results = searchResults || [];
  const aiAnswer = results.length > 0 ? results[0]?.answer : null;
  const hasSearched = !!lastQuery;

  return (
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
            <h2 className="text-2xl font-bold text-white">Search Results</h2>
            <span className="px-3 py-1 bg-amber-50 text-amber-800 rounded-full text-sm">
              {results.length} books
            </span>
          </div>

          {aiAnswer && (
            <div className="mb-6 p-4 bg-amber-50 rounded-lg border border-amber-200">
              <p className="text-gray-800">{aiAnswer}</p>
            </div>
          )}

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {results.map((book) => (
              <TinyBookTile
                key={book.id || book.book_id}
                book={book}
                onClick={onBookClick}
              />
            ))}
          </div>
        </section>
      ) : hasSearched ? (
        <div className="text-center py-12 bg-white/70 backdrop-blur-md rounded-xl">
          <p className="text-gray-700">No books found. Try a different search term.</p>
        </div>
      ) : null}
    </div>
  );
}