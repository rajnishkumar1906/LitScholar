// src/pages/Profile.jsx
import { useState, useEffect } from 'react';
import {
  FaUser, FaEnvelope, FaBook, FaHistory, FaHeart,
  FaCog, FaSignOutAlt, FaCamera, FaSpinner, FaCalendarAlt
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
    fetchUserActivity
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
    readingGoal: 0,
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
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Fetch user's books and activity - USING CONTEXT FUNCTIONS
  const fetchUserBooksAndActivity = async () => {
    if (!user) return;

    setLoadingHistory(true);
    try {
      const [booksRes, activityRes] = await Promise.all([
        fetchUserBooks('finished', 5),
        fetchUserActivity(5)
      ]);

      if (booksRes.success) setReadingHistory(booksRes.books);
      if (activityRes.success) setRecentActivities(activityRes.activities);
    } catch (error) {
      console.error('Error fetching user data:', error);
    } finally {
      setLoadingHistory(false);
    }
  };

  const updateProfileState = (profileData, userData = null) => {
    const userInfo = userData || user || {};

    setProfile({
      name: userInfo.full_name || userInfo.email?.split('@')[0] || '',
      email: userInfo.email || '',
      bio: userInfo.bio || '',
      location: userInfo.location || '',
      favoriteGenres: Array.isArray(profileData?.categories_read) ? profileData.categories_read : [],
      readingGoal: profileData?.yearly_goal || 0,
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
        if (profileStats) {
          updateProfileState(profileStats, profileStats.user);
        } else {
          const res = await loadProfile();
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
  }, [user]); // Only depend on user, not profileStats

  const handleSave = async () => {
    setSaving(true);
    try {
      const updateData = {
        full_name: profile.name !== user?.email?.split('@')[0] ? profile.name : undefined,
        yearly_goal: profile.readingGoal,
        categories_read: profile.favoriteGenres,
        bio: profile.bio || undefined,
        location: profile.location || undefined
      };

      // Remove undefined values
      Object.keys(updateData).forEach(key =>
        updateData[key] === undefined && delete updateData[key]
      );

      const result = await updateProfile(updateData);

      if (result.success) {
        setIsEditing(false);
        toast.success('Profile updated successfully!');
        // Refresh profile data
        await loadProfile();
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
                      placeholder="0"
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
              {profile.favoriteGenres.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2">
                  {profile.favoriteGenres.map((genre, index) => (
                    <span key={index} className="px-3 py-1 bg-amber-50 text-amber-900 rounded-full text-xs font-medium border border-amber-200">
                      {genre}
                    </span>
                  ))}
                </div>
              )}
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
                {recentActivities.map((activity) => (
                  <div key={activity.id} className="flex items-start gap-3">
                    <div className="w-8 h-8 bg-amber-50 rounded-lg flex items-center justify-center">
                      <FaBook className="w-4 h-4 text-amber-700" />
                    </div>
                    <div className="flex-1">
                      <p className="text-gray-800">
                        <span className="font-medium">{activity.activity_type}</span>{' '}
                        {activity.book_title && (
                          <span className="text-amber-800">"{activity.book_title}"</span>
                        )}
                      </p>
                      <p className="text-xs text-gray-500">
                        {new Date(activity.created_at).toLocaleDateString()}
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
                  style={{ width: `${(profile.booksRead / profile.readingGoal) * 100}%` }}
                ></div>
              </div>
              <p className="text-sm text-gray-500 mt-2">
                {profile.readingGoal - profile.booksRead} more books to reach your goal!
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