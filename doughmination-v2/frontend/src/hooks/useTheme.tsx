/*
 * Copyright (c) 2026 Clove Twilight
 * Licensed under the ESAL-1.3 Licence.
 * See LICENCE.md in the project root for full licence information.
 */

import { useEffect, useState } from 'react';

const useTheme = () => {
  const [theme, setTheme] = useState(() => {
    // Check localStorage first, then default to dark theme
    const saved = localStorage.getItem('theme');
    return saved || 'dark';
  });

  useEffect(() => {
    const root = document.documentElement;
    
    // Remove existing theme classes
    root.classList.remove('dark', 'light');
    
    // Apply theme class
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.add('light');
    }
    
    // Store theme in localStorage
    localStorage.setItem('theme', theme);
    
    // Dispatch a custom event to notify theme change
    const event = new CustomEvent('themeChanged', { detail: { theme } });
    document.dispatchEvent(event);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  return [theme, toggleTheme] as const;
};

export default useTheme;