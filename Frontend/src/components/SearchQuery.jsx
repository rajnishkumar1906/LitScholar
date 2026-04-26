import { useState } from 'react';
import SearchBar from '../components/SearchBar';
import { useApp } from '../context/AppContext';

// Tiny Book Tile for search results (more transparent, slightly bigger)
function TinyBookTile({ book, onClick }) {
  // Helper to parse genres into a clean array
  const getGenresArray = (genres) => {
    if (!genres) return ['General'];
    if (Array.isArray(genres)) return genres;
    if (typeof genres === 'string') {
      try {
        // Handle stringified arrays like "['A', 'B']"
        const parsed = JSON.parse(genres.replace(/'/g, '"'));
        return Array.isArray(parsed) ? parsed : [genres];
      } catch (e) {
        // Handle comma separated strings
        return genres.split(',').map(g => g.trim());
      }
    }
    return ['General'];
  };

  const genres = getGenresArray(book.genres);

  return (
    <div
      onClick={() => onClick(book)}
      className="group cursor-pointer bg-white/10 backdrop-blur-xl rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-500 overflow-hidden border border-white/20 hover:bg-white/30 transform hover:-translate-y-1 active:scale-95"
    >
      <div className="p-5 flex flex-col h-full min-h-[160px] justify-between">
        <div>
          <h3 className="font-black text-amber-950 text-base mb-1.5 line-clamp-2 group-hover:text-amber-800 transition-colors leading-tight drop-shadow-sm">
            {book.title}
          </h3>
          <p className="text-sm text-amber-900/80 mb-3 truncate font-semibold">by {book.author}</p>
        </div>
        
        <div className="mt-auto">
          {/* Genre Badges - Individual items instead of a list string */}
          <div className="flex flex-wrap gap-1.5 mb-4">
            {genres.slice(0, 3).map((genre, i) => (
              <span 
                key={i} 
                className="text-[9px] px-2 py-0.5 bg-amber-800/10 text-amber-900 rounded-full font-black border border-amber-800/20 backdrop-blur-md uppercase tracking-wider"
              >
                {genre}
              </span>
            ))}
            {genres.length > 3 && (
              <span className="text-[9px] px-2 py-0.5 bg-white/10 text-amber-900/60 rounded-full font-bold border border-white/20">
                +{genres.length - 3}
              </span>
            )}
          </div>

          <div className="flex items-center justify-between pt-3 border-t border-amber-900/10">
            <span className="text-[10px] font-black text-amber-900/40 uppercase tracking-widest">
              View Details
            </span>
            <div className="w-8 h-8 rounded-xl bg-amber-900/10 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-300">
              <span className="text-amber-900 text-sm">→</span>
            </div>
          </div>
        </div>
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
        <section className="bg-white/10 backdrop-blur-xl rounded-[2.5rem] p-8 shadow-2xl border border-white/20">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h2 className="text-3xl font-black text-white drop-shadow-md">Search Results</h2>
              <p className="text-amber-200 text-sm font-medium mt-1">Based on your query "{lastQuery}"</p>
            </div>
            <span className="px-4 py-1.5 bg-amber-800/80 backdrop-blur-md text-white rounded-full text-xs font-black border border-white/20 uppercase tracking-widest shadow-lg">
              {results.length} Results
            </span>
          </div>

          {aiAnswer && (
            <div className="mb-8 p-6 bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 shadow-inner">
              <p className="text-amber-100 text-lg leading-relaxed italic">"{aiAnswer}"</p>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
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