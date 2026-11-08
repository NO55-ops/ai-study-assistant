import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { BookOpen, Mail, Lock, User, Eye, EyeOff } from 'lucide-react';
import { toast } from 'sonner';

const Login = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordError, setPasswordError] = useState('');
  const [resetStage, setResetStage] = useState('login');
  const [resetEmail, setResetEmail] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newPasswordConfirm, setNewPasswordConfirm] = useState('');
  const [resetLoading, setResetLoading] = useState(false);
  const [resetMessage, setResetMessage] = useState('');
  const [resetError, setResetError] = useState('');
  const { login, register, requestPasswordReset, confirmPasswordReset } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const mode = searchParams.get('mode');
    const urlToken = searchParams.get('token');
    const urlEmail = searchParams.get('email');

    if (mode === 'reset' && urlToken && urlEmail) {
      setResetStage('confirm');
      setIsLogin(true);
      setResetEmail(urlEmail);
      setResetToken(urlToken);
      setResetError('');
      setResetMessage('Choose a new password to finish resetting your account.');
      return;
    }

    if (resetStage === 'confirm' && !urlToken) {
      setResetToken('');
    }
  }, [searchParams, resetStage]);

  const getPasswordError = (nextPassword, nextConfirmPassword) => {
    if (!nextPassword || !nextConfirmPassword) {
      return 'Passwords do not match.';
    }
    if (nextPassword !== nextConfirmPassword) {
      return 'Passwords do not match.';
    }
    return '';
  };

  const handlePasswordChange = (value) => {
    setPassword(value);
    if (!isLogin) {
      setPasswordError(getPasswordError(value, confirmPassword));
    }
  };

  const handleConfirmPasswordChange = (value) => {
    setConfirmPassword(value);
    if (!isLogin) {
      setPasswordError(getPasswordError(password, value));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!isLogin) {
      if (!password || !confirmPassword || password !== confirmPassword) {
        setPasswordError('Passwords do not match.');
        return;
      }
    }

    setLoading(true);

    let result;
    if (isLogin) {
      result = await login(email, password);
    } else {
      result = await register(name, email, password);
    }

    setLoading(false);

    if (result.success) {
      toast.success(isLogin ? 'Welcome back!' : 'Account created!');
      const userData = result.user || {};
      if (userData.onboarded) {
        navigate('/dashboard');
      } else {
        navigate('/onboarding');
      }
    } else {
      toast.error(result.error);
    }
  };

  const beginPasswordReset = () => {
    setResetStage('request');
    setResetMessage('');
    setResetError('');
    setResetEmail(email || '');
    setResetToken('');
    setNewPassword('');
    setNewPasswordConfirm('');
  };

  const handlePasswordResetRequest = async (e) => {
    e.preventDefault();
    if (!resetEmail.trim()) {
      setResetError('Please enter your email address.');
      return;
    }

    setResetLoading(true);
    setResetError('');
    const result = await requestPasswordReset(resetEmail.trim());
    setResetLoading(false);

    if (!result.success) {
      setResetError(result.error || 'Unable to send a reset email right now.');
      return;
    }

    setResetMessage('Check your email for a secure reset link. Click it to choose a new password.');
    setResetStage('confirm');
    toast.success(result.message || 'If an account exists, a reset link was sent.');
  };

  const handlePasswordResetConfirm = async (e) => {
    e.preventDefault();
    if (!resetEmail.trim()) {
      setResetError('Please enter your email address.');
      return;
    }

    const resolvedToken = (resetToken || searchParams.get('token') || '').trim();
    if (!resolvedToken) {
      setResetError('Please open the secure reset link from your email to continue.');
      return;
    }
    if (newPassword.length < 8) {
      setResetError('New password must be at least 8 characters long.');
      return;
    }
    if (newPassword !== newPasswordConfirm) {
      setResetError('Passwords do not match.');
      return;
    }

    setResetLoading(true);
    setResetError('');
    const result = await confirmPasswordReset(resetEmail.trim(), resolvedToken, newPassword);
    setResetLoading(false);

    if (!result.success) {
      setResetError(result.error || 'Unable to reset the password.');
      return;
    }

    toast.success(result.message || 'Password reset succeeded.');
    setResetStage('login');
    setResetMessage('');
    setResetEmail('');
    setResetToken('');
    setNewPassword('');
    setNewPasswordConfirm('');
    setIsLogin(true);
    setPassword('');
    setConfirmPassword('');
  };

  const resetToLogin = () => {
    setResetStage('login');
    setResetError('');
    setResetMessage('');
    setResetEmail('');
    setResetToken('');
    setNewPassword('');
    setNewPasswordConfirm('');
  };

  const authCardContent = resetStage === 'login' ? (
    <form onSubmit={handleSubmit} className="space-y-4">
      {!isLogin && (
        <div>
          <label className="block text-sm font-semibold text-[#0A0A0A] mb-2" style={{ fontFamily: 'DM Sans, sans-serif' }}>
            NAME
          </label>
          <div className="relative">
            <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#0A0A0A]" />
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="input-field pl-14"
              placeholder="Your name"
              required={!isLogin}
              data-testid="name-input"
            />
          </div>
        </div>
      )}

      <div>
        <label className="block text-sm font-semibold text-[#0A0A0A] mb-2" style={{ fontFamily: 'DM Sans, sans-serif' }}>
          EMAIL
        </label>
        <div className="relative">
          <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#0A0A0A]" />
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="input-field pl-14"
            placeholder="you@example.com"
            required
            data-testid="email-input"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-semibold text-[#0A0A0A] mb-2" style={{ fontFamily: 'DM Sans, sans-serif' }}>
          PASSWORD
        </label>
        <div className="relative">
          <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#0A0A0A]" />
          <input
            type={showPassword ? 'text' : 'password'}
            value={password}
            onChange={(e) => handlePasswordChange(e.target.value)}
            className="input-field pl-14 pr-12"
            placeholder="••••••••"
            required
            autoComplete="new-password"
            data-testid="password-input"
          />
          <button
            type="button"
            aria-label={showPassword ? 'Hide password' : 'Show password'}
            onClick={() => setShowPassword((prev) => !prev)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-[#0A0A0A] hover:opacity-80"
          >
            {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {!isLogin && (
        <div>
          <label className="block text-sm font-semibold text-[#0A0A0A] mb-2" style={{ fontFamily: 'DM Sans, sans-serif' }}>
            Confirm password
          </label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#0A0A0A]" />
            <input
              type={showConfirmPassword ? 'text' : 'password'}
              value={confirmPassword}
              onChange={(e) => handleConfirmPasswordChange(e.target.value)}
              className="input-field pl-14 pr-12"
              placeholder="••••••••"
              required={!isLogin}
              autoComplete="new-password"
              data-testid="register-password-confirm-input"
            />
            <button
              type="button"
              aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
              onClick={() => setShowConfirmPassword((prev) => !prev)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-[#0A0A0A] hover:opacity-80"
            >
              {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
          </div>
          {passwordError && (
            <p className="mt-2 text-sm font-medium text-red-600" role="alert">
              {passwordError}
            </p>
          )}
        </div>
      )}

      <button
        type="submit"
        disabled={loading}
        className="btn-primary w-full mt-6"
        data-testid="submit-auth-btn"
      >
        {loading ? 'Please wait...' : isLogin ? 'Login' : 'Create Account'}
      </button>

      {isLogin && (
        <div className="text-right mt-3">
          <button
            type="button"
            onClick={beginPasswordReset}
            className="text-sm font-semibold underline text-[#0A0A0A] hover:opacity-80"
            data-testid="forgot-password-link"
          >
            Forgot password?
          </button>
        </div>
      )}
    </form>
  ) : (
    <form onSubmit={resetStage === 'request' ? handlePasswordResetRequest : handlePasswordResetConfirm} className="space-y-4">
      <div className="mb-4">
        <h2 className="text-2xl font-black text-[#0A0A0A] tracking-tight" style={{ fontFamily: 'Outfit, sans-serif' }}>
          {resetStage === 'request' ? 'Reset your password' : 'Set a new password'}
        </h2>
      </div>

      {resetMessage && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700" role="status">
          {resetMessage}
        </div>
      )}

      {resetError && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
          {resetError}
        </div>
      )}

      <div>
        <label className="block text-sm font-semibold text-[#0A0A0A] mb-2" style={{ fontFamily: 'DM Sans, sans-serif' }}>
          EMAIL
        </label>
        <div className="relative">
          <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#0A0A0A]" />
          <input
            type="email"
            value={resetEmail}
            onChange={(e) => setResetEmail(e.target.value)}
            className="input-field pl-14"
            placeholder="you@example.com"
            required
            data-testid="reset-email-input"
          />
        </div>
      </div>

      {resetStage === 'confirm' && (
        <>
          {!resetToken && !searchParams.get('token') && (
            <div className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-700" role="status">
              Check your email for the secure reset link. Open it to continue.
            </div>
          )}

          {(resetToken || searchParams.get('token')) && (
            <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
              Secure reset link detected. Set your new password below.
            </div>
          )}

          <div>
            <label className="block text-sm font-semibold text-[#0A0A0A] mb-2" style={{ fontFamily: 'DM Sans, sans-serif' }}>
              NEW PASSWORD
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#0A0A0A]" />
              <input
                type={showPassword ? 'text' : 'password'}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="input-field pl-14 pr-12"
                placeholder="••••••••"
                required
                autoComplete="new-password"
                data-testid="reset-new-password-input"
              />
              <button
                type="button"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                onClick={() => setShowPassword((prev) => !prev)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[#0A0A0A] hover:opacity-80"
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-[#0A0A0A] mb-2" style={{ fontFamily: 'DM Sans, sans-serif' }}>
              CONFIRM NEW PASSWORD
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#0A0A0A]" />
              <input
                type={showConfirmPassword ? 'text' : 'password'}
                value={newPasswordConfirm}
                onChange={(e) => setNewPasswordConfirm(e.target.value)}
                className="input-field pl-14 pr-12"
                placeholder="••••••••"
                required
                autoComplete="new-password"
                data-testid="reset-confirm-password-input"
              />
              <button
                type="button"
                aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                onClick={() => setShowConfirmPassword((prev) => !prev)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[#0A0A0A] hover:opacity-80"
              >
                {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </>
      )}

      <button type="submit" disabled={resetLoading} className="btn-primary w-full mt-6" data-testid="reset-submit-btn">
        {resetLoading ? 'Please wait...' : resetStage === 'request' ? 'Send reset link' : 'Reset password'}
      </button>

      <button
        type="button"
        onClick={resetToLogin}
        className="text-sm font-semibold underline text-[#0A0A0A] hover:opacity-80"
        data-testid="back-to-login-btn"
      >
        Back to login
      </button>
    </form>
  );

  return (
    <div className="min-h-screen flex items-center justify-center px-4 noise-overlay" style={{ background: 'var(--bg-main)' }}>
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-[#FF5722] rounded-2xl border-2 border-[#0A0A0A] neo-shadow mb-4">
            <BookOpen className="w-8 h-8 text-[#FDFBF7]" strokeWidth={2.5} />
          </div>
          <h1 className="text-4xl font-black text-[#0A0A0A] tracking-tight" style={{ fontFamily: 'Outfit, sans-serif' }}>
            AI Study Assistant
          </h1>
          <p className="text-base text-[#0A0A0A] mt-2" style={{ fontFamily: 'DM Sans, sans-serif' }}>
            Transform your learning with AI
          </p>
        </div>

        <div className="bg-white rounded-2xl border-2 border-[#0A0A0A] neo-shadow p-8" data-testid="auth-card">
          {resetStage === 'login' && (
            <div className="flex gap-2 mb-6">
              <button
                onClick={() => {
                  setIsLogin(true);
                  setResetStage('login');
                  setResetError('');
                  setResetMessage('');
                }}
                data-testid="login-tab-btn"
                className={`flex-1 py-2 px-4 rounded-xl border-2 border-[#0A0A0A] font-semibold transition-all ${
                  isLogin ? 'bg-[#FF5722] text-[#FDFBF7] neo-shadow' : 'bg-white text-[#0A0A0A]'
                }`}
              >
                Login
              </button>
              <button
                onClick={() => {
                  setIsLogin(false);
                  setResetStage('login');
                  setResetError('');
                  setResetMessage('');
                }}
                data-testid="register-tab-btn"
                className={`flex-1 py-2 px-4 rounded-xl border-2 border-[#0A0A0A] font-semibold transition-all ${
                  !isLogin ? 'bg-[#FF5722] text-[#FDFBF7] neo-shadow' : 'bg-white text-[#0A0A0A]'
                }`}
              >
                Sign Up
              </button>
            </div>
          )}

          {authCardContent}
        </div>

        {resetStage === 'login' && (
          <p className="text-center text-sm text-[#0A0A0A] mt-6" style={{ fontFamily: 'DM Sans, sans-serif' }}>
            {isLogin ? "Don't have an account? " : 'Already have an account? '}
            <button
              onClick={() => setIsLogin(!isLogin)}
              className="font-semibold underline"
              data-testid="toggle-auth-mode-btn"
            >
              {isLogin ? 'Sign up' : 'Login'}
            </button>
          </p>
        )}
      </div>
    </div>
  );
};

export default Login;
