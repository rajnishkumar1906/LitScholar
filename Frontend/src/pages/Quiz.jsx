// src/pages/Quiz.jsx
import { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { FaArrowLeft, FaCheckCircle, FaTimesCircle, FaTrophy, FaRedo, FaHome } from 'react-icons/fa';
import { useApp } from '../context/AppContext';
import LitScholarLogo from '../components/LitScholarLogo';
import { toast } from 'react-toastify';

export default function Quiz() {
  const { bookId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { generateQuiz, saveQuizScore } = useApp();
  
  const book = location.state?.book;
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentStep, setCurrentStep] = useState('taking'); // 'taking', 'submitting', 'result'
  const [userAnswers, setUserAnswers] = useState({});
  const [score, setScore] = useState(0);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    if (!book) {
      navigate(`/book/${bookId}`);
      return;
    }

    const fetchQuiz = async () => {
      setLoading(true);
      try {
        const result = await generateQuiz(book.title, book.author);
        if (result.success && result.data.quiz) {
          setQuestions(result.data.quiz);
        } else {
          toast.error("Failed to generate quiz. Please try again.");
          navigate(`/book/${bookId}`);
        }
      } catch (err) {
        console.error(err);
        toast.error("An error occurred while generating the quiz.");
        navigate(`/book/${bookId}`);
      } finally {
        setLoading(false);
      }
    };

    fetchQuiz();
  }, [bookId, book, generateQuiz, navigate]);

  const handleOptionSelect = (qIdx, option) => {
    if (submitted) return;
    setUserAnswers(prev => ({
      ...prev,
      [qIdx]: option
    }));
  };

  const handleSubmit = async () => {
    if (Object.keys(userAnswers).length < questions.length) {
      toast.warn("Please answer all questions before submitting.");
      return;
    }

    setSubmitted(true);
    let correctCount = 0;
    questions.forEach((q, idx) => {
      if (userAnswers[idx] === q.correct_answer) {
        correctCount++;
      }
    });
    
    setScore(correctCount);
    setCurrentStep('result');

    const quizResults = questions.map((q, idx) => ({
      question: q.question,
      options: q.options,
      correct_answer: q.correct_answer,
      user_answer: userAnswers[idx]
    }));

    try {
      await saveQuizScore(bookId, book.title, correctCount, quizResults);
      toast.success("Quiz score saved! 🎉");
    } catch (err) {
      console.error("Failed to save score:", err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-4">
        <div className="animate-bounce mb-6">
          <LitScholarLogo className="w-16 h-16" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">Creating your quiz...</h2>
        <p className="text-amber-200">Gemini is crafting 5 special questions for you.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <button
            onClick={() => navigate(`/book/${bookId}`)}
            className="flex items-center gap-2 text-white hover:text-amber-200 font-medium transition-colors"
          >
            <FaArrowLeft /> Back to Book
          </button>
          <LitScholarLogo className="w-10 h-10" />
        </div>

        <div className="bg-white/10 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/20 p-6 sm:p-10">
          <div className="mb-8 text-center">
            <h1 className="text-3xl font-black text-white mb-2 drop-shadow-md">Book Quiz</h1>
            <p className="text-amber-200 text-lg font-medium">"{book.title}"</p>
          </div>

          {currentStep === 'taking' && (
            <div className="space-y-10">
              {questions.map((q, qIdx) => (
                <div key={qIdx} className="space-y-4">
                  <h3 className="text-xl font-bold text-white leading-relaxed">
                    {qIdx + 1}. {q.question}
                  </h3>
                  <div className="grid grid-cols-1 gap-3">
                    {q.options.map((option, oIdx) => {
                      const isSelected = userAnswers[qIdx] === option;
                      return (
                        <button
                          key={oIdx}
                          onClick={() => handleOptionSelect(qIdx, option)}
                          className={`w-full text-left p-4 rounded-2xl border-2 transition-all duration-300 ${
                            isSelected 
                              ? 'bg-white border-white shadow-lg text-amber-900 font-black transform scale-[1.02]' 
                              : 'bg-white/5 border-white/10 text-white hover:bg-white/10 hover:border-white/30'
                          }`}
                        >
                          <span className="flex items-center gap-3">
                            <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs border ${isSelected ? 'bg-amber-800 text-white border-amber-800' : 'bg-transparent border-white/30 text-white/60'}`}>
                              {String.fromCharCode(65 + oIdx)}
                            </span>
                            {option}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}

              <button
                onClick={handleSubmit}
                className="w-full py-5 bg-gradient-to-r from-amber-700 to-amber-900 text-white rounded-2xl font-black text-xl hover:from-amber-800 hover:to-amber-950 transition-all shadow-xl transform hover:scale-[1.02] active:scale-[0.98] mt-8"
              >
                Submit Quiz
              </button>
            </div>
          )}

          {currentStep === 'result' && (
            <div className="text-center space-y-8 py-4">
              <div className="flex justify-center">
                <div className="relative animate-float">
                  <FaTrophy className="text-amber-400 w-24 h-24 drop-shadow-lg" />
                  <div className="absolute inset-0 flex items-center justify-center pt-2">
                    <span className="text-2xl font-black text-white drop-shadow-md">{score}/5</span>
                  </div>
                </div>
              </div>
              
              <div>
                <h2 className="text-3xl font-black text-white mb-2 drop-shadow-md">
                  {score === 5 ? "Perfect Score!" : score >= 3 ? "Great Job!" : "Good Effort!"}
                </h2>
                <p className="text-amber-200 text-lg font-medium">You scored {score} out of 5 correct.</p>
              </div>

              <div className="space-y-8 text-left mt-10">
                {questions.map((q, qIdx) => (
                  <div key={qIdx} className="p-6 rounded-2xl bg-white/5 backdrop-blur-md border border-white/10 shadow-sm">
                    <p className="font-bold text-white text-lg mb-4 leading-relaxed">{qIdx + 1}. {q.question}</p>
                    <div className="space-y-3">
                      {q.options.map((option, oIdx) => {
                        const isUserAnswer = userAnswers[qIdx] === option;
                        const isCorrect = option === q.correct_answer;
                        
                        let style = "bg-white/5 border-white/10 text-white/60 opacity-60";
                        if (isCorrect) style = "bg-green-500/20 border-green-500 text-green-100 font-bold ring-2 ring-green-500/50 opacity-100 shadow-lg shadow-green-500/20";
                        else if (isUserAnswer && !isCorrect) style = "bg-red-500/20 border-red-500 text-red-100 font-bold ring-2 ring-red-500/50 opacity-100 shadow-lg shadow-red-500/20";

                        return (
                          <div key={oIdx} className={`p-4 rounded-xl border flex justify-between items-center transition-all ${style}`}>
                            <span className="flex items-center gap-3">
                              <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs border ${isCorrect ? 'bg-green-500 text-white border-green-500' : isUserAnswer ? 'bg-red-500 text-white border-red-500' : 'bg-transparent border-white/30'}`}>
                                {String.fromCharCode(65 + oIdx)}
                              </span>
                              {option}
                            </span>
                            {isCorrect && <FaCheckCircle className="text-green-400 text-lg" />}
                            {isUserAnswer && !isCorrect && <FaTimesCircle className="text-red-400 text-lg" />}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex flex-col sm:flex-row gap-4 pt-8">
                <button
                  onClick={() => window.location.reload()}
                  className="flex-1 py-4 border-2 border-white/30 text-white rounded-2xl font-bold flex items-center justify-center gap-2 hover:bg-white/10 hover:border-white/50 transition-all backdrop-blur-sm"
                >
                  <FaRedo /> Retake Quiz
                </button>
                <button
                  onClick={() => navigate('/dashboard')}
                  className="flex-1 py-4 bg-gradient-to-r from-amber-700 to-amber-900 text-white rounded-2xl font-black flex items-center justify-center gap-2 hover:from-amber-800 hover:to-amber-950 transition-all shadow-xl"
                >
                  <FaHome /> Back to Home
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
