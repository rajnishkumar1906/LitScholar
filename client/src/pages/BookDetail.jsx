import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { useState, useEffect } from 'react';
import {
  FaArrowLeft, FaBook, FaUser, FaLayerGroup, FaFileAlt,
  FaCalendar, FaBuilding, FaBarcode, FaStar, FaRobot,
  FaQuestionCircle, FaSpinner, FaCheckCircle
} from 'react-icons/fa';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import NotFound from './NotFound';
import BookDataCard from '../components/BookDataCard';
import { useApp } from '../context/AppContext';
import { toast } from 'react-toastify';

export default function BookDetail() {
  const { bookId } = useParams();  
  const location = useLocation();
  const navigate = useNavigate();
  const { getBookById, askFollowUp, finishBook, loadProfile } = useApp();

  const [book, setBook] = useState(location.state?.book || null);
  const [loading, setLoading] = useState(!location.state?.book);
  const [showFollowUp, setShowFollowUp] = useState(false);
  const [followUpQuestion, setFollowUpQuestion] = useState('');
  const [followUpAnswer, setFollowUpAnswer] = useState('');
  const [isAsking, setIsAsking] = useState(false);
  const [citations, setCitations] = useState({});
  const [isFinishing, setIsFinishing] = useState(false);
  const [isFinished, setIsFinished] = useState(false);

  useEffect(() => {
    if (!bookId) return;

    const fetchBook = async () => {
      setLoading(true);
      const result = await getBookById(bookId);
      if (result.success) {
        setBook(result.book);
        // Check if already finished (you'd need an endpoint for this)
        checkIfFinished(bookId);
      } else if (!book) {
        navigate('/dashboard');
      }
      setLoading(false);
    };

    fetchBook();
  }, [bookId, getBookById, navigate]);

  // Add function to check if book is already finished
  const checkIfFinished = async (bookId) => {
    try {
      // You'd need an endpoint to check this
      // For now, we'll just set to false
      setIsFinished(false);
    } catch (error) {
      console.error('Error checking finished status:', error);
    }
  };

  const handleFollowUpSubmit = async (e) => {
    e.preventDefault();
    if (!followUpQuestion.trim() || !book) return;

    setIsAsking(true);
    setFollowUpAnswer('');
    setCitations({});

    const result = await askFollowUp(followUpQuestion, [book]);
    if (result.success) {
      setFollowUpAnswer(result.answer);
      setCitations(result.citations || {});
    } else {
      setFollowUpAnswer('Sorry, I encountered an error. Please try again.');
    }
    setIsAsking(false);
  };

  const handleSuggestedQuestion = (question) => {
    setFollowUpQuestion(question);
    setTimeout(() => {
      handleFollowUpSubmit({ preventDefault: () => {} });
    }, 100);
  };

  const handleMarkAsFinished = async () => {
    if (!book) return;
    
    setIsFinishing(true);
    const result = await finishBook(book.book_id || book.id);
    
    if (result.success) {
      setIsFinished(true);
      // Refresh profile to update reading goal
      await loadProfile();
    }
    
    setIsFinishing(false);
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="bg-white/95 backdrop-blur-sm shadow-xl p-8 rounded-3xl border border-gray-200">
          <div className="w-16 h-16 border-4 border-amber-200 border-t-amber-800 rounded-full animate-spin"></div>
        </div>
      </div>
    );
  }

  if (!book) {
    return <NotFound />;
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-6xl mx-auto px-4 py-8 w-full">
        {/* Back button and finish button row */}
        <div className="flex justify-between items-center mb-6">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 text-white text-2xl font-bold hover:text-amber-800 transition-colors group"
          >
            <FaArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
            Back
          </button>
          
          {/* Mark as Finished Button */}
          <button
            onClick={handleMarkAsFinished}
            disabled={isFinishing || isFinished}
            className={`px-6 py-3 rounded-xl font-medium flex items-center gap-2 transition-all ${
              isFinished 
                ? 'bg-green-100 text-green-700 border border-green-300 cursor-default'
                : 'bg-gradient-to-r from-amber-800 to-amber-900 text-white hover:shadow-lg'
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

        {/* Book details */}
        <BookDataCard
          book={book}
          showFollowUp={showFollowUp}
          setShowFollowUp={setShowFollowUp}
        />

        {/* Follow-up Questions Section */}
        {showFollowUp && (
          <div className="bg-white/95 backdrop-blur-sm rounded-3xl shadow-xl border border-gray-200 p-8 mb-8 animate-fadeIn">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-gradient-to-r from-amber-800 to-amber-900 rounded-xl flex items-center justify-center">
                <FaQuestionCircle className="w-5 h-5 text-white" />
              </div>
              <h2 className="text-2xl font-semibold text-gray-800">Ask a follow-up question</h2>
            </div>

            <form onSubmit={handleFollowUpSubmit} className="mb-6">
              <div className="flex gap-3">
                <input
                  type="text"
                  value={followUpQuestion}
                  onChange={(e) => setFollowUpQuestion(e.target.value)}
                  placeholder="e.g., Tell me more about this book, Similar recommendations, About the author..."
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-xl bg-white/80 focus:outline-none focus:ring-2 focus:ring-amber-800"
                  disabled={isAsking}
                />
                <button
                  type="submit"
                  disabled={isAsking || !followUpQuestion.trim()}
                  className="px-6 py-3 bg-gradient-to-r from-amber-800 to-amber-900 text-white font-medium rounded-xl hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {isAsking ? (
                    <>
                      <FaSpinner className="w-4 h-4 animate-spin" />
                      <span>Asking...</span>
                    </>
                  ) : (
                    'Ask'
                  )}
                </button>
              </div>
            </form>

            {/* Suggested questions */}
            <div className="mb-6">
              <p className="text-sm text-gray-500 mb-2">Suggested questions:</p>
              <div className="flex flex-wrap gap-2">
                {[
                  "What's a summary of this book?",
                  "Similar books to this?",
                  "Tell me about the author",
                  "Is this book worth reading?"
                ].map((q, i) => (
                  <button
                    key={i}
                    onClick={() => handleSuggestedQuestion(q)}
                    disabled={isAsking}
                    className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded-full text-xs text-gray-700 transition-colors disabled:opacity-50"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>

            {/* Answer */}
            {followUpAnswer && (
              <div className="bg-amber-50 rounded-2xl p-6 border border-amber-200">
                <div className="flex gap-3">
                  <div className="w-8 h-8 bg-gradient-to-r from-amber-800 to-amber-900 rounded-lg flex items-center justify-center flex-shrink-0">
                    <FaRobot className="w-4 h-4 text-white" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-gray-800 leading-relaxed">{followUpAnswer}</p>

                    {/* Citations */}
                    {Object.keys(citations).length > 0 && (
                      <div className="mt-3 pt-3 border-t border-amber-200">
                        <p className="text-xs font-medium text-amber-800 mb-1">Sources:</p>
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(citations).map(([ref, id]) => (
                            <button
                              key={ref}
                              onClick={() => navigate(`/book/${id}`)}
                              className="text-xs bg-white px-2 py-1 rounded border border-amber-200 hover:bg-amber-100 transition-colors"
                            >
                              {ref}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    <p className="text-xs text-gray-500 mt-2">AI Librarian • Just now</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* You might also like section */}
        <div className="mt-12">
          <h2 className="text-4xl font-bold text-white mb-6"><u>You might also like</u></h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="bg-white/95 backdrop-blur-sm rounded-xl shadow-md border border-gray-200 p-4 hover:shadow-xl transition-all cursor-pointer transform hover:-translate-y-1"
                onClick={() => navigate('/book/1')}
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
        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out;
        }
      `}</style>
    </div>
  );
}