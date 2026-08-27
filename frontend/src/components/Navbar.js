import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { BookOpen, Home, FileText, Brain, HelpCircle, Layers, LogOut, Menu, X, Settings, NotebookPen } from 'lucide-react';
import { useState } from 'react';

const Navbar = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: Home },
    { path: '/documents', label: 'Documents', icon: FileText },
    { path: '/notes', label: 'Notes', icon: NotebookPen },
    { path: '/tutor', label: 'AI Tutor', icon: Brain },
    { path: '/quiz', label: 'Quiz', icon: HelpCircle },
    { path: '/flashcards', label: 'Flashcards', icon: Layers },
    { path: '/settings', label: 'Settings', icon: Settings },
  ];

  return (
    <nav
      className="sticky top-0 z-50 backdrop-blur-xl"
      style={{
        background: 'var(--bg-main)',
        borderBottom: '2px solid var(--border-main)',
        opacity: 0.98,
      }}
      data-testid="navbar"
    >
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link
            to="/dashboard"
            className="flex items-center gap-2 font-black text-xl transition-colors"
            style={{ fontFamily: 'Outfit, sans-serif', color: 'var(--text-main)' }}
            data-testid="nav-logo"
          >
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center border-2 neo-shadow"
              style={{ background: 'var(--accent)', borderColor: 'var(--border-main)' }}
            >
              <BookOpen className="w-5 h-5" style={{ color: '#FDFBF7' }} strokeWidth={2.5} />
            </div>
            Study AI
          </Link>

          <div className="hidden md:flex items-center gap-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  data-testid={`nav-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl border-2 font-semibold text-sm transition-all"
                  style={{
                    background: isActive ? 'var(--accent)' : 'var(--bg-surface)',
                    color: isActive ? '#FDFBF7' : 'var(--text-main)',
                    borderColor: 'var(--border-main)',
                    boxShadow: isActive ? '4px 4px 0px var(--shadow-color)' : 'none',
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.transform = 'translateY(-2px)';
                      e.currentTarget.style.boxShadow = '4px 4px 0px var(--shadow-color)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.transform = 'translateY(0)';
                      e.currentTarget.style.boxShadow = 'none';
                    }
                  }}
                >
                  <Icon className="w-4 h-4" strokeWidth={2.5} />
                  {item.label}
                </Link>
              );
            })}
          </div>

          <div className="hidden md:flex items-center gap-3">
            {user && (
              <div
                className="px-4 py-2 rounded-xl border-2 font-semibold text-sm"
                style={{ background: '#CDB4DB', color: '#0A0A0A', borderColor: 'var(--border-main)' }}
              >
                {user.name}
              </div>
            )}
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-4 py-2 rounded-xl border-2 font-semibold text-sm transition-all"
              style={{ background: '#FF865E', color: '#0A0A0A', borderColor: 'var(--border-main)' }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '4px 4px 0px var(--shadow-color)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}
              data-testid="logout-btn"
            >
              <LogOut className="w-4 h-4" strokeWidth={2.5} />
              Logout
            </button>
          </div>

          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-lg border-2"
            style={{ background: 'var(--bg-surface)', color: 'var(--text-main)', borderColor: 'var(--border-main)' }}
            data-testid="mobile-menu-btn"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {mobileMenuOpen && (
          <div
            className="md:hidden py-4 space-y-2 border-t-2"
            style={{ borderColor: 'var(--border-main)' }}
            data-testid="mobile-menu"
          >
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center gap-2 px-4 py-3 rounded-xl border-2 font-semibold"
                  style={{
                    background: isActive ? 'var(--accent)' : 'var(--bg-surface)',
                    color: isActive ? '#FDFBF7' : 'var(--text-main)',
                    borderColor: 'var(--border-main)',
                  }}
                >
                  <Icon className="w-5 h-5" strokeWidth={2.5} />
                  {item.label}
                </Link>
              );
            })}
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-2 px-4 py-3 rounded-xl border-2 font-semibold"
              style={{ background: '#FF865E', color: '#0A0A0A', borderColor: 'var(--border-main)' }}
            >
              <LogOut className="w-5 h-5" strokeWidth={2.5} />
              Logout
            </button>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
