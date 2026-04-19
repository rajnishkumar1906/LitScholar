// src/pages/ForgotPassword.jsx
import { useState, useRef, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { FaEnvelope, FaArrowLeft, FaCheckCircle, FaLock, FaKey, FaSync } from 'react-icons/fa';
import LitScholarLogo from '../components/LitScholarLogo';
import { authService } from '../services/auth';
import { toast } from 'react-toastify';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const otpRefs = [useRef(), useRef(), useRef(), useRef(), useRef(), useRef()];
  
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const [isLoading, setIsLoading] = useState(false);
  const [step, setStep] = useState('email'); // 'email', 'otp', 'password', 'success'
  const [error, setError] = useState('');
  const navigate = useNavigate();

  // Timer state
  const [timer, setTimer] = useState(0);
  const [canResend, setCanResend] = useState(false);

  // Focus management for OTP
  useEffect(() => {
    if (step === 'otp') {
      setTimeout(() => otpRefs[0].current?.focus(), 100);
    }
  }, [step]);

  // Timer logic
  useEffect(() => {
    let interval = null;
    if (timer > 0) {
      interval = setInterval(() => {
        setTimer((prev) => prev - 1);
      }, 1000);
    } else {
      setCanResend(true);
      clearInterval(interval);
    }
    return () => clearInterval(interval);
  }, [timer]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  const handleOtpChange = (index, value) => {
    if (value && !/^\d+$/.test(value)) return;
    const newOtp = [...otp];
    newOtp[index] = value.substring(value.length - 1);
    setOtp(newOtp);
    if (value && index < 5) {
      otpRefs[index + 1].current.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      otpRefs[index - 1].current.focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').slice(0, 6).split('');
    const newOtp = [...otp];
    pastedData.forEach((char, index) => {
      if (/^\d$/.test(char) && index < 6) {
        newOtp[index] = char;
      }
    });
    setOtp(newOtp);
    const nextIndex = Math.min(pastedData.length, 5);
    otpRefs[nextIndex].current.focus();
  };

  const startTimer = () => {
    setTimer(600); // 10 minutes
    setCanResend(false);
  };

  const handleSendOtp = async (e) => {
    if (e) e.preventDefault();
    setIsLoading(true);
    setError('');
    try {
      await authService.forgotPassword(email);
      setStep('otp');
      startTimer();
      toast.success('OTP sent to your email!');
    } catch (err) {
      setError(err.message || 'Failed to send OTP. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    const otpString = otp.join('');
    if (otpString.length < 6) {
      setError('Please enter the full 6-digit OTP.');
      return;
    }
    setIsLoading(true);
    setError('');
    try {
      await authService.verifyOtp(email, otpString);
      setStep('password');
      toast.success('OTP verified! Set your new password.');
    } catch (err) {
      setError(err.message || 'Invalid OTP or code expired.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }
    setIsLoading(true);
    setError('');
    try {
      await authService.resetPassword(email, otp.join(''), newPassword);
      setStep('success');
      toast.success('Password reset successfully! 🎉');
    } catch (err) {
      setError(err.message || 'Failed to reset password.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <LitScholarLogo className="h-12 w-auto" />
        </div>
        <h2 className="mt-6 text-center text-3xl font-black text-white drop-shadow-md">
          {step === 'success' ? 'Password Reset!' : 'Reset your password'}
        </h2>
        <p className="mt-2 text-center text-sm text-amber-200 font-medium px-4">
          {step === 'email' && "Enter your email and we'll send you a 6-digit OTP."}
          {step === 'otp' && `Enter the 6-digit code sent to ${email}.`}
          {step === 'password' && "OTP verified! Enter your new password below."}
          {step === 'success' && "Your password has been updated. You can now log in."}
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4 sm:px-0">
        <div className="bg-white/10 backdrop-blur-xl py-8 px-4 shadow-2xl sm:rounded-3xl sm:px-10 border border-white/20">
          
          {step === 'email' && (
            <form className="space-y-6" onSubmit={handleSendOtp}>
              {error && (
                <div className="bg-red-500/10 backdrop-blur-md border border-red-500/20 p-4 rounded-xl mb-4">
                  <p className="text-sm font-bold text-red-100">{error}</p>
                </div>
              )}
              <div>
                <label htmlFor="email" className="block text-sm font-black text-white mb-2 uppercase tracking-widest">
                  Email address
                </label>
                <div className="mt-1 relative rounded-xl shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <FaEnvelope className="h-5 w-5 text-amber-400" />
                  </div>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="block w-full pl-10 pr-3 py-3 border border-white/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent bg-white/5 text-white placeholder-white/40 transition-all font-medium"
                    placeholder="you@example.com"
                  />
                </div>
              </div>
              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex justify-center py-4 px-4 border border-transparent rounded-xl shadow-xl text-base font-black text-white bg-gradient-to-r from-amber-700 to-amber-900 hover:from-amber-800 hover:to-amber-950 transition-all transform hover:scale-[1.02] active:scale-[0.98]"
              >
                {isLoading ? "Sending..." : "Send 6-Digit OTP"}
              </button>
            </form>
          )}

          {step === 'otp' && (
            <form className="space-y-6" onSubmit={handleVerifyOtp}>
              {error && (
                <div className="bg-red-500/10 backdrop-blur-md border border-red-500/20 p-4 rounded-xl mb-4">
                  <p className="text-sm font-bold text-red-100">{error}</p>
                </div>
              )}
              <div className="text-center">
                <label className="block text-sm font-black text-white mb-4 uppercase tracking-widest">
                  Enter 6-Digit OTP
                </label>
                <div className="flex justify-between gap-2 mb-4" onPaste={handlePaste}>
                  {otp.map((digit, idx) => (
                    <input
                      key={idx}
                      ref={otpRefs[idx]}
                      type="text"
                      inputMode="numeric"
                      maxLength="1"
                      value={digit}
                      onChange={(e) => handleOtpChange(idx, e.target.value)}
                      onKeyDown={(e) => handleKeyDown(idx, e)}
                      className="w-12 h-14 bg-white/5 border border-white/10 rounded-xl text-center text-2xl font-black text-white focus:outline-none focus:ring-2 focus:ring-amber-500 transition-all"
                    />
                  ))}
                </div>
                
                {/* Timer & Resend */}
                <div className="flex flex-col items-center gap-3 mt-6">
                  <p className="text-amber-200 text-xs font-bold uppercase tracking-widest">
                    Code expires in: <span className="text-white ml-1 font-black">{formatTime(timer)}</span>
                  </p>
                  <button
                    type="button"
                    onClick={handleSendOtp}
                    disabled={!canResend || isLoading}
                    className={`flex items-center gap-2 text-sm font-black transition-colors ${
                      canResend ? 'text-white hover:text-amber-200' : 'text-white/20 cursor-not-allowed'
                    }`}
                  >
                    <FaSync className={isLoading ? 'animate-spin' : ''} />
                    Resend Code
                  </button>
                </div>
              </div>
              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex justify-center py-4 px-4 border border-transparent rounded-xl shadow-xl text-base font-black text-white bg-gradient-to-r from-amber-700 to-amber-900 hover:from-amber-800 hover:to-amber-950 transition-all transform hover:scale-[1.02] active:scale-[0.98]"
              >
                {isLoading ? "Verifying..." : "Verify OTP"}
              </button>
              <button type="button" onClick={() => setStep('email')} className="w-full text-center text-xs text-amber-200 hover:text-white font-bold transition-colors">
                Use a different email
              </button>
            </form>
          )}

          {step === 'password' && (
            <form className="space-y-6" onSubmit={handleResetPassword}>
              {error && (
                <div className="bg-red-500/10 backdrop-blur-md border border-red-500/20 p-4 rounded-xl mb-4">
                  <p className="text-sm font-bold text-red-100">{error}</p>
                </div>
              )}
              <div className="space-y-4">
                <div>
                  <label htmlFor="pass" className="block text-sm font-black text-white mb-2 uppercase tracking-widest">
                    New Password
                  </label>
                  <div className="mt-1 relative rounded-xl shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <FaLock className="h-5 w-5 text-amber-400" />
                    </div>
                    <input
                      id="pass"
                      type="password"
                      required
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      className="block w-full pl-10 pr-3 py-3 border border-white/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent bg-white/5 text-white placeholder-white/40 transition-all font-medium"
                      placeholder="••••••••"
                    />
                  </div>
                </div>
                <div>
                  <label htmlFor="confirm" className="block text-sm font-black text-white mb-2 uppercase tracking-widest">
                    Confirm Password
                  </label>
                  <div className="mt-1 relative rounded-xl shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <FaLock className="h-5 w-5 text-amber-400" />
                    </div>
                    <input
                      id="confirm"
                      type="password"
                      required
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="block w-full pl-10 pr-3 py-3 border border-white/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent bg-white/5 text-white placeholder-white/40 transition-all font-medium"
                      placeholder="••••••••"
                    />
                  </div>
                </div>
              </div>
              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex justify-center py-4 px-4 border border-transparent rounded-xl shadow-xl text-base font-black text-white bg-gradient-to-r from-amber-700 to-amber-900 hover:from-amber-800 hover:to-amber-950 transition-all transform hover:scale-[1.02] active:scale-[0.98]"
              >
                {isLoading ? "Updating..." : "Update Password"}
              </button>
            </form>
          )}

          {step === 'success' && (
            <div className="text-center py-4">
              <div className="flex justify-center mb-6">
                <div className="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center border border-green-500/30">
                  <FaCheckCircle className="h-10 w-10 text-green-400" />
                </div>
              </div>
              <h3 className="text-2xl font-black text-white mb-4">Reset Successful!</h3>
              <p className="text-amber-100 mb-8 font-medium">Your account security has been updated. You can now log in with your new credentials.</p>
              <Link
                to="/auth"
                className="w-full flex justify-center py-4 px-4 border border-transparent rounded-xl shadow-xl text-base font-black text-white bg-gradient-to-r from-amber-700 to-amber-900 hover:from-amber-800 hover:to-amber-950 transition-all transform hover:scale-[1.02] active:scale-[0.98]"
              >
                Go to Login
              </Link>
            </div>
          )}

          <div className="text-center mt-8">
            <Link
              to="/auth"
              className="text-sm font-black text-white hover:text-amber-200 flex items-center justify-center transition-colors"
            >
              <FaArrowLeft className="mr-2" /> Back to login
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
