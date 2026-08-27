import React, { createContext, useContext, useState, useEffect, useMemo, useCallback } from 'react';

const ThemeContext = createContext(null);

const DEFAULT_THEME = {
  mode: 'light',
  accent: 'orange',
  background: 'cream',
  fontSize: 'medium',
  reduceMotion: false,
};

export const ACCENT_COLORS = {
  orange: { name: 'Sunset', value: '#FF5722', hover: '#E64A19' },
  lavender: { name: 'Lavender', value: '#CDB4DB', hover: '#B896C7' },
  mint: { name: 'Sky', value: '#A2D2FF', hover: '#7FB8EE' },
  butter: { name: 'Butter', value: '#FFC857', hover: '#E6B040' },
  peach: { name: 'Peach', value: '#FF865E', hover: '#E66E48' },
};

export const BACKGROUNDS = {
  cream: { name: 'Cream', light: '#FDFBF7', dark: '#0F0E0C' },
  pure: { name: 'Pure', light: '#FFFFFF', dark: '#000000' },
  warm: { name: 'Warm', light: '#FFF4E6', dark: '#1A1410' },
  cool: { name: 'Cool', light: '#F0F4F8', dark: '#0C1218' },
};

export const FONT_SIZES = {
  small: { name: 'Small', scale: 0.9 },
  medium: { name: 'Medium', scale: 1 },
  large: { name: 'Large', scale: 1.1 },
};

export const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState(() => {
    try {
      const stored = localStorage.getItem('studyai_theme');
      return stored ? { ...DEFAULT_THEME, ...JSON.parse(stored) } : DEFAULT_THEME;
    } catch {
      return DEFAULT_THEME;
    }
  });

  const applyTheme = useCallback((t) => {
    const root = document.documentElement;
    const bg = BACKGROUNDS[t.background];
    const accent = ACCENT_COLORS[t.accent];
    const fontScale = FONT_SIZES[t.fontSize].scale;

    if (t.mode === 'dark') {
      root.style.setProperty('--bg-main', bg.dark);
      root.style.setProperty('--bg-surface', '#1A1A1A');
      root.style.setProperty('--text-main', '#FDFBF7');
      root.style.setProperty('--border-main', '#FDFBF7');
      root.style.setProperty('--shadow-color', '#FDFBF7');
      root.style.setProperty('--muted-bg', '#0A0A0A');
    } else {
      root.style.setProperty('--bg-main', bg.light);
      root.style.setProperty('--bg-surface', '#FFFFFF');
      root.style.setProperty('--text-main', '#0A0A0A');
      root.style.setProperty('--border-main', '#0A0A0A');
      root.style.setProperty('--shadow-color', '#0A0A0A');
      root.style.setProperty('--muted-bg', bg.light);
    }

    root.style.setProperty('--accent', accent.value);
    root.style.setProperty('--accent-hover', accent.hover);
    root.style.setProperty('--font-scale', fontScale);
    root.setAttribute('data-theme', t.mode);
    root.setAttribute('data-reduce-motion', t.reduceMotion ? 'true' : 'false');
  }, []);

  useEffect(() => {
    localStorage.setItem('studyai_theme', JSON.stringify(theme));
    applyTheme(theme);
  }, [theme, applyTheme]);

  const updateTheme = useCallback((updates) => {
    setTheme((prev) => ({ ...prev, ...updates }));
  }, []);

  const resetTheme = useCallback(() => {
    setTheme(DEFAULT_THEME);
  }, []);

  const value = useMemo(
    () => ({ theme, updateTheme, resetTheme }),
    [theme, updateTheme, resetTheme]
  );

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useTheme must be used within ThemeProvider');
  return context;
};

export default ThemeContext;
