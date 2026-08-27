import React from 'react';
import { useTheme, ACCENT_COLORS, BACKGROUNDS, FONT_SIZES } from '../context/ThemeContext';
import { Settings as SettingsIcon, Sun, Moon, Palette, Type, Zap, RotateCcw, Check } from 'lucide-react';
import { toast } from 'sonner';

const Settings = () => {
  const { theme, updateTheme, resetTheme } = useTheme();

  const handleReset = () => {
    resetTheme();
    toast.success('Settings reset to defaults');
  };

  return (
    <div className="min-h-screen noise-overlay" style={{ background: 'var(--bg-main)' }}>
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl border-2 neo-shadow mb-4"
            style={{ background: 'var(--accent)', borderColor: 'var(--border-main)' }}>
            <SettingsIcon className="w-8 h-8" style={{ color: '#FDFBF7' }} strokeWidth={2.5} />
          </div>
          <h1 className="text-5xl font-black tracking-tight mb-2" style={{ fontFamily: 'Outfit, sans-serif', color: 'var(--text-main)' }}>
            Settings
          </h1>
          <p className="text-lg" style={{ fontFamily: 'DM Sans, sans-serif', color: 'var(--text-main)' }}>
            Personalize your Study AI experience
          </p>
        </div>

        <div className="space-y-6">
          {/* Theme Mode */}
          <div className="card animate-fade-up stagger-1" data-testid="theme-mode-section">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl border-2 flex items-center justify-center"
                style={{ background: '#FFC857', borderColor: 'var(--border-main)' }}>
                {theme.mode === 'light' ? <Sun className="w-5 h-5" style={{ color: '#0A0A0A' }} strokeWidth={2.5} />
                  : <Moon className="w-5 h-5" style={{ color: '#0A0A0A' }} strokeWidth={2.5} />}
              </div>
              <div>
                <h2 className="text-2xl font-black" style={{ fontFamily: 'Outfit, sans-serif', color: 'var(--text-main)' }}>Appearance</h2>
                <p className="text-sm opacity-70" style={{ color: 'var(--text-main)' }}>Choose your preferred theme</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={() => updateTheme({ mode: 'light' })}
                data-testid="theme-light-btn"
                className={`p-6 rounded-xl border-2 font-semibold transition-all ${
                  theme.mode === 'light' ? 'neo-shadow' : 'hover:-translate-y-1 hover:neo-shadow'
                }`}
                style={{
                  background: theme.mode === 'light' ? 'var(--accent)' : 'var(--bg-surface)',
                  color: theme.mode === 'light' ? '#FDFBF7' : 'var(--text-main)',
                  borderColor: 'var(--border-main)',
                }}
              >
                <Sun className="w-8 h-8 mx-auto mb-2" strokeWidth={2.5} />
                <div>Light Mode</div>
              </button>

              <button
                onClick={() => updateTheme({ mode: 'dark' })}
                data-testid="theme-dark-btn"
                className={`p-6 rounded-xl border-2 font-semibold transition-all ${
                  theme.mode === 'dark' ? 'neo-shadow' : 'hover:-translate-y-1 hover:neo-shadow'
                }`}
                style={{
                  background: theme.mode === 'dark' ? 'var(--accent)' : 'var(--bg-surface)',
                  color: theme.mode === 'dark' ? '#FDFBF7' : 'var(--text-main)',
                  borderColor: 'var(--border-main)',
                }}
              >
                <Moon className="w-8 h-8 mx-auto mb-2" strokeWidth={2.5} />
                <div>Dark Mode</div>
              </button>
            </div>
          </div>

          {/* Accent Color */}
          <div className="card animate-fade-up stagger-2" data-testid="accent-color-section">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl border-2 flex items-center justify-center"
                style={{ background: '#CDB4DB', borderColor: 'var(--border-main)' }}>
                <Palette className="w-5 h-5" style={{ color: '#0A0A0A' }} strokeWidth={2.5} />
              </div>
              <div>
                <h2 className="text-2xl font-black" style={{ fontFamily: 'Outfit, sans-serif', color: 'var(--text-main)' }}>Accent Color</h2>
                <p className="text-sm opacity-70" style={{ color: 'var(--text-main)' }}>Pick your primary color</p>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {Object.entries(ACCENT_COLORS).map(([key, color]) => (
                <button
                  key={key}
                  onClick={() => updateTheme({ accent: key })}
                  data-testid={`accent-${key}-btn`}
                  className={`p-4 rounded-xl border-2 font-semibold transition-all relative ${
                    theme.accent === key ? 'neo-shadow' : 'hover:-translate-y-1 hover:neo-shadow'
                  }`}
                  style={{
                    background: color.value,
                    color: '#0A0A0A',
                    borderColor: 'var(--border-main)',
                  }}
                >
                  {theme.accent === key && (
                    <div className="absolute top-2 right-2 w-6 h-6 rounded-full flex items-center justify-center"
                      style={{ background: '#0A0A0A' }}>
                      <Check className="w-4 h-4" style={{ color: '#FDFBF7' }} strokeWidth={3} />
                    </div>
                  )}
                  <div className="text-sm">{color.name}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Background */}
          <div className="card animate-fade-up stagger-3" data-testid="background-section">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl border-2 flex items-center justify-center"
                style={{ background: '#A2D2FF', borderColor: 'var(--border-main)' }}>
                <div className="w-5 h-5 rounded" style={{ background: '#0A0A0A' }} />
              </div>
              <div>
                <h2 className="text-2xl font-black" style={{ fontFamily: 'Outfit, sans-serif', color: 'var(--text-main)' }}>Background</h2>
                <p className="text-sm opacity-70" style={{ color: 'var(--text-main)' }}>Choose base background tone</p>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {Object.entries(BACKGROUNDS).map(([key, bg]) => (
                <button
                  key={key}
                  onClick={() => updateTheme({ background: key })}
                  data-testid={`bg-${key}-btn`}
                  className={`p-4 rounded-xl border-2 font-semibold transition-all relative ${
                    theme.background === key ? 'neo-shadow' : 'hover:-translate-y-1 hover:neo-shadow'
                  }`}
                  style={{
                    background: theme.mode === 'dark' ? bg.dark : bg.light,
                    color: theme.mode === 'dark' ? '#FDFBF7' : '#0A0A0A',
                    borderColor: 'var(--border-main)',
                  }}
                >
                  {theme.background === key && (
                    <div className="absolute top-2 right-2 w-6 h-6 rounded-full flex items-center justify-center"
                      style={{ background: 'var(--accent)' }}>
                      <Check className="w-4 h-4" style={{ color: '#FDFBF7' }} strokeWidth={3} />
                    </div>
                  )}
                  <div className="text-sm">{bg.name}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Font Size */}
          <div className="card animate-fade-up stagger-4" data-testid="font-size-section">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl border-2 flex items-center justify-center"
                style={{ background: '#FF865E', borderColor: 'var(--border-main)' }}>
                <Type className="w-5 h-5" style={{ color: '#0A0A0A' }} strokeWidth={2.5} />
              </div>
              <div>
                <h2 className="text-2xl font-black" style={{ fontFamily: 'Outfit, sans-serif', color: 'var(--text-main)' }}>Font Size</h2>
                <p className="text-sm opacity-70" style={{ color: 'var(--text-main)' }}>Adjust text size for readability</p>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              {Object.entries(FONT_SIZES).map(([key, size]) => (
                <button
                  key={key}
                  onClick={() => updateTheme({ fontSize: key })}
                  data-testid={`font-${key}-btn`}
                  className={`p-4 rounded-xl border-2 font-semibold transition-all ${
                    theme.fontSize === key ? 'neo-shadow' : 'hover:-translate-y-1 hover:neo-shadow'
                  }`}
                  style={{
                    background: theme.fontSize === key ? 'var(--accent)' : 'var(--bg-surface)',
                    color: theme.fontSize === key ? '#FDFBF7' : 'var(--text-main)',
                    borderColor: 'var(--border-main)',
                    fontSize: `${size.scale}rem`,
                  }}
                >
                  Aa
                  <div className="text-xs mt-1">{size.name}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Motion */}
          <div className="card animate-fade-up stagger-5" data-testid="motion-section">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl border-2 flex items-center justify-center"
                  style={{ background: '#FFC857', borderColor: 'var(--border-main)' }}>
                  <Zap className="w-5 h-5" style={{ color: '#0A0A0A' }} strokeWidth={2.5} />
                </div>
                <div>
                  <h2 className="text-2xl font-black" style={{ fontFamily: 'Outfit, sans-serif', color: 'var(--text-main)' }}>Reduce Motion</h2>
                  <p className="text-sm opacity-70" style={{ color: 'var(--text-main)' }}>Disable animations and transitions</p>
                </div>
              </div>

              <button
                onClick={() => updateTheme({ reduceMotion: !theme.reduceMotion })}
                data-testid="motion-toggle-btn"
                className="w-16 h-9 rounded-full border-2 transition-all relative"
                style={{
                  background: theme.reduceMotion ? 'var(--accent)' : 'var(--bg-surface)',
                  borderColor: 'var(--border-main)',
                  boxShadow: '2px 2px 0px var(--shadow-color)',
                }}
              >
                <div
                  className="w-6 h-6 rounded-full border-2 absolute top-0.5"
                  style={{
                    background: 'var(--bg-main)',
                    borderColor: 'var(--border-main)',
                    left: theme.reduceMotion ? 'calc(100% - 28px)' : '2px',
                    transition: 'left 0.2s ease',
                  }}
                />
              </button>
            </div>
          </div>

          {/* Reset */}
          <div className="flex justify-end pt-4">
            <button
              onClick={handleReset}
              data-testid="reset-settings-btn"
              className="btn-secondary flex items-center gap-2"
            >
              <RotateCcw className="w-4 h-4" strokeWidth={2.5} />
              Reset to Defaults
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
