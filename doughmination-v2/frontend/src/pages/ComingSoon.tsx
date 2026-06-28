/*
 * Copyright (c) 2026 Clove Twilight
 * Licensed under the ESAL-1.3 Licence.
 * See LICENCE.md in the project root for full licence information.
 */

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import useTheme from '@/hooks/useTheme';

interface ComingSoonProps {
  title?: string;
  description?: string;
  icon?: string;
  showBackButton?: boolean;
}

const ComingSoon: React.FC<ComingSoonProps> = ({
  title,
  description,
  icon = '🚧',
  showBackButton = true
}) => {
  const [theme] = useTheme();
  const location = useLocation();

  // Default title based on route
  const getDefaultTitle = () => {
    if (title) return title;
    
    const path = location.pathname;
    if (path.includes('/pet')) return 'Pet Dashboard';
    if (path.includes('/owner')) return 'Owner Features';
    if (path.includes('/admin')) return 'Admin Feature';
    if (path.includes('/user')) return 'User Feature';
    
    return 'New Feature';
  };

  // Default description
  const getDefaultDescription = () => {
    if (description) return description;
    return "We're working hard to bring you this feature. Check back soon!";
  };

  return (
    <div className="min-h-screen bg-background text-foreground theme-transition flex items-center justify-center p-6">
      <div className="max-w-2xl w-full">
        <Card className="border-2">
          <CardHeader className="text-center space-y-6 pb-4">
            {/* Animated Icon */}
            <div className="flex justify-center">
              <div className="text-8xl animate-bounce">
                {icon}
              </div>
            </div>
            
            {/* Title */}
            <div className="space-y-2">
              <CardTitle className="text-4xl font-bold font-comic text-primary">
                {getDefaultTitle()}
              </CardTitle>
              <CardDescription className="text-xl font-comic">
                Coming Soon
              </CardDescription>
            </div>
          </CardHeader>

          <CardContent className="space-y-8">
            {/* Description */}
            <p className="text-center text-muted-foreground font-comic text-lg">
              {getDefaultDescription()}
            </p>

            {/* Progress Indicator */}
            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm font-comic">
                <span className="text-muted-foreground">Development Progress</span>
                <span className="text-primary font-semibold">In Progress...</span>
              </div>
              <div className="w-full bg-muted rounded-full h-3 overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-primary to-accent rounded-full animate-pulse"
                  style={{ width: '35%' }}
                />
              </div>
            </div>

            {/* Feature Highlights */}
            <div className="bg-muted/50 rounded-lg p-6 space-y-4">
              <h3 className="font-comic font-semibold text-lg text-center">
                What to Expect
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="flex items-start gap-2">
                  <span className="text-xl">✨</span>
                  <span className="text-sm font-comic text-muted-foreground">
                    New features and functionality
                  </span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-xl">🎨</span>
                  <span className="text-sm font-comic text-muted-foreground">
                    Beautiful, intuitive design
                  </span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-xl">⚡</span>
                  <span className="text-sm font-comic text-muted-foreground">
                    Fast and responsive
                  </span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-xl">🔒</span>
                  <span className="text-sm font-comic text-muted-foreground">
                    Secure and reliable
                  </span>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              {showBackButton && (
                <Button variant="outline" size="lg" asChild className="font-comic">
                  <Link to="/">
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                    </svg>
                    Back to Home
                  </Link>
                </Button>
              )}
              
              <Button size="lg" asChild className="font-comic">
                <a 
                  href="https://github.com/CloveTwilight3/docker/issues" 
                  target="_blank" 
                  rel="noopener noreferrer"
                >
                  <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 0C4.477 0 0 4.484 0 10.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0110 4.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.203 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.942.359.31.678.921.678 1.856 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0020 10.017C20 4.484 15.522 0 10 0z" clipRule="evenodd" />
                  </svg>
                  Request Feature
                </a>
              </Button>
            </div>

            {/* Additional Info */}
            <div className="text-center pt-6 border-t border-border">
              <p className="text-sm text-muted-foreground font-comic">
                Want to stay updated?{' '}
                <a 
                  href="https://doughmination.co.uk" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-primary hover:underline font-semibold"
                >
                  Visit the Homepage
                </a>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ComingSoon;