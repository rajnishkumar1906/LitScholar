// src/pages/Profile.jsx
import { useState, useEffect } from 'react';
import { 
  FaUser, FaEnvelope, FaBook, FaHistory, FaHeart, 
  FaCog, FaSignOutAlt, FaCamera, FaStar, FaSpinner 
} from 'react-icons/fa';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { useApp } from '../context/AppContext';

export default function Profile() {
  const { user, logout } = useApp();
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState({
    name: '',
    email: '',
    bio: '',
    location: '',
    favoriteGenres: [],
    readingGoal: 50,
    booksRead: 24,
    joinDate: ''
  });

  const [stats] = useState({
    totalBooks: 24,
    readingStreak: 12,
    reviews: 18,
    wishlist: 32
  });

  const [recentActivities] = useState([
    { id: 1, action: 'Finished reading', book: 'Atomic Habits', date: '2 days ago' },
    { id: 2, action: 'Added to wishlist', book: 'Dune', date: '5 days ago' },
    { id: 3, action: 'Reviewed', book: 'The Psychology of Money', date: '1 week ago' },
    { id: 4, action: 'Started reading', book: 'Sapiens', date: '2 weeks ago' }
  ]);

  const [readingHistory] = useState([
    { id: 1, book: 'Atomic Habits', author: 'James Clear', progress: 100, rating: 5 },
    { id: 2, book: 'The Psychology of Money', author: 'Morgan Housel', progress: 100, rating: 4 },
    { id: 3, book: 'Sapiens', author: 'Yuval Noah Harari', progress: 65, rating: null },
    { id: 4, book: 'Dune', author: 'Frank Herbert', progress: 30, rating: null }
  ]);

  // Load user data
  useEffect(() => {
    if (user) {
      setProfile({
        name: user.email?.split('@')[0] || 'John Doe',
        email: user.email || 'john.doe@example.com',
        bio: 'Avid reader and book enthusiast. Love exploring different genres and discovering hidden gems.',
        location: 'New York, USA',
        favoriteGenres: ['Fiction', 'Science Fiction', 'Self-Help'],
        readingGoal: 50,
        booksRead: 24,
        joinDate: 'January 2025'
      });
      setLoading(false);
    }
  }, [user]);

  const handleSave = () => {
    // TODO: Implement profile update API
    setIsEditing(false);
  };

  const handleLogout = () => {
    logout();
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
    <div className="min-h-screen">
      <Navbar />

      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Profile Header */}
        <div className="bg-white/70 backdrop-blur-sm rounded-3xl shadow-xl border border-gray-200 p-8 mb-8">
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
                      className="text-3xl font-bold text-gray-900 mb-1 border-b-2 border-amber-800 focus:outline-none"
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
                    className="px-6 py-2 bg-gradient-to-r from-amber-800 to-amber-900 text-white font-medium rounded-xl hover:shadow-lg transition-all flex items-center gap-2 self-start"
                  >
                    <FaCog className="w-4 h-4" />
                    {isEditing ? 'Save Changes' : 'Edit Profile'}
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
                  className="w-full p-3 border border-gray-300 rounded-xl mb-4 focus:outline-none focus:ring-2 focus:ring-amber-800"
                  rows="3"
                />
              ) : (
                <p className="text-gray-700 mb-4">{profile.bio}</p>
              )}

              <div className="flex flex-wrap gap-4 text-sm">
                {isEditing ? (
                  <input
                    type="text"
                    value={profile.location}
                    onChange={(e) => setProfile({ ...profile, location: e.target.value })}
                    className="px-3 py-1 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-800"
                    placeholder="Location"
                  />
                ) : (
                  <span className="text-gray-600">📍 {profile.location}</span>
                )}
                <span className="text-gray-600">📅 Joined {profile.joinDate}</span>
                <span className="text-gray-600">📚 {profile.booksRead}/{profile.readingGoal} books this year</span>
              </div>

              {/* Favorite Genres */}
              <div className="mt-4 flex flex-wrap gap-2">
                {profile.favoriteGenres.map((genre, index) => (
                  <span key={index} className="px-3 py-1 bg-amber-50 text-amber-900 rounded-full text-xs font-medium border border-amber-200">
                    {genre}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200 p-6 text-center">
            <div className="text-3xl font-bold text-amber-800 mb-1">{stats.totalBooks}</div>
            <div className="text-sm text-gray-600">Books Read</div>
          </div>
          <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200 p-6 text-center">
            <div className="text-3xl font-bold text-amber-800 mb-1">{stats.readingStreak}</div>
            <div className="text-sm text-gray-600">Day Streak</div>
          </div>
          <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200 p-6 text-center">
            <div className="text-3xl font-bold text-amber-800 mb-1">{stats.reviews}</div>
            <div className="text-sm text-gray-600">Reviews</div>
          </div>
          <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200 p-6 text-center">
            <div className="text-3xl font-bold text-amber-800 mb-1">{stats.wishlist}</div>
            <div className="text-sm text-gray-600">Wishlist</div>
          </div>
        </div>

        {/* Two Column Layout */}
        <div className="grid md:grid-cols-2 gap-8">
          {/* Reading History */}
          <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <FaHistory className="w-5 h-5 text-amber-700" />
              Reading History
            </h2>
            <div className="space-y-4">
              {readingHistory.map((item) => (
                <div key={item.id} className="flex items-center justify-between">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900">{item.book}</h3>
                    <p className="text-sm text-gray-500">by {item.author}</p>
                  </div>
                  <div className="text-right">
                    {item.rating ? (
                      <div className="flex items-center gap-1 text-amber-600">
                        {'★'.repeat(item.rating)}
                        {'☆'.repeat(5 - item.rating)}
                      </div>
                    ) : (
                      <span className="text-sm text-gray-500">{item.progress}%</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
            <button className="mt-4 text-sm text-amber-700 hover:text-amber-800 font-medium">
              View all history →
            </button>
          </div>

          {/* Recent Activity */}
          <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <FaHeart className="w-5 h-5 text-amber-700" />
              Recent Activity
            </h2>
            <div className="space-y-4">
              {recentActivities.map((activity) => (
                <div key={activity.id} className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-amber-50 rounded-lg flex items-center justify-center">
                    <FaBook className="w-4 h-4 text-amber-700" />
                  </div>
                  <div className="flex-1">
                    <p className="text-gray-800">
                      <span className="font-medium">{activity.action}</span>{' '}
                      <span className="text-amber-800">"{activity.book}"</span>
                    </p>
                    <p className="text-xs text-gray-500">{activity.date}</p>
                  </div>
                </div>
              ))}
            </div>
            <button className="mt-4 text-sm text-amber-700 hover:text-amber-800 font-medium">
              View all activity →
            </button>
          </div>
        </div>

        {/* Reading Goal Progress */}
        <div className="mt-8 bg-white/70 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-800">2025 Reading Goal</h2>
            <span className="text-amber-800 font-semibold">{profile.booksRead}/{profile.readingGoal} books</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-gradient-to-r from-amber-700 to-amber-800 h-3 rounded-full"
              style={{ width: `${(profile.booksRead / profile.readingGoal) * 100}%` }}
            ></div>
          </div>
          <p className="text-sm text-gray-500 mt-2">
            {profile.readingGoal - profile.booksRead} more books to reach your goal!
          </p>
        </div>
      </main>

      <Footer />
    </div>
  );
}