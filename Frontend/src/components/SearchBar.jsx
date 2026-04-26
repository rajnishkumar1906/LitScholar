import React, { useState } from 'react';
import { FaSearch, FaMagic } from 'react-icons/fa';

function SearchBar({ onSearch }) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query);
    }
  };

  const suggestions = [
    { text: "Philosophical", emoji: "🤔", query: "Books that make me think about life" },
    { text: "Sci-Fi", emoji: "🚀", query: "Space adventure with real science" },
    { text: "Self-Help", emoji: "📚", query: "Books to build better habits" },
    { text: "Fantasy", emoji: "⚔️", query: "Epic fantasy with magic" },
    { text: "Mystery", emoji: "🔍", query: "Page-turning mystery" },
  ];

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Describe the book you're looking for..."
          className="w-full px-6 py-4 text-lg rounded-xl border border-gray-300 bg-white/80 backdrop-blur-sm text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-800 focus:border-transparent pr-36"
        />
        
        <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex gap-2">
          <button
            type="button"
            className="p-3 hover:bg-gray-100 rounded-xl text-amber-800 transition-colors"
            title="AI-powered search"
          >
            <FaMagic className="w-4 h-4" />
          </button>
          <button
            type="submit"
            className="px-6 py-2 bg-gradient-to-r from-amber-800 to-amber-900 text-white font-medium rounded-xl hover:shadow-lg transition-all duration-300 flex items-center gap-2"
          >
            <FaSearch className="h-4 w-4" />
            <span className="hidden sm:inline">Search</span>
          </button>
        </div>
      </div>

      {/* Quick Suggestions */}
      <div className="mt-4 flex flex-wrap gap-2">
        {suggestions.map((suggestion, index) => (
          <button
            key={index}
            type="button"
            onClick={() => {
              setQuery(suggestion.query);
              onSearch(suggestion.query);
            }}
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-full text-sm text-gray-700 transition-colors flex items-center gap-2"
          >
            <span>{suggestion.emoji}</span>
            <span className="hidden sm:inline">{suggestion.text}</span>
          </button>
        ))}
      </div>

      {/* Example query hint */}
      <p className="mt-3 text-xs text-gray-500">
        Try: "Books to build better habits" or "Space adventure with real science"
      </p>
    </form>
  );
}

export default SearchBar;