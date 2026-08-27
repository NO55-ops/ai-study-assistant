import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { BookOpen, Mail, Lock, User } from 'lucide-react';
import { toast } from 'sonner';

const Login = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
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
      // Check if user needs onboarding
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

        <div
          className="bg-white rounded-2xl border-2 border-[#0A0A0A] neo-shadow p-8"
          data-testid="auth-card"
        >
          <div className="flex gap-2 mb-6">
            <button
              onClick={() => setIsLogin(true)}
              data-testid="login-tab-btn"
              className={`flex-1 py-2 px-4 rounded-xl border-2 border-[#0A0A0A] font-semibold transition-all ${
                isLogin ? 'bg-[#FF5722] text-[#FDFBF7] neo-shadow' : 'bg-white text-[#0A0A0A]'
              }`}
            >
              Login
            </button>
            <button
              onClick={() => setIsLogin(false)}
              data-testid="register-tab-btn"
              className={`flex-1 py-2 px-4 rounded-xl border-2 border-[#0A0A0A] font-semibold transition-all ${
                !isLogin ? 'bg-[#FF5722] text-[#FDFBF7] neo-shadow' : 'bg-white text-[#0A0A0A]'
              }`}
            >
              Sign Up
            </button>
          </div>

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
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-field pl-14"
                  placeholder="••••••••"
                  required
                  data-testid="password-input"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full mt-6"
              data-testid="submit-auth-btn"
            >
              {loading ? 'Please wait...' : isLogin ? 'Login' : 'Create Account'}
            </button>
          </form>
        </div>

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
      </div>
    </div>
  );
};

export default Login;
