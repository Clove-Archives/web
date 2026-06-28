/*
 * Copyright (c) 2026 Clove Twilight
 * Licensed under the ESAL-1.3 Licence.
 * See LICENCE.md in the project root for full licence information.
 */

import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import ThemeToggle from '@/components/ThemeToggle';
import useTheme from '@/hooks/useTheme';
import { Button } from '@/components/ui/button';
import MemberStatus from '@/components/MemberStatus';

// Define interfaces for type safety
interface Member {
  id: number;
  name: string;
  display_name?: string;
  avatar_url?: string;
  pronouns?: string;
  color?: string | null;
  tags?: string[];
  status?: {
    text: string;
    emoji?: string;
    updated_at: string;
  } | null;
}

interface Fronting {
  members: Member[];
}

interface SystemInfo {
  mental_state?: MentalState;
}

interface MentalState {
  level: string;
  notes?: string;
  updated_at: string;
}

interface UserData {
  username: string;
  display_name?: string;
}

export default function Index() {
  const [theme] = useTheme();
  const navigate = useNavigate();

  // State management
  const [members, setMembers] = useState<Member[]>([]);
  const [fronting, setFronting] = useState<Fronting | null>(null);
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [loggedIn, setLoggedIn] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [currentUser, setCurrentUser] = useState<UserData | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentTagFilter, setCurrentTagFilter] = useState<string | null>(null);
  const [filteredMembers, setFilteredMembers] = useState<Member[]>([]);
  const [availableTags, setAvailableTags] = useState<string[]>([]);
  const [wsConnected, setWsConnected] = useState(false);

  // WebSocket connection with improved reconnection logic
  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimeout: NodeJS.Timeout | null = null;
    let heartbeatInterval: NodeJS.Timeout | null = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 10;

    const connectWebSocket = () => {
      try {
        // Clear any existing connection
        if (ws) {
          ws.close();
          ws = null;
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        console.log('🔌 Connecting to WebSocket:', wsUrl);
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          console.log('✅ WebSocket connected');
          setWsConnected(true);
          reconnectAttempts = 0;

          // Send initial subscription message
          ws!.send('subscribe');

          // Clear any existing heartbeat
          if (heartbeatInterval) {
            clearInterval(heartbeatInterval);
          }

          // Send heartbeat every 25 seconds (before typical 30s timeout)
          heartbeatInterval = setInterval(() => {
            if (ws?.readyState === WebSocket.OPEN) {
              console.log('💓 Sending heartbeat ping');
              ws.send('ping');
            }
          }, 25000);
        };

        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            console.log('📩 WebSocket message received:', message.type);

            switch (message.type) {
              case 'connection_established':
                console.log('✅ Connection established:', message.message);
                break;

              case 'subscribed':
                console.log('✅ Subscribed to updates');
                break;

              case 'keepalive':
                console.log('💓 Keepalive received');
                break;

              case 'fronting_update':
                console.log('👥 Fronting update received');
                setFronting(message.data);
                break;

              case 'mental_state_update':
                console.log('🧠 Mental state update received');
                setSystemInfo(prev => prev ? { ...prev, mental_state: message.data } : null);
                break;

              case 'members_update':
                console.log('📋 Members update received');
                if (message.data?.members) {
                  const sortedMembers = [...message.data.members].sort((a: Member, b: Member) => {
                    const nameA = (a.display_name || a.name).toLowerCase();
                    const nameB = (b.display_name || b.name).toLowerCase();
                    return nameA.localeCompare(nameB);
                  });
                  setMembers(sortedMembers);

                  // Update tags
                  const tags = new Set<string>();
                  sortedMembers.forEach((member: Member) => {
                    member.tags?.forEach(tag => tags.add(tag));
                  });
                  setAvailableTags(Array.from(tags).sort((a, b) => a.localeCompare(b)));
                }
                break;

              case 'force_refresh':
                console.log('🔄 Force refresh received from admin');
                window.location.reload();
                break;

              default:
                console.log('❓ Unknown message type:', message.type);
            }
          } catch (err) {
            // Handle non-JSON messages (like "pong")
            if (event.data === 'pong') {
              console.log('💓 Received pong');
            } else {
              console.error('❌ Error parsing WebSocket message:', err);
            }
          }
        };

        ws.onerror = (error) => {
          console.error('❌ WebSocket error:', error);
          setWsConnected(false);
        };

        ws.onclose = (event) => {
          console.log('🔌 WebSocket disconnected. Code:', event.code, 'Reason:', event.reason || 'No reason provided');
          setWsConnected(false);

          // Clear heartbeat
          if (heartbeatInterval) {
            clearInterval(heartbeatInterval);
            heartbeatInterval = null;
          }

          // Attempt to reconnect with exponential backoff
          if (reconnectAttempts < maxReconnectAttempts) {
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
            console.log(`🔄 Reconnecting in ${delay}ms (attempt ${reconnectAttempts + 1}/${maxReconnectAttempts})`);
            
            reconnectTimeout = setTimeout(() => {
              reconnectAttempts++;
              connectWebSocket();
            }, delay);
          } else {
            console.error('❌ Max reconnection attempts reached. Please refresh the page.');
          }
        };
      } catch (err) {
        console.error('❌ Error creating WebSocket:', err);
        setWsConnected(false);
      }
    };

    connectWebSocket();

    // Cleanup on unmount
    return () => {
      console.log('🧹 Cleaning up WebSocket connection');
      if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
      }
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      if (ws) {
        ws.close();
      }
    };
  }, []);

  // Initialize app data
  useEffect(() => {
    initialize();
  }, []);

  const initialize = async () => {
    setLoading(true);
    try {
      // Check authentication status
      await checkAuthStatus();

      // Fetch public data
      await Promise.all([
        fetchMembers(),
        fetchFronting(),
        fetchSystemInfo()
      ]);
    } catch (error) {
      console.error('Initialization error:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkAuthStatus = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      setLoggedIn(false);
      setIsAdmin(false);
      setCurrentUser(null);
      return;
    }

    // Fast-path for mock dev token
    if (token.startsWith('mock-')) {
      setLoggedIn(true);
      setIsAdmin(token === 'mock-admin');
      setCurrentUser({ username: 'mock-user', display_name: 'Mock User' });
      return;
    }

    try {
      const response = await fetch("/api/auth/is_admin", {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setLoggedIn(true);
        setIsAdmin(!!data.isAdmin);

        // Fetch user info
        const userResponse = await fetch("/api/user_info", {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });

        if (userResponse.ok) {
          const userData = await userResponse.json();
          setCurrentUser({
            username: userData.username,
            display_name: userData.display_name
          });
        }
      } else {
        setLoggedIn(false);
        setIsAdmin(false);
        setCurrentUser(null);
      }
    } catch (error) {
      console.error('Auth check error:', error);
      setLoggedIn(false);
      setIsAdmin(false);
      setCurrentUser(null);
    }
  };

  const fetchMembers = async () => {
    try {
      const response = await fetch("/api/members");
      if (response.ok) {
        const data = await response.json();

        // Sort members alphabetically by display name or name
        const sortedMembers = [...data].sort((a: Member, b: Member) => {
          const nameA = (a.display_name || a.name).toLowerCase();
          const nameB = (b.display_name || b.name).toLowerCase();
          return nameA.localeCompare(nameB);
        });

        setMembers(sortedMembers);

        // Extract unique tags and sort alphabetically
        const tags = new Set<string>();
        sortedMembers.forEach((member: Member) => {
          member.tags?.forEach(tag => tags.add(tag));
        });
        setAvailableTags(Array.from(tags).sort((a, b) => a.localeCompare(b)));
      }
    } catch (error) {
      console.error('Error fetching members:', error);
    }
  };

  const fetchFronting = async () => {
    try {
      const response = await fetch("/api/fronters");
      if (response.ok) {
        const data = await response.json();
        setFronting(data);
      }
    } catch (error) {
      console.error('Error fetching fronting:', error);
    }
  };

  const fetchSystemInfo = async () => {
    try {
      const response = await fetch("/api/system");
      if (response.ok) {
        const data = await response.json();
        setSystemInfo(data);
      }
    } catch (error) {
      console.error('Error fetching system info:', error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setLoggedIn(false);
    setIsAdmin(false);
    setCurrentUser(null);
    navigate('/');
  };

  // Event handlers
  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  }, []);

  const clearSearch = useCallback(() => {
    setSearchQuery('');
  }, []);

  const handleTagFilterChange = useCallback((filter: string | null) => {
    setCurrentTagFilter(filter);
  }, []);

  const toggleMenu = useCallback(() => {
    setMenuOpen(prev => !prev);
  }, []);

  // Filter members based on search and tag filter
  useEffect(() => {
    let filtered = members;

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(member =>
        (member.display_name || member.name).toLowerCase().includes(searchQuery.toLowerCase()) ||
        member.tags?.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
      );
    }

    // Apply tag filter
    if (currentTagFilter) {
      if (currentTagFilter === 'untagged') {
        filtered = filtered.filter(member => !member.tags || member.tags.length === 0);
      } else {
        filtered = filtered.filter(member =>
          member.tags?.includes(currentTagFilter)
        );
      }
    }

    setFilteredMembers(filtered);
  }, [members, searchQuery, currentTagFilter]);

  // Check if a member is currently fronting
  const isMemberFronting = useCallback((memberId: number, memberName: string): boolean => {
    if (!fronting?.members || fronting.members.length === 0) {
      return false;
    }

    // Check direct fronting
    return fronting.members.some(m => m.id === memberId || m.name === memberName);
  }, [fronting]);

  // Helper function to normalize color values from PluralKit
  const normalizeColor = (color: string | null | undefined): string | null => {
    if (!color) return null;
    // If it's already got a #, return as-is
    if (color.startsWith('#')) return color;
    // Add # prefix to hex colors from PluralKit
    return `#${color}`;
  };

  // Mental state helper functions
  const getMentalStateLabel = (level: string) => {
    const labels: { [key: string]: string } = {
      'safe': 'Safe',
      'unstable': 'Unstable',
      'idealizing': 'Idealizing',
      'self-harming': 'Self-Harming',
      'highly at risk': 'Highly At Risk'
    };
    return labels[level] || level;
  };

  const getMentalStateIcon = (level: string) => {
    const icons: { [key: string]: string } = {
      'safe': '✅',
      'unstable': '⚠️',
      'idealizing': '❗',
      'self-harming': '🚨',
      'highly at risk': '⛔'
    };
    return icons[level] || '❓';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-2xl font-comic text-foreground">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground theme-transition">
      {/* WebSocket Connection Indicator */}
      {!wsConnected && (
        <div className="fixed top-0 left-0 right-0 z-50 bg-yellow-500 text-black text-center py-2 text-sm font-comic">
          ⚠️ Live updates disconnected. Reconnecting...
        </div>
      )}

      {/* Header with navigation */}
      <header className="fixed top-0 left-0 w-full z-40 bg-card/90 backdrop-blur-sm border-b border-border theme-transition">
        <div className="container mx-auto px-4 py-3 flex justify-between items-center">
          <Link
            to="/"
            className="text-2xl font-bold font-comic text-primary hover:text-primary/80 transition-colors"
          >
            Doughmination System®
          </Link>

          {/* Desktop Navigation */}
          <div className="desktop-nav hidden md:flex items-center gap-3">
            {loggedIn && currentUser && (
              <div className="text-sm font-comic text-muted-foreground mr-2">
                Logged in as: <span className="text-foreground font-semibold">{currentUser.display_name || currentUser.username}</span>
              </div>
            )}
            <ThemeToggle />
            <Button variant="outline" size="sm" asChild>
              <a
                href="https://doughmination.co.uk"
                target="_blank"
                rel="noopener noreferrer"
                className="font-comic"
              >
                Homepage
              </a>
            </Button>
            {loggedIn ? (
              <>
                {isAdmin && (
                  <Button variant="outline" size="sm" asChild>
                    <Link to="/admin/dash" className="font-comic">
                      Admin Panel
                    </Link>
                  </Button>
                )}
                <Button variant='outline' size='sm' asChild>
                  <Link to="/user/metrics" className='font-comic'>
                    Metrics
                  </Link>
                </Button>
                <Button variant="outline" size="sm" asChild>
                  <Link to="/user/profile" className="font-comic">
                    Profile
                  </Link>
                </Button>
                <Button variant="destructive" size="sm" onClick={handleLogout} className="font-comic">
                  Logout
                </Button>
              </>
            ) : (
              <>
                <Button variant='outline' size='sm' asChild>
                  <Link to="/user/signup" className='font-comic'>
                    Sign Up
                  </Link>
                </Button>
                <Button variant="outline" size="sm" asChild>
                  <Link to="/user/login" className="font-comic">
                    Login
                  </Link>
                </Button>
              </>
            )}
          </div>

          {/* Mobile menu button */}
          <button
            className="flex md:hidden items-center justify-center p-2 rounded-md bg-secondary text-secondary-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
            onClick={toggleMenu}
            aria-label="Toggle menu"
            aria-expanded={menuOpen}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {menuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>

        {/* Mobile Navigation overlay */}
        {menuOpen && (
          <div className="mobile-menu-overlay fixed inset-0 z-30 bg-black/50 md:hidden" onClick={toggleMenu}>
            <div
              className="absolute right-0 top-[61px] w-64 max-w-[80vw] h-screen shadow-lg bg-card/95 backdrop-blur-sm border-l border-border"
              onClick={(e) => e.stopPropagation()}
            >
              <ul className="flex flex-col p-4 gap-3">
                {loggedIn && currentUser && (
                  <li className="px-4 py-2 text-sm font-comic text-muted-foreground border-b border-border">
                    Logged in as: <span className="text-foreground font-semibold block mt-1">{currentUser.display_name || currentUser.username}</span>
                  </li>
                )}
                <li>
                  <a
                    href="https://doughmination.co.uk"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block w-full px-4 py-3 rounded-lg text-sm text-center transition-all font-comic bg-primary text-primary-foreground hover:bg-primary/80"
                    onClick={toggleMenu}
                  >
                    Homepage
                  </a>
                </li>
                {loggedIn ? (
                  <>
                    {isAdmin && (
                      <li>
                        <Link
                          to="/admin/dash"
                          className="block w-full px-4 py-3 rounded-lg text-sm text-center transition-all font-comic bg-secondary text-secondary-foreground hover:bg-accent hover:text-accent-foreground"
                          onClick={toggleMenu}
                        >
                          Admin Panel
                        </Link>
                      </li>
                    )}
                    <li>
                      <Link
                        to="/user/metrics"
                        className="block w-full px-4 py-3 rounded-lg text-sm text-center transition-all font-comic bg-secondary text-secondary-foreground hover:bg-accent hover:text-accent-foreground"
                        onClick={toggleMenu}
                      >
                        Metrics
                      </Link>
                    </li>
                    <li>
                      <Link
                        to="/user/profile"
                        className="block w-full px-4 py-3 rounded-lg text-sm text-center transition-all font-comic bg-secondary text-secondary-foreground hover:bg-accent hover:text-accent-foreground"
                        onClick={toggleMenu}
                      >
                        Profile
                      </Link>
                    </li>
                    <li>
                      <button
                        onClick={() => {
                          handleLogout();
                          toggleMenu();
                        }}
                        className="w-full px-4 py-3 bg-destructive text-destructive-foreground rounded-lg text-sm text-center hover:bg-destructive/80 transition-colors font-comic"
                      >
                        Logout
                      </button>
                    </li>
                  </>
                ) : (
                  <li>
                    <Link
                      to="/user/login"
                      className="block w-full px-4 py-3 rounded-lg text-sm text-center transition-all font-comic bg-secondary text-secondary-foreground hover:bg-accent hover:text-accent-foreground"
                      onClick={toggleMenu}
                    >
                      Login
                    </Link>
                  </li>
                )}
              </ul>
            </div>
          </div>
        )}
      </header>

      {/* Space for fixed header */}
      <div className="h-20"></div>

      {/* Main content */}
      <main className="container mx-auto px-2 sm:px-4 pt-4 flex-grow">
        <div className="flex">
          <div className="flex-1">
            <div className="content-wrapper flex flex-col gap-2 sm:gap-4">
              <div className="mt-2">
                <h1 className="text-4xl font-bold mb-8 text-center font-comic text-primary">
                  System Members
                </h1>

                {/* Mental State Banner */}
                {systemInfo?.mental_state && (
                  <div className={`mental-state-banner ${systemInfo.mental_state.level.replace(' ', '-')} mb-6 p-4 rounded-lg`}>
                    <div className="flex items-center justify-center gap-3">
                      <span className="mental-state-icon text-2xl">
                        {getMentalStateIcon(systemInfo.mental_state.level)}
                      </span>
                      <div>
                        <span className="mental-state-label font-comic">Current Status: </span>
                        <span className="mental-state-level font-comic font-bold">
                          {getMentalStateLabel(systemInfo.mental_state.level)}
                        </span>
                        {systemInfo.mental_state.notes && (
                          <p className="mental-state-notes mt-2 font-comic text-sm opacity-80">
                            {systemInfo.mental_state.notes}
                          </p>
                        )}
                      </div>
                    </div>
                    <small className="mental-state-updated block mt-2 opacity-75 text-center font-comic">
                      Last updated: {new Date(systemInfo.mental_state.updated_at).toLocaleString()}
                    </small>
                  </div>
                )}

                {/* Currently Fronting Section */}
                {fronting && fronting.members && fronting.members.length > 0 && (
                  <div className="mb-6 p-4 border-b border-border">
                    <h2 className="text-xl font-comic mb-3 text-center">
                      Currently {fronting.members.length > 1 ? 'Co-fronting' : 'Fronting'}
                    </h2>
                    <div className="flex flex-wrap gap-4 justify-center">
                      {fronting.members.map((member, index) => {
                        const memberColor = normalizeColor((member as any).color);
                        const borderColor = memberColor || 'rgb(var(--primary))';
                        
                        return (
                          <div key={member.id || `${member.name}-${index}`} className="flex flex-col items-center relative">
                            {/* Status Bubble - Thought Bubble Style */}
                            {member.status && (
                              <div className="absolute -top-10 left-1/2 transform -translate-x-1/2 z-20">
                                <div className="relative bg-card border-2 border-border rounded-[30px] px-3 py-1.5 shadow-lg max-w-[140px]">
                                  <div className="flex items-center gap-1.5">
                                    {member.status.emoji && <span className="text-sm">{member.status.emoji}</span>}
                                    <span className="text-xs font-comic text-foreground truncate">{member.status.text}</span>
                                  </div>
                                  {/* Thought bubble circles - staggered diagonally toward avatar */}
                                  <div className="absolute -bottom-5 left-1/2 transform -translate-x-1/2 translate-x-2">
                                    <div className="w-2.5 h-2.5 bg-card border-2 border-border rounded-full shadow-md"></div>
                                  </div>
                                  <div className="absolute -bottom-7 left-1/2 transform -translate-x-1/2 translate-x-3">
                                    <div className="w-1.5 h-1.5 bg-card border border-border rounded-full shadow-sm"></div>
                                  </div>
                                </div>
                              </div>
                            )}
                            <Link to={`/${member.name}`}>
                              <div className="relative">
                                <img
                                  src={member.avatar_url || 'https://c.stupid.cat/assets/favicon/avatar.png'}
                                  alt={member.display_name || member.name}
                                  className="w-16 h-16 rounded-full object-cover border-[3px] transition-all cursor-pointer hover:scale-105"
                                  style={{
                                    borderColor: borderColor,
                                    boxShadow: `0 0 12px ${borderColor}40`
                                  }}
                                  loading="lazy"
                                  onError={(e) => {
                                    (e.target as HTMLImageElement).src = 'https://c.stupid.cat/assets/favicon/avatar.png';
                                  }}
                                />
                              </div>
                            </Link>
                            <div className="mt-2 text-center max-w-[120px]">
                              <Link
                                to={`/${member.name}`}
                                className="font-comic font-semibold text-sm transition-colors block"
                                style={{
                                  color: memberColor || 'rgb(var(--primary))'
                                }}
                              >
                                {member.display_name || member.name || "Unknown"}
                              </Link>

                              {member.tags && member.tags.length > 0 && (
                                <div className="flex flex-wrap gap-1 mt-1 justify-center">
                                  {[...member.tags].sort((a, b) => a.localeCompare(b)).map((tag, tagIndex) => (
                                    <span
                                      key={tagIndex}
                                      className="text-xs px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground font-comic"
                                    >
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Search and Filter */}
                <div className="mb-6 space-y-4">
                  <div className="flex flex-wrap gap-2 justify-center">
                    <button
                      onClick={() => handleTagFilterChange(null)}
                      className={`filter-button ${currentTagFilter === null ? 'active' : ''}`}
                    >
                      All Members
                    </button>
                    {availableTags.map((tag) => (
                      <button
                        key={tag}
                        onClick={() => handleTagFilterChange(tag)}
                        className={`filter-button ${currentTagFilter === tag ? 'active' : ''}`}
                      >
                        {tag}
                      </button>
                    ))}
                    <button
                      onClick={() => handleTagFilterChange('untagged')}
                      className={`filter-button ${currentTagFilter === 'untagged' ? 'active' : ''}`}
                    >
                      Untagged
                    </button>
                  </div>

                  <div className="search-container">
                    <div className="relative">
                      <svg className="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                      </svg>
                      <input
                        id="member-search"
                        type="text"
                        placeholder="Search members..."
                        value={searchQuery}
                        onChange={handleSearchChange}
                        className="search-input"
                      />
                      {searchQuery && (
                        <button
                          onClick={clearSearch}
                          className="search-clear"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      )}
                    </div>
                  </div>
                </div>

                {/* Members Grid */}
                {filteredMembers.length > 0 ? (
                  <div className="member-grid" style={{ paddingTop: '3rem' }}>
                    {filteredMembers.map((member) => {
                      const isFronting = isMemberFronting(member.id, member.name);
                      const memberColor = normalizeColor((member as any).color);
                      const borderColor = memberColor || 'rgb(var(--primary))';
                      
                      return (
                        <div 
                          key={member.id} 
                          className={`member-grid-item ${isFronting ? 'fronting-glow' : ''} relative`}
                          style={{
                            '--member-color': borderColor,
                          } as React.CSSProperties & { '--member-color': string }}
                        >
                          {/* Status Bubble - Thought Bubble Style */}
                          {member.status && (
                            <div className="absolute -top-12 left-1/2 transform -translate-x-1/2 z-20">
                              <div className="relative bg-card border-2 border-border rounded-[30px] px-3 py-1.5 shadow-lg max-w-[130px]">
                                <div className="flex items-center gap-1.5">
                                  {member.status.emoji && <span className="text-sm">{member.status.emoji}</span>}
                                  <span className="text-xs font-comic text-foreground truncate">{member.status.text}</span>
                                </div>
                                {/* Thought bubble circles - staggered diagonally toward avatar */}
                                <div className="absolute -bottom-5 left-1/2 transform -translate-x-1/2 translate-x-2">
                                  <div className="w-2.5 h-2.5 bg-card border-2 border-border rounded-full shadow-md"></div>
                                </div>
                                <div className="absolute -bottom-7 left-1/2 transform -translate-x-1/2 translate-x-3">
                                  <div className="w-1.5 h-1.5 bg-card border border-border rounded-full shadow-sm"></div>
                                </div>
                              </div>
                            </div>
                          )}
                          <Link to={`/${member.name}`}>
                            <div className="text-center">
                              <div className="relative inline-block">
                                <img
                                  src={member.avatar_url || 'https://c.stupid.cat/assets/favicon/avatar.png'}
                                  alt={member.display_name || member.name}
                                  className="w-16 h-16 mx-auto rounded-full object-cover mb-2 border-[3px] transition-all hover:scale-105 member-avatar"
                                  style={{
                                    borderColor: borderColor,
                                    boxShadow: `0 0 12px ${borderColor}40`
                                  }}
                                  onError={(e) => {
                                    (e.target as HTMLImageElement).src = 'https://c.stupid.cat/assets/favicon/avatar.png';
                                  }}
                                />
                              </div>
                              <h3 
                                className="font-comic font-semibold text-sm transition-colors"
                                style={{
                                  color: memberColor || 'rgb(var(--card-foreground))'
                                }}
                              >
                                {member.display_name || member.name}
                              </h3>
                              {member.pronouns && (
                                <p className="text-xs text-muted-foreground mt-1 font-comic">
                                  {member.pronouns}
                                </p>
                              )}

                              {member.tags && member.tags.length > 0 && (
                                <div className="flex flex-wrap gap-1 mt-2 justify-center">
                                  {[...member.tags].sort((a, b) => a.localeCompare(b)).slice(0, 2).map((tag, index) => (
                                    <span
                                      key={index}
                                      className="text-xs px-2 py-1 rounded-full font-comic bg-secondary text-secondary-foreground"
                                    >
                                      {tag}
                                    </span>
                                  ))}
                                  {member.tags.length > 2 && (
                                    <span className="text-xs text-muted-foreground font-comic">
                                      +{member.tags.length - 2}
                                    </span>
                                  )}
                                </div>
                              )}
                            </div>
                          </Link>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <p className="font-comic text-lg text-muted-foreground">
                      {searchQuery || currentTagFilter
                        ? 'No members found matching your criteria.'
                        : 'No members available.'
                      }
                    </p>
                    {(searchQuery || currentTagFilter) && (
                      <div className="mt-4 flex gap-2 justify-center">
                        {searchQuery && (
                          <Button variant="secondary" size="sm" onClick={clearSearch} className="font-comic">
                            Clear search
                          </Button>
                        )}
                        {currentTagFilter && (
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => setCurrentTagFilter(null)}
                            className="font-comic"
                          >
                            Clear filter
                          </Button>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="github-footer">
        <a
          href="https://git.gay/doughmination/web"
          target="_blank"
          rel="noopener noreferrer"
          className="github-button"
        >
          <svg xmlns="http://www.w3.org/2000/svg" xmlSpace="preserve" viewBox="0 0 120 120" width="32" height="32"><defs><clipPath id="a" clipPathUnits="userSpaceOnUse"><path stroke-width="1.306" d="m117.728 54.656-52.39-52.39a7.727 7.727 0 0 0-10.931 0l-10.875 10.88 13.797 13.8a9.18 9.18 0 0 1 11.622 11.702l13.3 13.3a9.18 9.18 0 0 1 9.505 2.183 9.194 9.194 0 0 1 0 13.003 9.205 9.205 0 0 1-13.013 0 9.2 9.2 0 0 1-1.995-10.003L64.343 44.728v32.645c5.642 2.788 6.879 10.294 2.428 14.744a9.19 9.19 0 0 1-13.002 0 9.194 9.194 0 0 1 0-13.005 9.2 9.2 0 0 1 3.009-2.01V44.158a9.206 9.206 0 0 1-4.988-12.06L38.186 18.493 2.26 54.41a7.74 7.74 0 0 0 0 10.931l52.392 52.399a7.736 7.736 0 0 0 10.93 0l52.157-52.152a7.74 7.74 0 0 0 0-10.932"/></clipPath></defs><g clip-path="url(#a)" paint-order="markers stroke fill"><rect width="120" height="22.5" fill="#fe9494" ry="0"/><rect width="120" height="22.5" y="20" fill="#ffc783" ry="0"/><rect width="120" height="22.5" y="40" fill="#fff683" ry="0"/><rect width="120" height="22.5" y="60.001" fill="#69cb86" ry="0"/><rect width="120" height="22.5" y="80.001" fill="#83a8ff" ry="0"/><rect width="120" height="19.999" y="100.002" fill="#c56ad4" ry="0"/></g></svg>
          View on GitGay
        </a>
        <p className="mt-4 text-sm text-muted-foreground font-comic">
          Doughmination System® is a trade mark in the United Kingdom under trademark number{' '}
          <a
            href="https://www.ipo.gov.uk/t-tmj.htm/t-tmj/tm-journals/2025-039/UK00004263144.html"
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:text-foreground transition-colors"
          >
            UK00004263144
          </a>
        </p>
      </footer>

      {/* SEO Content Section - Hidden visually but readable by search engines */}
      <section className="sr-only" aria-label="About Doughmination System">
        <h1>Doughmination System® - Real-Time Plural System Tracker</h1>
        <p>
          Welcome to the Doughmination System®, a plural system (DID/OSDD) management platform.
          Track current fronters, view all system members, and manage switching patterns in real-time.
        </p>
        <h2>Features</h2>
        <ul>
          <li>Real-time fronting status tracking</li>
          <li>Comprehensive member profiles with pronouns and descriptions</li>
          <li>Mental health state monitoring</li>
          <li>Member tagging and categorization</li>
          <li>Switching metrics and analytics</li>
        </ul>
      </section>
    </div>
  );
}