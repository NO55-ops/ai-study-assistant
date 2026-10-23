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
    { path: '/dashboard', label: 'Dashboard', description: 'View your study progress and overview.', icon: Home },
    { path: '/documents', label: 'Documents', description: 'Upload and manage your study materials.', icon: FileText },
    { path: '/library', label: 'Library', description: 'Browse a curated collection of study content.', icon: BookOpen },
    { path: '/notes', label: 'Notes', description: 'Create and review study notes.', icon: NotebookPen },
    { path: '/tutor', label: 'AI Tutor', description: 'Ask questions and get help studying.', icon: Brain },
    { path: '/quiz', label: 'Quiz', description: 'Generate and take practice quizzes.', icon: HelpCircle },
    { path: '/flashcards', label: 'Flashcards', description: 'Review and memorise key concepts.', icon: Layers },
    { path: '/settings', label: 'Settings', description: 'Manage your account and preferences.', icon: Settings },
  ];

  return (
    <>
      <nav
        className="hidden md:flex fixed left-0 top-0 z-50 h-screen w-24 flex-col justify-between overflow-visible border-r-2 bg-[var(--bg-main)]/95 backdrop-blur-xl"
        style={{
          background: 'var(--bg-main)',
          borderRight: '2px solid var(--border-main)',
          boxShadow: '4px 0 0 var(--shadow-color)',
          opacity: 0.98,
        }}
        data-testid="navbar"
      >
        <div className="flex flex-col items-center gap-4 p-4 pt-5">
          <Link
            to="/dashboard"
            className="flex flex-col items-center justify-center gap-2 font-black text-xs transition-colors"
            style={{ fontFamily: 'Outfit, sans-serif', color: 'var(--text-main)' }}
            data-testid="nav-logo"
          >
            <div
              className="w-12 h-12 rounded-xl flex items-center justify-center border-2 neo-shadow"
              style={{ background: 'var(--accent)', borderColor: 'var(--border-main)' }}
            >
              <BookOpen className="w-5 h-5" style={{ color: '#FDFBF7' }} strokeWidth={2.5} />
            </div>
            <span className="sr-only">Study AI</span>
          </Link>

          <div className="mt-3 flex w-full flex-col items-center gap-3 overflow-visible">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              const tooltipText = `${item.label} — ${item.description}`;

              return (
                <Link
                  key={item.path}
                  to={item.path}
                  title={tooltipText}
                  aria-label={tooltipText}
                  data-testid={`nav-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
                  className="group relative flex items-center justify-center w-12 h-12 rounded-xl border-2 transition-all duration-200 ease-out overflow-visible focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2"
                  style={{
                    background: isActive ? 'var(--accent)' : 'var(--bg-surface)',
                    color: isActive ? '#FDFBF7' : 'var(--text-main)',
                    borderColor: 'var(--border-main)',
                    boxShadow: isActive ? '4px 4px 0px var(--shadow-color)' : 'none',
                    transform: isActive ? 'translateY(0)' : undefined,
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
                  <span className="sr-only">{item.label}</span>
                  <Icon className="w-5 h-5" strokeWidth={2.5} />

                  <span
                    className="pointer-events-none absolute left-full top-1/2 z-[60] ml-3 -translate-y-1/2 translate-x-1 whitespace-nowrap rounded-xl border-2 px-3 py-2 text-left opacity-0 transition-all duration-200 ease-out group-hover:translate-x-0 group-hover:opacity-100 group-focus-within:translate-x-0 group-focus-within:opacity-100"
                    style={{
                      background: 'var(--bg-surface)',
                      borderColor: 'var(--border-main)',
                      boxShadow: '4px 4px 0px var(--shadow-color)',
                      color: 'var(--text-main)',
                      minWidth: '185px',
                    }}
                  >
                    <span className="block text-[10px] font-black uppercase tracking-[0.08em]">{item.label}</span>
                    <span className="mt-1 block text-[10px] leading-tight opacity-80">{item.description}</span>
                  </span>
                </Link>
              );
            })}
          </div>
        </div>

        <div className="flex flex-col items-center gap-3 p-4 pb-6">
          {user && (
            <div
              className="flex h-10 w-10 items-center justify-center rounded-xl border-2 text-[10px] font-black"
              style={{ background: '#CDB4DB', color: '#0A0A0A', borderColor: 'var(--border-main)' }}
              aria-label={`Signed in as ${user.name}`}
            >
              {user.name?.charAt(0)?.toUpperCase() || 'U'}
            </div>
          )}
          <button
            onClick={handleLogout}
            className="flex items-center justify-center w-12 h-12 rounded-xl border-2 transition-all duration-200 ease-out"
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
            aria-label="Logout"
          >
            <LogOut className="w-4 h-4" strokeWidth={2.5} />
          </button>
        </div>
      </nav>

      <nav
        className="sticky top-0 z-50 backdrop-blur-xl md:hidden"
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

            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg border-2"
              style={{ background: 'var(--bg-surface)', color: 'var(--text-main)', borderColor: 'var(--border-main)' }}
              data-testid="mobile-menu-btn"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>

          {mobileMenuOpen && (
            <div
              className="py-4 space-y-2 border-t-2"
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
    </>
  );
};

export default Navbar;
