// src/pages/Profile.jsx
import { useState, useEffect } from 'react';
import {
  FaUser, FaEnvelope, FaBook, FaHistory, FaHeart,
  FaCog, FaSignOutAlt, FaCamera, FaSpinner, FaCalendarAlt, FaTrophy, FaTimes, FaCheckCircle, FaTimesCircle
} from 'react-icons/fa';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { useApp } from '../context/AppContext';
import { toast } from 'react-toastify';

export default function Profile() {
  const {
    user,
    logout,
    profileStats,
    loadProfile,
    updateProfile,
    fetchUserBooks,
    fetchUserActivity,
    getQuizHistory
  } = useApp();

  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [profile, setProfile] = useState({
    name: '',
    email: '',
    bio: '',
    location: '',
    favoriteGenres: [],
    readingGoal: 12,
    booksRead: 0,
    joinDate: ''
  });

  const [stats, setStats] = useState({
    totalBooks: 0,
    totalPages: 0,
    readingStreak: 0,
    longestStreak: 0,
    monthlyProgress: 0,
    yearlyProgress: 0
  });

  const [readingHistory, setReadingHistory] = useState([]);
  const [recentActivities, setRecentActivities] = useState([]);
  const [quizHistory, setQuizHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [selectedQuiz, setSelectedQuiz] = useState(null);

  // Fetch user's books, activity, and quiz history
  const fetchUserBooksAndActivity = async () => {
    if (!user) return;

    setLoadingHistory(true);
    try {
      const [booksRes, activityRes, quizRes] = await Promise.all([
        fetchUserBooks('finished', 6),
        fetchUserActivity(6),
        getQuizHistory(6)
      ]);

      if (booksRes.success) {
        setReadingHistory(booksRes.books || []);
      }
      
      if (activityRes.success) {
        setRecentActivities(activityRes.activities || []);
      }

      if (quizRes.success) {
        setQuizHistory(quizRes.data || []);
      }
    } catch (error) {
      console.error('Error fetching user data:', error);
    } finally {
      setLoadingHistory(false);
    }
  };

  const updateProfileState = (profileData, userData = null) => {
    const userInfo = userData || user || {};

    // Parse categories_read if it's a string
    let categories = [];
    if (profileData?.categories_read) {
      if (typeof profileData.categories_read === 'string') {
        try {
          categories = JSON.parse(profileData.categories_read);
        } catch {
          categories = [profileData.categories_read];
        }
      } else if (Array.isArray(profileData.categories_read)) {
        categories = profileData.categories_read;
      }
    }

    setProfile({
      name: userInfo.full_name || userInfo.email?.split('@')[0] || '',
      email: userInfo.email || '',
      bio: userInfo.bio || '',
      location: userInfo.location || '',
      favoriteGenres: categories,
      readingGoal: profileData?.yearly_goal || 12,
      booksRead: profileData?.total_books_read || 0,
      joinDate: userInfo.created_at ? new Date(userInfo.created_at).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      }) : ''
    });

    setStats({
      totalBooks: profileData?.total_books_read || 0,
      totalPages: profileData?.total_pages_read || 0,
      readingStreak: profileData?.current_streak || 0,
      longestStreak: profileData?.longest_streak || 0,
      monthlyProgress: profileData?.monthly_progress || 0,
      yearlyProgress: profileData?.yearly_progress || 0
    });
  };

  // Load user + profile data
  useEffect(() => {
    const init = async () => {
      if (!user) {
        setLoading(false);
        return;
      }

      try {
        console.log("👤 Loading profile for user:", user);
        
        if (profileStats) {
          updateProfileState(profileStats, profileStats.user);
        } else {
          const res = await loadProfile();
          console.log("📥 Profile loaded:", res);
          if (res.success) {
            updateProfileState(res.profile, res.user);
          }
        }

        await fetchUserBooksAndActivity();
      } catch (error) {
        console.error('Error initializing profile:', error);
      } finally {
        setLoading(false);
      }
    };

    init();
  }, [user]); // Only depend on user

  const handleSave = async () => {
    setSaving(true);
    try {
      const updateData = {
        full_name: profile.name !== user?.email?.split('@')[0] ? profile.name : undefined,
        bio: profile.bio || undefined,
        location: profile.location || undefined,
        yearly_goal: profile.readingGoal,
        categories_read: profile.favoriteGenres
      };

      // Remove undefined values
      Object.keys(updateData).forEach(key =>
        updateData[key] === undefined && delete updateData[key]
      );

      console.log("📤 Updating profile with:", updateData);

      const result = await updateProfile(updateData);

      if (result.success) {
        setIsEditing(false);
        toast.success('Profile updated successfully!');
        // Refresh profile data
        await loadProfile();
        await fetchUserBooksAndActivity();
      }
    } catch (error) {
      console.error('Error saving profile:', error);
      toast.error('Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = () => {
    logout();
  };

  const handleAddGenre = (genre) => {
    if (genre && !profile.favoriteGenres.includes(genre)) {
      setProfile({
        ...profile,
        favoriteGenres: [...profile.favoriteGenres, genre]
      });
    }
  };

  const handleRemoveGenre = (genreToRemove) => {
    setProfile({
      ...profile,
      favoriteGenres: profile.favoriteGenres.filter(g => g !== genreToRemove)
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="bg-white/95 backdrop-blur-sm shadow-xl p-8 rounded-3xl border border-gray-200">
          <FaSpinner className="w-12 h-12 text-amber-800 animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white/1 flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-6xl mx-auto px-4 py-8 w-full">
        {/* Profile Header */}
        <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-xl border border-gray-200 p-8 mb-8">
          <div className="flex flex-col md:flex-row gap-8 items-start">
            {/* Profile Picture */}
            <div className="relative group">
              <div className="w-32 h-32 rounded-2xl bg-gradient-to-r from-amber-800 to-amber-900 flex items-center justify-center">
                <FaUser className="w-16 h-16 text-white/80" />
              </div>
              <button className="absolute bottom-2 right-2 p-2 bg-white rounded-xl shadow-md hover:shadow-lg transition-all border border-gray-200 opacity-0 group-hover:opacity-100">
                <FaCamera className="w-4 h-4 text-amber-800" />
              </button>
            </div>

            {/* Profile Info */}
            <div className="flex-1">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                <div>
                  {isEditing ? (
                    <input
                      type="text"
                      value={profile.name}
                      onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                      className="text-3xl font-bold text-gray-900 mb-1 border-b-2 border-amber-800 focus:outline-none bg-transparent"
                      placeholder="Your name"
                    />
                  ) : (
                    <h1 className="text-3xl font-bold text-gray-900 mb-1">{profile.name}</h1>
                  )}
                  <p className="text-gray-600 flex items-center gap-2">
                    <FaEnvelope className="w-4 h-4" />
                    {profile.email}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => isEditing ? handleSave() : setIsEditing(true)}
                    disabled={saving}
                    className="px-6 py-2 bg-gradient-to-r from-amber-800 to-amber-900 text-white font-medium rounded-xl hover:shadow-lg transition-all flex items-center gap-2 self-start disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {saving ? <FaSpinner className="w-4 h-4 animate-spin" /> : <FaCog className="w-4 h-4" />}
                    {saving ? 'Saving...' : (isEditing ? 'Save Changes' : 'Edit Profile')}
                  </button>
                  <button
                    onClick={handleLogout}
                    className="px-4 py-2 border border-red-200 text-red-600 font-medium rounded-xl hover:bg-red-50 transition-all flex items-center gap-2"
                  >
                    <FaSignOutAlt className="w-4 h-4" />
                    <span className="hidden sm:inline">Logout</span>
                  </button>
                </div>
              </div>

              {isEditing ? (
                <textarea
                  value={profile.bio}
                  onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
                  className="w-full p-3 border border-gray-300 rounded-xl mb-4 focus:outline-none focus:ring-2 focus:ring-amber-800 bg-white/50"
                  rows="3"
                  placeholder="Tell us about yourself..."
                />
              ) : (
                profile.bio && <p className="text-gray-700 mb-4">{profile.bio}</p>
              )}

              <div className="flex flex-wrap gap-4 text-sm">
                {isEditing ? (
                  <input
                    type="text"
                    value={profile.location}
                    onChange={(e) => setProfile({ ...profile, location: e.target.value })}
                    className="px-3 py-1 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-800 bg-white/50"
                    placeholder="Location"
                  />
                ) : (
                  profile.location && <span className="text-gray-600">📍 {profile.location}</span>
                )}

                {isEditing && (
                  <div className="flex items-center gap-2">
                    <label className="text-sm text-gray-600">Reading Goal:</label>
                    <input
                      type="number"
                      min="1"
                      value={profile.readingGoal}
                      onChange={(e) => setProfile({
                        ...profile,
                        readingGoal: parseInt(e.target.value) || 0
                      })}
                      className="w-20 px-2 py-1 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-800 bg-white/50"
                      placeholder="12"
                    />
                    <span className="text-sm text-gray-600">books/year</span>
                  </div>
                )}

                {profile.joinDate && (
                  <span className="text-gray-600 flex items-center gap-1">
                    <FaCalendarAlt className="w-3 h-3" /> Joined {profile.joinDate}
                  </span>
                )}

                <span className="text-gray-600">
                  📚 {profile.booksRead}/{profile.readingGoal || 1} books this year
                </span>
              </div>

              {/* Favorite Genres */}
              <div className="mt-4 flex flex-wrap gap-2 items-center">
                {profile.favoriteGenres.map((genre, index) => (
                  <span key={index} className="px-3 py-1 bg-amber-50 text-amber-900 rounded-full text-xs font-medium border border-amber-200 flex items-center gap-1">
                    {genre}
                    {isEditing && (
                      <button
                        onClick={() => handleRemoveGenre(genre)}
                        className="ml-1 text-amber-700 hover:text-amber-900"
                      >
                        ×
                      </button>
                    )}
                  </span>
                ))}
                {isEditing && (
                  <input
                    type="text"
                    placeholder="Add genre..."
                    className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-amber-800 bg-white/50"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleAddGenre(e.target.value);
                        e.target.value = '';
                      }
                    }}
                  />
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200 p-4 text-center">
            <div className="text-2xl font-bold text-amber-800 mb-1">{stats.totalBooks}</div>
            <div className="text-xs text-gray-600">Books Read</div>
          </div>
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200 p-4 text-center">
            <div className="text-2xl font-bold text-amber-800 mb-1">{stats.totalPages}</div>
            <div className="text-xs text-gray-600">Pages Read</div>
          </div>
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200 p-4 text-center">
            <div className="text-2xl font-bold text-amber-800 mb-1">{stats.readingStreak}</div>
            <div className="text-xs text-gray-600">Current Streak</div>
          </div>
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200 p-4 text-center">
            <div className="text-2xl font-bold text-amber-800 mb-1">{stats.longestStreak}</div>
            <div className="text-xs text-gray-600">Longest Streak</div>
          </div>
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200 p-4 text-center">
            <div className="text-2xl font-bold text-amber-800 mb-1">{stats.monthlyProgress}</div>
            <div className="text-xs text-gray-600">Monthly</div>
          </div>
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200 p-4 text-center">
            <div className="text-2xl font-bold text-amber-800 mb-1">{stats.yearlyProgress}</div>
            <div className="text-xs text-gray-600">Yearly</div>
          </div>
        </div>

        {/* Two Column Layout */}
        <div className="grid md:grid-cols-2 gap-8">
          {/* Reading History */}
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <FaHistory className="w-5 h-5 text-amber-700" />
              Reading History
            </h2>
            {loadingHistory ? (
              <div className="flex justify-center py-8">
                <FaSpinner className="w-8 h-8 text-amber-800 animate-spin" />
              </div>
            ) : readingHistory.length > 0 ? (
              <div className="space-y-4">
                {readingHistory.map((item) => (
                  <div key={item.id} className="flex items-center justify-between">
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900">{item.book_title || item.title}</h3>
                      <p className="text-sm text-gray-500">by {item.author}</p>
                    </div>
                    <div className="text-right">
                      {item.rating ? (
                        <div className="flex items-center gap-1 text-amber-600">
                          {'★'.repeat(item.rating)}
                          {'☆'.repeat(5 - item.rating)}
                        </div>
                      ) : (
                        <span className="text-sm text-gray-500">
                          {item.finish_date ? 'Completed' : 'In Progress'}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">No reading history yet</p>
            )}
            {readingHistory.length > 0 && (
              <button className="mt-4 text-sm text-amber-700 hover:text-amber-800 font-medium">
                View all history →
              </button>
            )}
          </div>

          {/* Recent Activity */}
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <FaHeart className="w-5 h-5 text-amber-700" />
              Recent Activity
            </h2>
            {loadingHistory ? (
              <div className="flex justify-center py-8">
                <FaSpinner className="w-8 h-8 text-amber-800 animate-spin" />
              </div>
            ) : recentActivities.length > 0 ? (
              <div className="space-y-4">
                {recentActivities.map((activity, index) => (
                  <div key={activity.id || index} className="flex items-start gap-3">
                    <div className="w-8 h-8 bg-amber-50 rounded-lg flex items-center justify-center">
                      <FaBook className="w-4 h-4 text-amber-700" />
                    </div>
                    <div className="flex-1">
                      <p className="text-gray-800">
                        <span className="font-medium">
                          {activity.activity_type?.replace(/_/g, ' ') || 'Activity'}
                        </span>{' '}
                        {activity.book_title && (
                          <span className="text-amber-800">"{activity.book_title}"</span>
                        )}
                      </p>
                      <p className="text-xs text-gray-500">
                        {activity.created_at ? new Date(activity.created_at).toLocaleDateString() : ''}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">No recent activity</p>
            )}
            {recentActivities.length > 0 && (
              <button className="mt-4 text-sm text-amber-700 hover:text-amber-800 font-medium">
                View all activity →
              </button>
            )}
          </div>
        </div>

        {/* Quiz History Section */}
        <div className="mt-8 bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-6 flex items-center gap-2">
            <FaTrophy className="w-5 h-5 text-amber-700" />
            Quiz History
          </h2>
          {loadingHistory ? (
            <div className="flex justify-center py-8">
              <FaSpinner className="w-8 h-8 text-amber-800 animate-spin" />
            </div>
          ) : quizHistory.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {quizHistory.map((quiz) => (
                <div 
                  key={quiz.id} 
                  onClick={() => setSelectedQuiz(quiz)}
                  className="p-4 rounded-xl bg-white/50 border border-amber-100 shadow-sm flex items-center gap-4 group hover:bg-white/80 transition-all duration-300 cursor-pointer"
                >
                  <div className="w-12 h-12 rounded-lg bg-amber-50 flex items-center justify-center text-amber-800 font-bold text-lg group-hover:scale-110 transition-transform">
                    {quiz.score}/{quiz.total_questions}
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-gray-900 line-clamp-1">{quiz.book_title}</h3>
                    <p className="text-xs text-gray-500">
                      {new Date(quiz.created_at).toLocaleDateString()} at {new Date(quiz.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className={`text-sm font-bold ${quiz.score >= 4 ? 'text-green-600' : quiz.score >= 3 ? 'text-amber-600' : 'text-red-600'}`}>
                      {Math.round((quiz.score / quiz.total_questions) * 100)}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8 bg-gray-50/50 rounded-xl border border-dashed border-gray-300">
              No quizzes taken yet. Visit a book page to start a quiz!
            </p>
          )}
        </div>

        {/* Quiz Details Modal */}
        {selectedQuiz && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <div className="bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/20 w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col animate-fadeIn">
              {/* Modal Header */}
              <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-amber-50/50">
                <div>
                  <h2 className="text-2xl font-black text-gray-900 leading-tight">{selectedQuiz.book_title}</h2>
                  <p className="text-sm text-gray-600">Quiz taken on {new Date(selectedQuiz.created_at).toLocaleDateString()}</p>
                </div>
                <button 
                  onClick={() => setSelectedQuiz(null)}
                  className="p-2 hover:bg-gray-200 rounded-full transition-colors"
                >
                  <FaTimes className="w-5 h-5 text-gray-500" />
                </button>
              </div>

              {/* Modal Content */}
              <div className="flex-1 overflow-y-auto p-6 space-y-8">
                {/* Score Summary */}
                <div className="flex items-center justify-between p-6 bg-gradient-to-r from-amber-800 to-amber-900 rounded-2xl text-white shadow-lg">
                  <div className="flex items-center gap-4">
                    <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center">
                      <FaTrophy className="w-8 h-8 text-amber-300" />
                    </div>
                    <div>
                      <p className="text-amber-200 text-sm font-bold uppercase tracking-wider">Final Score</p>
                      <h3 className="text-3xl font-black">{selectedQuiz.score} / {selectedQuiz.total_questions}</h3>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-amber-200 text-sm font-bold uppercase tracking-wider">Percentage</p>
                    <h3 className="text-3xl font-black">{Math.round((selectedQuiz.score / selectedQuiz.total_questions) * 100)}%</h3>
                  </div>
                </div>

                {/* Question Details */}
                <div className="space-y-6">
                  {selectedQuiz.quiz_results && selectedQuiz.quiz_results.length > 0 ? (
                    selectedQuiz.quiz_results.map((q, idx) => (
                      <div key={idx} className="p-5 rounded-2xl bg-gray-50 border border-gray-100 shadow-sm space-y-4">
                        <p className="font-bold text-gray-900 text-lg leading-relaxed">{idx + 1}. {q.question}</p>
                        <div className="space-y-2">
                          {q.options.map((option, oIdx) => {
                            const isUserAnswer = q.user_answer === option;
                            const isCorrect = option === q.correct_answer;
                            
                            let style = "bg-white border-gray-200 text-gray-600 opacity-60";
                            if (isCorrect) style = "bg-green-50 border-green-500 text-green-800 font-bold ring-2 ring-green-500/20 opacity-100 shadow-sm";
                            else if (isUserAnswer && !isCorrect) style = "bg-red-50 border-red-500 text-red-800 font-bold ring-2 ring-red-500/20 opacity-100 shadow-sm";

                            return (
                              <div key={oIdx} className={`p-3 rounded-xl border flex justify-between items-center transition-all ${style}`}>
                                <span className="flex items-center gap-3">
                                  <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs border ${isCorrect ? 'bg-green-500 text-white border-green-500' : isUserAnswer ? 'bg-red-500 text-white border-red-500' : 'bg-transparent border-gray-300'}`}>
                                    {String.fromCharCode(65 + oIdx)}
                                  </span>
                                  {option}
                                </span>
                                {isCorrect && <FaCheckCircle className="text-green-600" />}
                                {isUserAnswer && !isCorrect && <FaTimesCircle className="text-red-600" />}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8">
                      <p className="text-gray-500">Detailed results are not available for this quiz.</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Modal Footer */}
              <div className="p-6 border-t border-gray-100 bg-gray-50/50 flex justify-end">
                <button 
                  onClick={() => setSelectedQuiz(null)}
                  className="px-8 py-3 bg-gray-900 text-white font-bold rounded-xl hover:bg-gray-800 transition-all shadow-md active:scale-95"
                >
                  Close Results
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Reading Goal Progress */}
        <div className="mt-8 bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-800">
              Reading Goal {profile.readingGoal > 0 ? `: ${profile.readingGoal} books` : ''}
            </h2>
            <span className="text-amber-800 font-semibold">
              {profile.booksRead}/{profile.readingGoal || 0} books
            </span>
          </div>

          {profile.readingGoal > 0 ? (
            <>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-gradient-to-r from-amber-700 to-amber-800 h-3 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min((profile.booksRead / profile.readingGoal) * 100, 100)}%` }}
                ></div>
              </div>
              <p className="text-sm text-gray-500 mt-2">
                {Math.max(profile.readingGoal - profile.booksRead, 0)} more books to reach your goal!
              </p>
            </>
          ) : (
            <p className="text-sm text-gray-500 italic">
              No reading goal set. Click "Edit Profile" to set your yearly reading target.
            </p>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}