// src/pages/Auth.jsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FaEnvelope,
  FaLock,
  FaUser,
  FaGoogle,
  FaGithub,
  FaArrowRight
} from 'react-icons/fa';
import LitScholarLogo from '../components/LitScholarLogo';
import { useApp } from '../context/AppContext';

export default function Auth() {
  const [isLogin, setIsLogin] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [error, setError] = useState('');

  const navigate = useNavigate();
  const { login, register, googleLogin, handleGoogleCallback, isAuthenticated } = useApp();

  // Check for Google OAuth callback (tokens in URL) or existing auth
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('access_token')) {
      handleGoogleCallback();
      window.history.replaceState({}, '', window.location.pathname);
      navigate('/dashboard', { replace: true });
      return;
    }
    if (isAuthenticated()) {
      navigate('/dashboard');
    }
  }, [handleGoogleCallback, isAuthenticated, navigate]);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      if (isLogin) {
        const result = await login(formData.email, formData.password);
        if (result.success) {
          navigate('/dashboard');
        } else {
          setError(result.error);
        }
      } else {
        // Validate passwords match
        if (formData.password !== formData.confirmPassword) {
          throw new Error('Passwords do not match');
        }
        
        const result = await register(formData.email, formData.password);
        if (result.success) {
          setIsLogin(true);
          setFormData({ ...formData, password: '', confirmPassword: '' });
          alert('Registration successful! Please login.');
        } else {
          setError(result.error);
        }
      }
    } catch (error) {
      setError(error.message || 'Authentication failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    googleLogin();
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setFormData({
      name: '',
      email: '',
      password: '',
      confirmPassword: ''
    });
    setError('');
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-150">
        <div className="bg-white/20 backdrop-blur-md rounded-3xl shadow-2xl p-8">
          {/* Logo */}
          <div className="flex flex-col items-center mb-6">
            <div className="p-3 bg-gradient-to-r from-amber-800 to-amber-900 rounded-2xl mb-3 shadow-lg">
              <LitScholarLogo className="w-12 h-12 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-amber-900">
              LitScholar
            </h1>
          </div>

          {/* Form header */}
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">
              {isLogin ? 'Welcome Back' : 'Create Account'}
            </h2>
            <p className="text-gray-200 text-lg">
              {isLogin
                ? 'Sign in to continue your reading journey'
                : 'Get started with your free account'}
            </p>
          </div>

          {/* Error message */}
          {error && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-xl text-sm">
              {error}
            </div>
          )}

          {/* Auth Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div>
                <label className="block text-m font-medium text-gray-100 mb-1">
                  Full name
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <FaUser className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-xl bg-white/80 backdrop-blur-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-amber-800"
                    placeholder="John Doe"
                    required={!isLogin}
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-m font-medium text-gray-100 mb-1">
                Email address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <FaEnvelope className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-xl bg-white/80 backdrop-blur-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-amber-800"
                  placeholder="you@example.com"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-m font-medium text-gray-100 mb-1">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <FaLock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-xl bg-white/80 backdrop-blur-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-amber-800"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            {!isLogin && (
              <div>
                <label className="block text-m font-medium text-gray-100 mb-1">
                  Confirm password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <FaLock className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="password"
                    name="confirmPassword"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-xl bg-white/80 backdrop-blur-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-amber-800"
                    placeholder="••••••••"
                    required={!isLogin}
                  />
                </div>
              </div>
            )}

            {isLogin && (
              <div className="flex items-center justify-between">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    className="w-4 h-4 rounded border-gray-300 text-amber-800 focus:ring-amber-800"
                  />
                  <span className="ml-2 text-m text-gray-100">Remember me</span>
                </label>
                <a href="#" className="text-sm font-medium text-amber-800 hover:text-amber-900">
                  Forgot password?
                </a>
              </div>
            )}

            {!isLogin && (
              <div className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  className="w-4 h-4 rounded border-gray-300 text-amber-800 focus:ring-amber-800"
                  required
                />
                <span className="text-gray-600">
                  I agree to the{' '}
                  <a href="#" className="text-amber-800 hover:underline">Terms</a> and{' '}
                  <a href="#" className="text-amber-800 hover:underline">Privacy Policy</a>
                </span>
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-gradient-to-r from-amber-800 to-amber-900 text-white font-semibold rounded-xl hover:from-amber-900 hover:to-amber-950 disabled:opacity-50 transition-all group"
            >
              {isLoading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>{isLogin ? 'Signing in...' : 'Creating account...'}</span>
                </>
              ) : (
                <>
                  <span>{isLogin ? 'Sign in' : 'Create account'}</span>
                  <FaArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-4 bg-white/60 backdrop-blur-sm text-gray-500">
                Or continue with
              </span>
            </div>
          </div>

          {/* Social login */}
          <div className="grid grid-cols-2 gap-3">
            <button 
              onClick={handleGoogleLogin}
              className="flex items-center justify-center gap-2 py-3 border border-gray-300 rounded-xl bg-white/80 backdrop-blur-sm hover:bg-gray-100 transition-all"
            >
              <FaGoogle className="w-5 h-5 text-gray-600" />
              <span className="text-sm font-medium text-gray-700">Google</span>
            </button>
            <button className="flex items-center justify-center gap-2 py-3 border border-gray-300 rounded-xl bg-white/80 backdrop-blur-sm hover:bg-gray-100 transition-all">
              <FaGithub className="w-5 h-5 text-gray-600" />
              <span className="text-sm font-medium text-gray-700">GitHub</span>
            </button>
          </div>

          {/* Toggle */}
          <p className="mt-6 text-center text-sm text-gray-100">
            {isLogin ? "Don't have an account?" : "Already have an account?"}
            <button onClick={toggleMode} className="ml-1 font-semibold text-amber-800 hover:text-amber-900">
              {isLogin ? 'Create free account' : 'Sign in'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}