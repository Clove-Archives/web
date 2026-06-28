/*
 * Copyright (c) 2026 Clove Twilight
 * Licensed under the ESAL-1.3 Licence.
 * See LICENCE.md in the project root for full licence information.
 */

import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';

interface ProtectedRouteProps {
  children: React.ReactNode;
  adminRequired?: boolean;
  ownerRequired?: boolean;
  petRequired?: boolean;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  adminRequired = false,
  ownerRequired = false,
  petRequired = false
}) => {
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [isOwner, setIsOwner] = useState(false);
  const [isPet, setIsPet] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token');
      
      if (!token) {
        setIsAuthenticated(false);
        setLoading(false);
        return;
      }

      // Fast-path for mock dev token
      if (token.startsWith('mock-')) {
        setIsAuthenticated(true);
        setIsAdmin(token === 'mock-admin');
        setIsOwner(token === 'mock-owner');
        setIsPet(token === 'mock-pet');
        setLoading(false);
        return;
      }

      try {
        // Check user permissions from the API
        const response = await fetch('/api/auth/is_admin', {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          setIsAuthenticated(true);
          setIsAdmin(!!data.isAdmin);
          setIsOwner(!!data.isOwner);
          setIsPet(!!data.isPet);
        } else {
          setIsAuthenticated(false);
          setIsAdmin(false);
          setIsOwner(false);
          setIsPet(false);
        }
      } catch (error) {
        console.error('Auth check error:', error);
        setIsAuthenticated(false);
        setIsAdmin(false);
        setIsOwner(false);
        setIsPet(false);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  if (loading) {
    return <div className="text-center p-8 font-comic">Verifying access...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/user/login" state={{ from: location }} replace />;
  }

  // Check owner permission (owner has all permissions)
  if (ownerRequired && !isOwner) {
    return (
      <div className="container mx-auto p-6 pt-20">
        <div className="max-w-md mx-auto text-center space-y-4">
          <div className="text-6xl">🔒</div>
          <h1 className="text-2xl font-bold font-comic">Owner Access Required</h1>
          <p className="text-muted-foreground font-comic">
            This area is restricted to system owners only.
          </p>
          <button
            onClick={() => window.history.back()}
            className="text-primary hover:underline font-comic"
          >
            ← Go Back
          </button>
        </div>
      </div>
    );
  }

  // Check admin permission (admin and owner have admin access)
  if (adminRequired && !isAdmin && !isOwner) {
    return (
      <div className="container mx-auto p-6 pt-20">
        <div className="max-w-md mx-auto text-center space-y-4">
          <div className="text-6xl">🔒</div>
          <h1 className="text-2xl font-bold font-comic">Admin Access Required</h1>
          <p className="text-muted-foreground font-comic">
            This area is restricted to administrators only.
          </p>
          <button
            onClick={() => window.history.back()}
            className="text-primary hover:underline font-comic"
          >
            ← Go Back
          </button>
        </div>
      </div>
    );
  }

  // Check pet permission
  if (petRequired && !isPet && !isOwner) {
    return (
      <div className="container mx-auto p-6 pt-20">
        <div className="max-w-md mx-auto text-center space-y-4">
          <div className="text-6xl">🐾</div>
          <h1 className="text-2xl font-bold font-comic">Pet Access Required</h1>
          <p className="text-muted-foreground font-comic">
            This area is restricted to pets only.
          </p>
          <button
            onClick={() => window.history.back()}
            className="text-primary hover:underline font-comic"
          >
            ← Go Back
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

export default ProtectedRoute;