import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { useState, useEffect, useRef } from 'react';
import {
  FaArrowLeft, FaBook, FaRobot,
  FaQuestionCircle, FaSpinner, FaCheckCircle, FaComments,
  FaUserCircle, FaTrash, FaGamepad
} from 'react-icons/fa';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import BookDataCard from '../components/BookDataCard';
import { useApp } from '../context/AppContext';
import { toast } from 'react-toastify';

export default function BookDetail() {
  const { bookId } = useParams();  
  const location = useLocation();
  const navigate = useNavigate();
  const { 
    getBookById, 
    askFollowUp, 
    finishBook, 
    loadProfile, 
    fetchUserBooks,
    trackBook 
  } = useApp();

  const chatEndRef = useRef(null);
  const hasFetched = useRef(false);        // ← prevents double-fetch in StrictMode

  const [book, setBook] = useState(location.state?.book || null);
  const [loading, setLoading] = useState(!location.state?.book);
  const [showFollowUp, setShowFollowUp] = useState(false);
  const [followUpQuestion, setFollowUpQuestion] = useState('');
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState('');
  const [isFinishing, setIsFinishing] = useState(false);
  const [isFinished, setIsFinished] = useState(false);
  
  // Chat history
  const [chatHistory, setChatHistory] = useState([]);

  useEffect(() => {
    if (!bookId) return;

    // 1. Prevent duplicate fetch in StrictMode (development)
    if (hasFetched.current) return;
    hasFetched.current = true;

    const fetchBook = async () => {
      setLoading(true);
      setError('');

      // 2. Try to load from sessionStorage first (persists across refresh)
      const cacheKey = `book_${bookId}`;
      const cached = sessionStorage.getItem(cacheKey);
      if (cached) {
        try {
          const bookData = JSON.parse(cached);
          setBook(bookData);
          setLoading(false);
          // Still track the view (lightweight) and check finished status
          await trackBook(bookId);
          await checkIfFinished(bookId);
          setChatHistory([
            {
              id: 'welcome',
              type: 'ai',
              message: `Hello! I'm your AI Librarian. Ask me anything about "${bookData.title}" by ${bookData.author}. I can provide summaries, discuss themes, suggest similar books, and more!`,
              timestamp: new Date().toISOString()
            }
          ]);
          return; // ✅ Exit early – no API call
        } catch (e) {
          // If cache is corrupted, ignore and fetch fresh
          console.warn('Failed to parse cached book', e);
        }
      }

      // 3. No cache or invalid – fetch from API
      try {
        const result = await getBookById(bookId);
        if (result.success) {
          setBook(result.book);
          // Store in sessionStorage for future visits/refresh
          sessionStorage.setItem(cacheKey, JSON.stringify(result.book));
          await trackBook(bookId);
          await checkIfFinished(bookId);
          setChatHistory([
            {
              id: 'welcome',
              type: 'ai',
              message: `Hello! I'm your AI Librarian. Ask me anything about "${result.book.title}" by ${result.book.author}. I can provide summaries, discuss themes, suggest similar books, and more!`,
              timestamp: new Date().toISOString()
            }
          ]);
        } else {
          setError('Book not found');
          setTimeout(() => navigate('/dashboard'), 2000);
        }
      } catch (err) {
        setError('Failed to load book');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchBook();
  }, [bookId, getBookById, navigate, trackBook]);

  // Scroll to bottom of chat when new messages arrive
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatHistory]);

  // Check if book is already finished
  const checkIfFinished = async (id) => {
    try {
      const result = await fetchUserBooks('finished', 50);
      if (result.success) {
        const isBookFinished = result.books.some(b => 
          String(b.book_id) === String(id) || String(b.book_id) === String(id)
        );
        setIsFinished(isBookFinished);
      }
    } catch (error) {
      console.error('Error checking finished status:', error);
    }
  };

  const handleFollowUpSubmit = async (e) => {
    e.preventDefault();
    if (!followUpQuestion.trim() || !book || isAsking) return;

    const question = followUpQuestion.trim();
    
    // Add user question to chat
    const userMessage = {
      id: Date.now().toString(),
      type: 'user',
      message: question,
      timestamp: new Date().toISOString()
    };
    
    setChatHistory(prev => [...prev, userMessage]);
    setFollowUpQuestion('');
    setIsAsking(true);
    setError('');

    try {
      console.log('DEBUG: Sending question to AI:', question);
      const result = await askFollowUp(question, [book]);
      console.log('DEBUG: AI response received:', result);
      
      if (result.success) {
        // Map citations to the actual book objects for easier UI display
        const citedBooks = [];
        if (result.citations && Object.keys(result.citations).length > 0) {
          Object.values(result.citations).forEach(citedId => {
            const citedBook = result.books.find(b => String(b.id) === String(citedId));
            if (citedBook) citedBooks.push(citedBook);
          });
        }

        // Add AI response to chat
        const aiMessage = {
          id: (Date.now() + 1).toString(),
          type: 'ai',
          message: result.answer || "I found some information, but couldn't generate a specific answer.",
          citations: citedBooks.length > 0 ? citedBooks : (result.books || []),
          timestamp: new Date().toISOString()
        };
        setChatHistory(prev => [...prev, aiMessage]);
      } else {
        // Add error message
        const errorMessage = {
          id: (Date.now() + 1).toString(),
          type: 'error',
          message: result.error || 'Failed to get answer',
          timestamp: new Date().toISOString()
        };
        setChatHistory(prev => [...prev, errorMessage]);
      }
    } catch (err) {
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        type: 'error',
        message: 'An error occurred. Please try again.',
        timestamp: new Date().toISOString()
      };
      setChatHistory(prev => [...prev, errorMessage]);
    } finally {
      setIsAsking(false);
    }
  };

  const handleSuggestedQuestion = (question) => {
    setFollowUpQuestion(question);
    setTimeout(() => {
      document.querySelector('form').dispatchEvent(
        new Event('submit', { cancelable: true, bubbles: true })
      );
    }, 100);
  };

  const handleMarkAsFinished = async () => {
    if (!book || isFinished) return;
    
    setIsFinishing(true);
    try {
      const result = await finishBook(book.book_id || book.id);
      
      if (result.success) {
        setIsFinished(true);
        await loadProfile();
        toast.success('Book marked as finished! 🎉');
      } else {
        toast.error(result.error || 'Failed to mark book as finished');
      }
    } catch (error) {
      toast.error('An error occurred');
    } finally {
      setIsFinishing(false);
    }
  };

  const toggleFollowUp = () => {
    setShowFollowUp(!showFollowUp);
  };

  const clearChat = () => {
    if (chatHistory.length > 1) {
      // Keep only welcome message
      const welcomeMessage = chatHistory.find(msg => msg.id === 'welcome');
      setChatHistory(welcomeMessage ? [welcomeMessage] : []);
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex flex-col relative">
        <Navbar />
        <main className="flex-1 flex items-center justify-center px-4 sm:px-6 lg:px-8 py-8 w-full">
          <div className="bg-white/90 backdrop-blur-sm shadow-xl p-8 rounded-3xl border border-gray-200">
            <div className="w-16 h-16 border-4 border-amber-200 border-t-amber-800 rounded-full animate-spin"></div>
            <p className="mt-4 text-gray-600">Loading book details...</p>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  if (error || !book) {
    return (
      <div className="min-h-screen flex flex-col relative">
        <Navbar />
        <main className="flex-1 flex items-center justify-center px-4 sm:px-6 lg:px-8 py-8 w-full">
          <div className="bg-white/90 backdrop-blur-sm shadow-xl p-8 rounded-3xl border border-gray-200 text-center">
            <p className="text-red-600 mb-4">{error || 'Book not found'}</p>
            <button
              onClick={() => navigate('/dashboard')}
              className="px-6 py-2 bg-amber-800 text-white rounded-lg hover:bg-amber-900"
            >
              Go to Dashboard
            </button>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col relative">
      <Navbar />

      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        {/* Back button and action buttons row */}
        <div className="flex justify-between items-center mb-6">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 text-gray-700 hover:text-amber-800 transition-colors group bg-white/80 px-4 py-2 rounded-lg shadow-sm"
          >
            <FaArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
            Back to Dashboard
          </button>
          
          <div className="flex gap-3">
            {/* Take Quiz Button */}
            <button
              onClick={() => navigate(`/quiz/${bookId}`, { state: { book } })}
              className="px-6 py-3 rounded-xl font-medium flex items-center gap-2 bg-white text-amber-800 border border-amber-200 hover:bg-amber-50 transition-all shadow-sm"
            >
              <FaGamepad className="w-4 h-4" />
              Take Quiz
            </button>

            {/* Ask AI Button */}
            <button
              onClick={toggleFollowUp}
              className={`px-6 py-3 rounded-xl font-medium flex items-center gap-2 transition-all shadow-sm ${
                showFollowUp 
                  ? 'bg-amber-100 text-amber-800 border-2 border-amber-500'
                  : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
              }`}
            >
              <FaComments className="w-4 h-4" />
              {showFollowUp ? 'Hide AI Assistant' : 'Ask AI Assistant'}
            </button>

            {/* Mark as Finished Button */}
            <button
              onClick={handleMarkAsFinished}
              disabled={isFinishing || isFinished}
              className={`px-6 py-3 rounded-xl font-medium flex items-center gap-2 transition-all shadow-sm ${
                isFinished 
                  ? 'bg-green-100 text-green-700 border border-green-300 cursor-default'
                  : 'bg-gradient-to-r from-amber-600 to-amber-700 text-white hover:shadow-lg hover:from-amber-700 hover:to-amber-800'
              }`}
            >
              {isFinishing ? (
                <>
                  <FaSpinner className="w-4 h-4 animate-spin" />
                  <span>Marking...</span>
                </>
              ) : isFinished ? (
                <>
                  <FaCheckCircle className="w-4 h-4" />
                  <span>Finished!</span>
                </>
              ) : (
                <>
                  <FaCheckCircle className="w-4 h-4" />
                  <span>Mark as Finished</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Two Column Layout - Book on Left, Chat on Right */}
        <div className="flex gap-6">
          {/* Left Column - Book Details (60%) */}
          <div className={`transition-all duration-300 ${showFollowUp ? 'w-[60%]' : 'w-full'}`}>
            <BookDataCard
              book={book}
              showFollowUp={false}
              setShowFollowUp={() => {}}
            />
          </div>

          {/* Right Column - Chat History (40%) - Only visible when toggled */}
          {showFollowUp && (
            <div className="w-[40%] animate-slideIn">
              <div className="bg-white/10 backdrop-blur-sm rounded-3xl shadow-xl border border-gray-200 flex flex-col h-[calc(100vh-12rem)] sticky top-4">
                
                {/* Chat Header */}
                <div className="p-4 border-b border-gray-200 flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-gradient-to-r from-amber-600 to-amber-700 rounded-lg flex items-center justify-center">
                      <FaRobot className="w-4 h-4 text-white" />
                    </div>
                    <div>
                      <h2 className="text-lg font-semibold text-white">AI Librarian</h2>
                      <p className="text-xs text-white">Ask anything about this book</p>
                    </div>
                  </div>
                  {chatHistory.length > 1 && (
                    <button
                      onClick={clearChat}
                      className="text-gray-400 hover:text-red-500 transition-colors"
                      title="Clear chat"
                    >
                      <FaTrash className="w-4 h-4" />
                    </button>
                  )}
                </div>

                {/* Chat Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {chatHistory.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div className={`flex gap-2 max-w-[85%] ${msg.type === 'user' ? 'flex-row-reverse' : ''}`}>
                        {/* Avatar */}
                        <div className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${
                          msg.type === 'user' 
                            ? 'bg-amber-100' 
                            : msg.type === 'error'
                              ? 'bg-red-100'
                              : 'bg-amber-600'
                        }`}>
                          {msg.type === 'user' ? (
                            <FaUserCircle className="w-5 h-5 text-amber-700" />
                          ) : msg.type === 'error' ? (
                            <FaQuestionCircle className="w-4 h-4 text-red-600" />
                          ) : (
                            <FaRobot className="w-4 h-4 text-white" />
                          )}
                        </div>

                        {/* Message Bubble */}
                        <div>
                          <div className={`rounded-2xl px-4 py-2 ${
                            msg.type === 'user'
                              ? 'bg-amber-600 text-white rounded-tr-none'
                              : msg.type === 'error'
                                ? 'bg-red-50 text-red-700 border border-red-200'
                                : 'bg-gray-100 text-gray-800 rounded-tl-none'
                          }`}>
                            <p className="text-sm whitespace-pre-wrap">{msg.message}</p>
                            
                            {/* Citations */}
                            {msg.citations && msg.citations.length > 0 && (
                              <div className="mt-2 pt-2 border-t border-gray-300/30">
                                <p className="text-xs font-medium opacity-70 mb-1">Sources:</p>
                                <div className="flex flex-wrap gap-1">
                                  {msg.citations.map((citation, idx) => (
                                    <button
                                      key={idx}
                                      onClick={() => navigate(`/book/${citation.book_id}`)}
                                      className={`text-xs px-2 py-1 rounded flex items-center gap-1 ${
                                        msg.type === 'user'
                                          ? 'bg-amber-500 hover:bg-amber-400'
                                          : 'bg-white hover:bg-gray-200 border border-gray-300'
                                      } transition-colors`}
                                    >
                                      <FaBook className="w-2 h-2" />
                                      <span className="truncate max-w-[80px]">
                                        {citation.title || `Book ${idx + 1}`}
                                      </span>
                                    </button>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                          <p className="text-xs text-gray-400 mt-1 px-2">
                            {formatTime(msg.timestamp)}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  {/* Typing indicator */}
                  {isAsking && (
                    <div className="flex justify-start">
                      <div className="flex gap-2 max-w-[85%]">
                        <div className="flex-shrink-0 w-6 h-6 bg-amber-600 rounded-full flex items-center justify-center">
                          <FaRobot className="w-4 h-4 text-white" />
                        </div>
                        <div className="bg-gray-100 rounded-2xl rounded-tl-none px-4 py-3">
                          <div className="flex gap-1">
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  <div ref={chatEndRef} />
                </div>

                {/* Input Area */}
                <div className="p-4 border-t border-gray-200">
                  <form onSubmit={handleFollowUpSubmit} className="space-y-2">
                    <textarea
                      value={followUpQuestion}
                      onChange={(e) => setFollowUpQuestion(e.target.value)}
                      placeholder="Ask a question..."
                      className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white/80 focus:outline-none focus:ring-2 focus:ring-amber-600 min-h-[60px]"
                      disabled={isAsking}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          handleFollowUpSubmit(e);
                        }
                      }}
                    />
                    
                    {/* Suggested quick questions */}
                    <div className="flex flex-wrap gap-1">
                      {[
                        "Summary",
                        "Similar books",
                        "Author",
                        "Themes",
                        "Review"
                      ].map((q, i) => (
                        <button
                          key={i}
                          type="button"
                          onClick={() => handleSuggestedQuestion(q)}
                          disabled={isAsking}
                          className="px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded-full text-xs text-gray-700 transition-colors disabled:opacity-50"
                        >
                          {q}
                        </button>
                      ))}
                    </div>

                    <button
                      type="submit"
                      disabled={isAsking || !followUpQuestion.trim()}
                      className="w-full px-3 py-2 bg-gradient-to-r from-amber-600 to-amber-700 text-white text-sm font-medium rounded-lg hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      {isAsking ? (
                        <>
                          <FaSpinner className="w-3 h-3 animate-spin" />
                          <span>Thinking...</span>
                        </>
                      ) : (
                        'Send Message'
                      )}
                    </button>
                  </form>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* You might also like section */}
        <div className="mt-12">
          <h2 className="text-3xl font-bold text-white mb-6">You might also like</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div
                key={i}
                className="bg-white/95 backdrop-blur-sm rounded-xl shadow-md border border-gray-200 p-4 hover:shadow-xl transition-all cursor-pointer transform hover:-translate-y-1"
                onClick={() => {
                  toast.info('Full recommendations coming soon!');
                }}
              >
                <div className="bg-amber-100 rounded-lg h-24 mb-3 flex items-center justify-center">
                  <FaBook className="w-8 h-8 text-amber-800/30" />
                </div>
                <h3 className="font-medium text-gray-900">Another Great Book</h3>
                <p className="text-xs text-gray-500">By Popular Author</p>
              </div>
            ))}
          </div>
        </div>
      </main>

      <Footer />

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes slideIn {
          from { opacity: 0; transform: translateX(20px); }
          to { opacity: 1; transform: translateX(0); }
        }
        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out;
        }
        .animate-slideIn {
          animation: slideIn 0.3s ease-out;
        }
      `}</style>
    </div>
  );
}