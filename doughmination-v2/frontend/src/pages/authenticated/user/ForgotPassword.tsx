/*
 * Copyright (c) 2026 Clove Twilight
 * Licensed under the ESAL-1.3 Licence.
 * See LICENCE.md in the project root for full licence information.
 */

import React from 'react';
import { Link } from 'react-router-dom';
import useTheme from '@/hooks/useTheme';

const ForgotPassword: React.FC = () => {
  const [theme] = useTheme();

  const contactMethods = [
    {
      icon: '💬',
      name: 'Discord',
      value: '@estrogenhrt',
      label: 'Preferred Method',
      color: 'bg-indigo-100 dark:bg-indigo-900 border-indigo-300 dark:border-indigo-700',
      textColor: 'text-indigo-800 dark:text-indigo-200'
    },
    {
      icon: '📧',
      name: 'Email',
      value: 'clovetwilight3@outlook.com',
      label: 'Email Address',
      color: 'bg-blue-100 dark:bg-blue-900 border-blue-300 dark:border-blue-700',
      textColor: 'text-blue-800 dark:text-blue-200'
    },
    {
      icon: '🐦',
      name: 'Twitter',
      value: '@estrogenhrt',
      label: 'Twitter Handle',
      color: 'bg-sky-100 dark:bg-sky-900 border-sky-300 dark:border-sky-700',
      textColor: 'text-sky-800 dark:text-sky-200'
    }
  ];

  return (
    <div className="max-w-2xl mx-auto mt-10 p-6 border rounded-lg shadow-lg dark:bg-gray-800 dark:border-gray-700">
      {/* Header */}
      <div className="text-center mb-6">
        <h2 className="text-3xl font-bold mb-2 font-comic">Account Recovery</h2>
        <p className="text-muted-foreground font-comic">
          Need help with your username or password?
        </p>
      </div>

      {/* Info Card */}
      <div className="bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-6">
        <div className="flex items-start gap-3">
          <span className="text-2xl">ℹ️</span>
          <div>
            <h3 className="font-semibold text-yellow-800 dark:text-yellow-200 font-comic mb-1">
              Manual Recovery Process
            </h3>
            <p className="text-sm text-yellow-700 dark:text-yellow-300 font-comic">
              Password resets and username changes are currently handled manually. 
              Please contact us through one of the methods below with your account details.
            </p>
          </div>
        </div>
      </div>

      {/* Contact Methods */}
      <div className="space-y-4 mb-6">
        <h3 className="font-semibold text-lg font-comic">Contact Methods</h3>
        
        {contactMethods.map((method, index) => (
          <div
            key={index}
            className={`${method.color} border rounded-lg p-4 transition-transform hover:scale-[1.02]`}
          >
            <div className="flex items-center gap-3">
              <span className="text-3xl">{method.icon}</span>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className={`font-semibold ${method.textColor} font-comic`}>
                    {method.name}
                  </h4>
                  {method.name === 'Discord' && (
                    <span className="text-xs bg-green-500 text-white px-2 py-0.5 rounded-full font-comic">
                      Preferred
                    </span>
                  )}
                </div>
                <p className={`text-sm ${method.textColor} font-mono font-semibold`}>
                  {method.value}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* What to Include */}
      <div className="bg-gray-100 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg p-4 mb-6">
        <h3 className="font-semibold text-lg font-comic mb-3">Please Include:</h3>
        <ul className="space-y-2 text-sm font-comic">
          <li className="flex items-start gap-2">
            <span className="text-green-500 font-bold">✓</span>
            <span>Your current username (if you remember it)</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-green-500 font-bold">✓</span>
            <span>Whether you need a password reset or username change</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-green-500 font-bold">✓</span>
            <span>Any additional details that can help verify your identity</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-green-500 font-bold">✓</span>
            <span>Your preferred contact method for the response</span>
          </li>
        </ul>
      </div>

      {/* Future Notice */}
      <div className="bg-purple-50 dark:bg-purple-900/30 border border-purple-200 dark:border-purple-800 rounded-lg p-4 mb-6">
        <div className="flex items-start gap-3">
          <span className="text-2xl">🚀</span>
          <div>
            <h3 className="font-semibold text-purple-800 dark:text-purple-200 font-comic mb-1">
              Coming Soon
            </h3>
            <p className="text-sm text-purple-700 dark:text-purple-300 font-comic">
              An automated email-based password reset system is planned for the future. 
              This page will be updated to username changes only when that feature is implemented.
            </p>
          </div>
        </div>
      </div>

      {/* Back to Login */}
      <div className="text-center">
        <Link
          to="/user/login"
          className="inline-block bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 transition-colors font-comic"
        >
          ← Back to Login
        </Link>
      </div>

      {/* Additional Help */}
      <div className="mt-6 pt-6 border-t border-gray-300 dark:border-gray-700">
        <p className="text-center text-sm text-muted-foreground font-comic">
          Response time is typically within 24-48 hours
        </p>
      </div>
    </div>
  );
};

export default ForgotPassword;