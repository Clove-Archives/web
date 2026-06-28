/*
 * Copyright (c) 2026 Clove Twilight
 * Licensed under the ESAL-1.3 Licence.
 * See LICENCE.md in the project root for full licence information.
 */

import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import useTheme from '@/hooks/useTheme';

// Extend Window interface to include turnstile
declare global {
  interface Window {
    turnstile: {
      render: (container: string | HTMLElement, options: {
        sitekey: string;
        callback: (token: string) => void;
        'error-callback'?: () => void;
        'expired-callback'?: () => void;
        theme?: 'light' | 'dark' | 'auto';
        size?: 'normal' | 'compact';
      }) => string;
      reset: (widgetId?: string) => void;
      remove: (widgetId?: string) => void;
    };
  }
}

const SignUp: React.FC = () => {
  const [theme] = useTheme();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [checkingUsername, setCheckingUsername] = useState(false);
  const [turnstileToken, setTurnstileToken] = useState<string | null>(null);
  const [turnstileLoaded, setTurnstileLoaded] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [usernameExists, setUsernameExists] = useState(false);
  
  const navigate = useNavigate();
  const turnstileRef = useRef<HTMLDivElement>(null);
  const widgetId = useRef<string | null>(null);
  const usernameCheckTimeout = useRef<NodeJS.Timeout | null>(null);

  // Load Turnstile script
  useEffect(() => {
    const loadTurnstile = () => {
      if (window.turnstile) {
        setTurnstileLoaded(true);
        return;
      }

      const script = document.createElement('script');
      script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js';
      script.async = true;
      script.defer = true;
      script.onload = () => {
        setTurnstileLoaded(true);
      };
      script.onerror = () => {
        console.error('Failed to load Turnstile script');
        setError('Failed to load security verification. Please refresh the page.');
      };
      
      document.head.appendChild(script);
    };

    loadTurnstile();

    // Cleanup function
    return () => {
      if (widgetId.current && window.turnstile) {
        window.turnstile.remove(widgetId.current);
      }
      if (usernameCheckTimeout.current) {
        clearTimeout(usernameCheckTimeout.current);
      }
    };
  }, []);

  // Render Turnstile widget when loaded
  useEffect(() => {
    if (turnstileLoaded && turnstileRef.current && !widgetId.current) {
      try {
        widgetId.current = window.turnstile.render(turnstileRef.current, {
          sitekey: '0x4AAAAAAB08ZhSxKn5rAD3d',
          callback: (token: string) => {
            setTurnstileToken(token);
            setError(""); // Clear any previous errors
          },
          'error-callback': () => {
            setError('Security verification failed. Please try again.');
            setTurnstileToken(null);
          },
          'expired-callback': () => {
            setError('Security verification expired. Please verify again.');
            setTurnstileToken(null);
          },
          theme: 'auto',
          size: 'normal'
        });
      } catch (err) {
        console.error('Error rendering Turnstile:', err);
        setError('Failed to initialize security verification.');
      }
    }
  }, [turnstileLoaded]);

  // Check if username exists (case-insensitive)
  const checkUsernameExists = async (usernameToCheck: string) => {
    if (!usernameToCheck.trim()) {
      setUsernameExists(false);
      return;
    }

    setCheckingUsername(true);
    
    try {
      // Use GET request with query parameter
      const response = await fetch(`/api/users/check-username?username=${encodeURIComponent(usernameToCheck.trim())}`);

      if (response.ok) {
        const data = await response.json();
        setUsernameExists(data.exists);
      }
    } catch (err) {
      console.error('Error checking username:', err);
      // Don't block signup on check error - fail open
      setUsernameExists(false);
    } finally {
      setCheckingUsername(false);
    }
  };

  // Debounced username check
  useEffect(() => {
    if (usernameCheckTimeout.current) {
      clearTimeout(usernameCheckTimeout.current);
    }

    if (username.trim()) {
      usernameCheckTimeout.current = setTimeout(() => {
        checkUsernameExists(username);
      }, 500);
    } else {
      setUsernameExists(false);
    }

    return () => {
      if (usernameCheckTimeout.current) {
        clearTimeout(usernameCheckTimeout.current);
      }
    };
  }, [username]);

  // Password validation
  const validatePassword = (pass: string): string | null => {
    if (pass.length < 10) {
      return "Password must be at least 10 characters long";
    }
    return null;
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Basic form validation
    if (!username || !password || !confirmPassword) {
      setError("Please fill in all required fields");
      return;
    }

    // Check if username exists (case-insensitive)
    if (usernameExists) {
      setError("This username is already taken");
      return;
    }

    // Password length validation
    const passwordError = validatePassword(password);
    if (passwordError) {
      setError(passwordError);
      return;
    }

    // Password match validation
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    // Check for Turnstile token
    if (!turnstileToken) {
      setError("Please complete the security verification");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const res = await fetch("/api/signup", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: username.trim(),
          password,
          display_name: displayName.trim() || undefined,
          turnstile_token: turnstileToken,
          is_admin: false // Explicitly set to false - users cannot sign up as admins
        }),
      });

      const responseText = await res.text();

      let data;
      try {
        data = JSON.parse(responseText);
      } catch (parseError) {
        console.error('Failed to parse signup response:', parseError);
        throw new Error('Invalid response from server. Please try again.');
      }

      if (res.ok) {
        // Show success message
        setShowSuccess(true);
        
        // Redirect to login after 3 seconds
        setTimeout(() => {
          navigate('/user/login', { replace: true });
        }, 3000);
      } else {
        // Handle signup failure
        const errorMessage = data.detail || data.message || "Signup failed. Please try again.";
        setError(errorMessage);
        
        // Reset Turnstile on signup failure
        if (widgetId.current && window.turnstile) {
          window.turnstile.reset(widgetId.current);
          setTurnstileToken(null);
        }
      }
    } catch (err: any) {
      console.error("Signup error:", err);
      
      let errorMessage = "Network error. Please check your connection and try again.";
      
      if (err.message) {
        errorMessage = err.message;
      } else if (err.toString && err.toString() !== '[object Object]') {
        errorMessage = err.toString();
      }
      
      setError(errorMessage);
      
      // Reset Turnstile on error
      if (widgetId.current && window.turnstile) {
        window.turnstile.reset(widgetId.current);
        setTurnstileToken(null);
      }
    } finally {
      setLoading(false);
    }
  };

  // Show success screen after successful signup
  if (showSuccess) {
    return (
      <div className="max-w-md mx-auto mt-10 p-6 border rounded-lg shadow-lg dark:bg-gray-800 dark:border-gray-700">
        <div className="text-center space-y-6">
          <div className="text-6xl">✅</div>
          <h2 className="text-3xl font-bold font-comic text-primary">
            Account Created!
          </h2>
          <p className="text-xl font-comic">
            Welcome, {displayName || username}!
          </p>
          <div className="bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-100 p-4 rounded-md">
            <p className="font-comic">
              Your account has been successfully created.
            </p>
          </div>
          <div className="flex justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
          <p className="text-sm text-muted-foreground font-comic">
            Redirecting you to login...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto mt-10 p-6 border rounded-lg shadow-lg dark:bg-gray-800 dark:border-gray-700">
      <h2 className="text-2xl font-bold mb-6 text-center font-comic">Create Account</h2>
      
      {error && (
        <div className="bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-100 p-3 rounded-md mb-4">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="flex flex-col space-y-4">
        {/* Username */}
        <div>
          <label htmlFor="username" className="block mb-1 text-sm font-medium font-comic">
            Username *
          </label>
          <input
            id="username"
            type="text"
            placeholder="Choose a username"
            className={`w-full border p-2 rounded dark:bg-gray-700 dark:border-gray-600 font-comic ${
              usernameExists ? 'border-red-500' : ''
            }`}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={loading}
            autoComplete="username"
          />
          {checkingUsername && (
            <p className="text-xs text-gray-500 mt-1 font-comic">Checking availability...</p>
          )}
          {usernameExists && !checkingUsername && (
            <p className="text-xs text-red-500 mt-1 font-comic">This username is already taken</p>
          )}
          {username && !usernameExists && !checkingUsername && (
            <p className="text-xs text-green-500 mt-1 font-comic">Username available!</p>
          )}
        </div>

        {/* Display Name */}
        <div>
          <label htmlFor="displayName" className="block mb-1 text-sm font-medium font-comic">
            Display Name (optional)
          </label>
          <input
            id="displayName"
            type="text"
            placeholder="How should we call you?"
            className="w-full border p-2 rounded dark:bg-gray-700 dark:border-gray-600 font-comic"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            disabled={loading}
            autoComplete="name"
          />
        </div>
        
        {/* Password */}
        <div>
          <label htmlFor="password" className="block mb-1 text-sm font-medium font-comic">
            Password *
          </label>
          <input
            id="password"
            type="password"
            placeholder="Enter your password (min 10 characters)"
            className="w-full border p-2 rounded dark:bg-gray-700 dark:border-gray-600 font-comic"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={loading}
            autoComplete="new-password"
          />
          {password && (
            <p className={`text-xs mt-1 font-comic ${
              password.length >= 10 ? 'text-green-500' : 'text-red-500'
            }`}>
              {password.length}/10 characters minimum
            </p>
          )}
        </div>

        {/* Confirm Password */}
        <div>
          <label htmlFor="confirmPassword" className="block mb-1 text-sm font-medium font-comic">
            Confirm Password *
          </label>
          <input
            id="confirmPassword"
            type="password"
            placeholder="Confirm your password"
            className="w-full border p-2 rounded dark:bg-gray-700 dark:border-gray-600 font-comic"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            disabled={loading}
            autoComplete="new-password"
          />
          {confirmPassword && (
            <p className={`text-xs mt-1 font-comic ${
              password === confirmPassword ? 'text-green-500' : 'text-red-500'
            }`}>
              {password === confirmPassword ? 'Passwords match!' : 'Passwords do not match'}
            </p>
          )}
        </div>

        {/* Turnstile Widget */}
        <div className="flex flex-col space-y-2">
          <label className="block text-sm font-medium font-comic">
            Security Verification *
          </label>
          <div 
            ref={turnstileRef}
            className="flex justify-center"
          />
          {!turnstileLoaded && (
            <div className="text-sm text-gray-500 dark:text-gray-400 text-center font-comic">
              Loading security verification...
            </div>
          )}
        </div>
        
        <button 
          type="submit" 
          className="bg-blue-600 text-white p-2 rounded disabled:bg-blue-300 transition-colors hover:bg-blue-700 font-comic"
          disabled={loading || !turnstileToken || usernameExists || checkingUsername}
        >
          {loading ? "Creating Account..." : "Sign Up"}
        </button>
      </form>

      {/* Login Link */}
      <div className="mt-4 text-center text-sm font-comic">
        Already have an account?{' '}
        <a href="/user/login" className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300">
          Log in here
        </a>
      </div>
      
      {loading && (
        <div className="mt-4 text-center text-sm text-gray-500 font-comic">
          Please wait while we create your account...
        </div>
      )}
    </div>
  );
};

export default SignUp;