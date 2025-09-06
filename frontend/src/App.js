import React, { useState, useEffect, createContext, useContext } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation, Link } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`, { withCredentials: true });
      setUser(response.data);
    } catch (error) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = (redirectUrl) => {
    const loginUrl = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
    window.location.href = loginUrl;
  };

  const logout = async () => {
    try {
      await axios.post(`${API}/auth/logout`, {}, { withCredentials: true });
      setUser(null);
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
};

// Profile page to handle OAuth redirect
const ProfilePage = () => {
  const { checkAuth } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const handleAuth = async () => {
      const hash = location.hash;
      if (hash.includes('session_id=')) {
        const sessionId = hash.split('session_id=')[1];
        
        try {
          // Get session data from Emergent
          const profileResponse = await axios.get(`${API}/auth/profile?session_id=${sessionId}`);
          const { session_token } = profileResponse.data;
          
          // Set session cookie
          await axios.post(`${API}/auth/set-session`, null, {
            params: { session_token },
            withCredentials: true
          });
          
          // Check auth and redirect
          await checkAuth();
          navigate('/dashboard');
        } catch (error) {
          console.error('Authentication error:', error);
          navigate('/');
        }
      } else {
        // No session_id, redirect to dashboard if already authenticated
        navigate('/dashboard');
      }
    };

    handleAuth();
  }, [location, checkAuth, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
        <p className="mt-4 text-gray-600">Completing authentication...</p>
      </div>
    </div>
  );
};

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/" replace />;
  }

  return children;
};

// Login Page
const LoginPage = () => {
  const { user, login } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (user) {
      navigate('/dashboard');
    }
  }, [user, navigate]);

  const handleLogin = () => {
    const redirectUrl = `${window.location.origin}/profile`;
    login(redirectUrl);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
        <div className="text-center mb-8">
          <div className="flex flex-col items-center mb-6">
            <img 
              src="https://customer-assets.emergentagent.com/job_biz-connector-4/artifacts/tgh8glfj_image.png"
              alt="YouroCRM Logo"
              className="yourocrm-logo-main h-32 sm:h-40 md:h-48 w-auto mb-4 transform hover:scale-105 transition-transform shadow-lg rounded-lg"
            />
            <p className="text-gray-600 text-center text-lg sm:text-xl">Professional CRM & Peppol Invoicing Platform</p>
          </div>
          <p className="text-gray-600">Manage customers and send Peppol invoices</p>
        </div>
        
        <div className="space-y-6">
          <button
            onClick={handleLogin}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg transition duration-200 flex items-center justify-center space-x-2"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            <span>Continue with Google</span>
          </button>
        </div>

        <div className="mt-8 pt-6 border-t border-gray-200">
          <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
            <div className="space-y-2">
              <h3 className="font-semibold text-gray-900">CRM Features</h3>
              <ul className="space-y-1">
                <li>• Contact Management</li>
                <li>• Account Tracking</li>
                <li>• Product Catalog</li>
                <li>• Calendar & Events</li>
              </ul>
            </div>
            <div className="space-y-2">
              <h3 className="font-semibold text-gray-900">Invoicing</h3>
              <ul className="space-y-1">
                <li>• Peppol Integration</li>
                <li>• PDF Generation</li>
                <li>• Payment Tracking</li>
                <li>• Credit Notes</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Main Layout Component
const Layout = ({ children }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: '📊', description: 'Overview & stats' },
    { name: 'Calendar', href: '/calendar', icon: '📅', description: 'Events & schedule' },
    { name: 'Contacts', href: '/contacts', icon: '👥', description: 'People & leads' },
    { name: 'Accounts', href: '/accounts', icon: '🏢', description: 'Companies & clients' },
    { name: 'Products', href: '/products', icon: '📦', description: 'Services & catalog' },
    { name: 'Invoices', href: '/invoices', icon: '🧾', description: 'Billing & Peppol' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Left Sidebar */}
      <div className={`${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0`}>
        <div className="flex flex-col h-full">
          {/* Sidebar Header */}
          <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200">
            <Link to="/dashboard" className="flex items-center space-x-3">
              <img 
                src="https://customer-assets.emergentagent.com/job_biz-connector-4/artifacts/tgh8glfj_image.png"
                alt="YouroCRM Logo"
                className="yourocrm-logo-sidebar h-10 lg:h-12 w-auto transform hover:scale-105 transition-transform"
              />
            </Link>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2">
            {navigation.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center px-3 py-3 rounded-lg text-sm font-medium transition-colors group ${
                  location.pathname === item.href
                    ? 'bg-blue-50 text-blue-700 border-r-4 border-blue-600'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
                onClick={() => setSidebarOpen(false)}
              >
                <span className="text-xl mr-3">{item.icon}</span>
                <div className="flex-1">
                  <div className="font-medium">{item.name}</div>
                  <div className="text-xs text-gray-500 group-hover:text-gray-600">
                    {item.description}
                  </div>
                </div>
              </Link>
            ))}
          </nav>

          {/* User Profile in Sidebar */}
          <div className="border-t border-gray-200 p-4">
            <div className="flex items-center space-x-3 mb-3">
              {user?.picture && (
                <img src={user.picture} alt="Profile" className="w-10 h-10 rounded-full" />
              )}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{user?.name}</p>
                <p className="text-xs text-gray-500 truncate">{user?.email}</p>
              </div>
            </div>
            <button
              onClick={logout}
              className="w-full flex items-center px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-md transition-colors"
            >
              <span className="mr-2">🚪</span>
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black bg-opacity-50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col lg:ml-0">
        {/* Top Header for Mobile */}
        <header className="lg:hidden bg-white shadow-sm border-b h-16 flex items-center justify-between px-4">
          <button
            onClick={() => setSidebarOpen(true)}
            className="text-gray-500 hover:text-gray-700"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <Link to="/dashboard" className="flex items-center space-x-2">
            <img 
              src="https://customer-assets.emergentagent.com/job_biz-connector-4/artifacts/tgh8glfj_image.png"
              alt="YouroCRM Logo"
              className="h-8 sm:h-10 w-auto transform hover:scale-105 transition-transform"
            />
          </Link>
          <div className="w-6"></div> {/* Spacer for centering */}
        </header>

        {/* Page Content */}
        <main className="flex-1 p-6 overflow-auto">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

// Global Search Component
const GlobalSearch = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState({ contacts: [], accounts: [], products: [], invoices: [], events: [] });
  const [searching, setSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);

  const performSearch = async (term) => {
    if (term.length < 2) {
      setSearchResults({ contacts: [], accounts: [], products: [], invoices: [], events: [] });
      setShowResults(false);
      return;
    }

    setSearching(true);
    try {
      const [contactsRes, accountsRes, productsRes, invoicesRes, eventsRes] = await Promise.all([
        axios.get(`${API}/contacts`, { withCredentials: true }),
        axios.get(`${API}/accounts`, { withCredentials: true }),
        axios.get(`${API}/products`, { withCredentials: true }),
        axios.get(`${API}/invoices`, { withCredentials: true }),
        axios.get(`${API}/calendar/events`, { withCredentials: true })
      ]);

      const lowerTerm = term.toLowerCase();

      const filteredContacts = contactsRes.data.filter(contact => 
        contact.name.toLowerCase().includes(lowerTerm) ||
        contact.email?.toLowerCase().includes(lowerTerm) ||
        contact.company?.toLowerCase().includes(lowerTerm)
      ).slice(0, 3);

      const filteredAccounts = accountsRes.data.filter(account =>
        account.name.toLowerCase().includes(lowerTerm) ||
        account.industry?.toLowerCase().includes(lowerTerm) ||
        account.vat_number?.toLowerCase().includes(lowerTerm)
      ).slice(0, 3);

      const filteredProducts = productsRes.data.filter(product =>
        product.name.toLowerCase().includes(lowerTerm) ||
        product.description?.toLowerCase().includes(lowerTerm) ||
        product.sku?.toLowerCase().includes(lowerTerm)
      ).slice(0, 3);

      const filteredInvoices = invoicesRes.data.filter(invoice =>
        invoice.invoice_number.toLowerCase().includes(lowerTerm)
      ).slice(0, 3);

      const filteredEvents = eventsRes.data.filter(event =>
        event.title.toLowerCase().includes(lowerTerm) ||
        event.description?.toLowerCase().includes(lowerTerm)
      ).slice(0, 3);

      setSearchResults({
        contacts: filteredContacts,
        accounts: filteredAccounts,
        products: filteredProducts,
        invoices: filteredInvoices,
        events: filteredEvents
      });
      setShowResults(true);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setSearching(false);
    }
  };

  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      performSearch(searchTerm);
    }, 300);

    return () => clearTimeout(debounceTimer);
  }, [searchTerm]);

  const getTotalResults = () => {
    return searchResults.contacts.length + searchResults.accounts.length + 
           searchResults.products.length + searchResults.invoices.length + searchResults.events.length;
  };

  return (
    <div className="relative w-full max-w-2xl">
      <div className="relative">
        <input
          type="text"
          placeholder="🔍 Search everything..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onFocus={() => searchTerm.length >= 2 && setShowResults(true)}
          className="w-full border-2 border-blue-300 rounded-lg px-4 py-3 pr-10 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
        />
        {searching && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
          </div>
        )}
      </div>

      {/* Search Results Dropdown */}
      {showResults && searchTerm.length >= 2 && (
        <div className="absolute top-full mt-2 w-full bg-white rounded-lg shadow-xl border-2 border-gray-200 z-50 max-h-96 overflow-y-auto">
          {getTotalResults() === 0 ? (
            <div className="p-4 text-center text-gray-500">
              No results found for "{searchTerm}"
            </div>
          ) : (
            <div className="p-2">
              <div className="text-sm text-gray-500 px-3 py-2 border-b">
                Found {getTotalResults()} results for "{searchTerm}"
              </div>

              {/* Contacts Results */}
              {searchResults.contacts.length > 0 && (
                <div className="py-2">
                  <div className="text-xs font-semibold text-gray-400 px-3 py-1 uppercase tracking-wider">Contacts</div>
                  {searchResults.contacts.map(contact => (
                    <Link
                      key={contact.id}
                      to="/contacts"
                      className="block px-3 py-2 hover:bg-blue-50 transition-colors"
                      onClick={() => setShowResults(false)}
                    >
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                          <span className="text-white text-sm font-semibold">
                            {contact.name.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <div className="font-medium text-gray-900">{contact.name}</div>
                          <div className="text-sm text-gray-600">{contact.email}</div>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              )}

              {/* Accounts Results */}
              {searchResults.accounts.length > 0 && (
                <div className="py-2">
                  <div className="text-xs font-semibold text-gray-400 px-3 py-1 uppercase tracking-wider">Accounts</div>
                  {searchResults.accounts.map(account => (
                    <Link
                      key={account.id}
                      to="/accounts"
                      className="block px-3 py-2 hover:bg-green-50 transition-colors"
                      onClick={() => setShowResults(false)}
                    >
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                          <span className="text-white text-sm font-semibold">
                            {account.name.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <div className="font-medium text-gray-900">{account.name}</div>
                          <div className="text-sm text-gray-600">{account.industry}</div>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              )}

              {/* Products Results */}
              {searchResults.products.length > 0 && (
                <div className="py-2">
                  <div className="text-xs font-semibold text-gray-400 px-3 py-1 uppercase tracking-wider">Products</div>
                  {searchResults.products.map(product => (
                    <Link
                      key={product.id}
                      to="/products"
                      className="block px-3 py-2 hover:bg-purple-50 transition-colors"
                      onClick={() => setShowResults(false)}
                    >
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
                          <span className="text-white text-sm font-semibold">
                            {product.name.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <div className="font-medium text-gray-900">{product.name}</div>
                          <div className="text-sm text-gray-600">€{product.price.toFixed(2)}</div>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              )}

              {/* Invoices Results */}
              {searchResults.invoices.length > 0 && (
                <div className="py-2">
                  <div className="text-xs font-semibold text-gray-400 px-3 py-1 uppercase tracking-wider">Invoices</div>
                  {searchResults.invoices.map(invoice => (
                    <Link
                      key={invoice.id}
                      to="/invoices"
                      className="block px-3 py-2 hover:bg-red-50 transition-colors"
                      onClick={() => setShowResults(false)}
                    >
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-red-500 rounded-full flex items-center justify-center">
                          <span className="text-white text-sm font-semibold">🧾</span>
                        </div>
                        <div>
                          <div className="font-medium text-gray-900">{invoice.invoice_number}</div>
                          <div className="text-sm text-gray-600">€{invoice.total_amount.toFixed(2)}</div>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              )}

              {/* Events Results */}
              {searchResults.events.length > 0 && (
                <div className="py-2">
                  <div className="text-xs font-semibold text-gray-400 px-3 py-1 uppercase tracking-wider">Events</div>
                  {searchResults.events.map(event => (
                    <Link
                      key={event.id}
                      to="/calendar"
                      className="block px-3 py-2 hover:bg-orange-50 transition-colors"
                      onClick={() => setShowResults(false)}
                    >
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center">
                          <span className="text-white text-sm font-semibold">📅</span>
                        </div>
                        <div>
                          <div className="font-medium text-gray-900">{event.title}</div>
                          <div className="text-sm text-gray-600">
                            {new Date(event.start_date).toLocaleDateString()}
                          </div>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Click outside to close */}
      {showResults && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowResults(false)}
        />
      )}
    </div>
  );
};

// Dashboard Component
const Dashboard = () => {
  const [stats, setStats] = useState({ contacts: 0, accounts: 0, products: 0, events: 0, invoices: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await axios.get(`${API}/dashboard/stats`, { withCredentials: true });
        setStats(response.data);
      } catch (error) {
        console.error('Error fetching stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  const statCards = [
    { name: 'Contacts', value: stats.contacts, icon: '👥', color: 'blue' },
    { name: 'Accounts', value: stats.accounts, icon: '🏢', color: 'green' },
    { name: 'Products', value: stats.products, icon: '📦', color: 'purple' },
    { name: 'Invoices', value: stats.invoices || 0, icon: '🧾', color: 'red' },
    { name: 'Events', value: stats.events, icon: '📅', color: 'orange' },
  ];

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-gray-200 rounded w-48"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-gray-200 rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col items-center gap-4">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">Welcome to yourocrm.com</p>
        </div>
        
        {/* Global Search */}
        <div className="w-full max-w-2xl">
          <GlobalSearch />
        </div>
      </div>

      {/* Quick Create Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <span className="text-2xl mr-2">⚡</span>
          Quick Actions
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          <Link
            to="/contacts?new=true"
            className="flex flex-col items-center p-4 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors group"
          >
            <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
              <span className="text-white text-xl font-bold">+</span>
            </div>
            <span className="text-sm font-medium text-gray-900">Add Contact</span>
            <span className="text-xs text-gray-600">New customer</span>
          </Link>

          <Link
            to="/accounts?new=true"
            className="flex flex-col items-center p-4 bg-green-50 hover:bg-green-100 rounded-lg transition-colors group"
          >
            <div className="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
              <span className="text-white text-xl font-bold">+</span>
            </div>
            <span className="text-sm font-medium text-gray-900">Add Account</span>
            <span className="text-xs text-gray-600">New company</span>
          </Link>

          <Link
            to="/products?new=true"
            className="flex flex-col items-center p-4 bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors group"
          >
            <div className="w-12 h-12 bg-purple-500 rounded-full flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
              <span className="text-white text-xl font-bold">+</span>
            </div>
            <span className="text-sm font-medium text-gray-900">Add Product</span>
            <span className="text-xs text-gray-600">New service</span>
          </Link>

          <Link
            to="/invoices?new=true"
            className="flex flex-col items-center p-4 bg-red-50 hover:bg-red-100 rounded-lg transition-colors group"
          >
            <div className="w-12 h-12 bg-red-500 rounded-full flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
              <span className="text-white text-xl font-bold">+</span>
            </div>
            <span className="text-sm font-medium text-gray-900">Create Invoice</span>
            <span className="text-xs text-gray-600">Bill customer</span>
          </Link>

          <Link
            to="/calendar?new=true"
            className="flex flex-col items-center p-4 bg-orange-50 hover:bg-orange-100 rounded-lg transition-colors group"
          >
            <div className="w-12 h-12 bg-orange-500 rounded-full flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
              <span className="text-white text-xl font-bold">+</span>
            </div>
            <span className="text-sm font-medium text-gray-900">Add Event</span>
            <span className="text-xs text-gray-600">Schedule meeting</span>
          </Link>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        {statCards.map((card) => (
          <div key={card.name} className="bg-white rounded-lg shadow p-6 text-center">
            <div className="flex flex-col items-center space-y-2">
              <div className="text-3xl">{card.icon}</div>
              <div>
                <p className="text-3xl font-bold text-gray-900">{card.value}</p>
                <p className="text-sm font-medium text-gray-600">{card.name}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="space-y-3">
            <Link
              to="/contacts?new=true"
              className="flex items-center p-3 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
            >
              <span className="text-2xl mr-3">➕</span>
              <div>
                <p className="font-medium text-gray-900">Add New Contact</p>
                <p className="text-sm text-gray-600">Create a new customer contact</p>
              </div>
            </Link>
            <Link
              to="/invoices?new=true"
              className="flex items-center p-3 bg-green-50 rounded-lg hover:bg-green-100 transition-colors"
            >
              <span className="text-2xl mr-3">🧾</span>
              <div>
                <p className="font-medium text-gray-900">Create Invoice</p>
                <p className="text-sm text-gray-600">Generate and send via Peppol</p>
              </div>
            </Link>
            <Link
              to="/calendar?new=true"
              className="flex items-center p-3 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors"
            >
              <span className="text-2xl mr-3">📅</span>
              <div>
                <p className="font-medium text-gray-900">Schedule Meeting</p>
                <p className="text-sm text-gray-600">Add event to calendar</p>
              </div>
            </Link>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
          <div className="space-y-3">
            <div className="flex items-center p-3 bg-gray-50 rounded-lg">
              <span className="text-2xl mr-3">🎉</span>
              <div>
                <p className="font-medium text-gray-900">Welcome to yourocrm.com!</p>
                <p className="text-sm text-gray-600">Start by adding your first contact</p>
              </div>
            </div>
            <div className="flex items-center p-3 bg-yellow-50 rounded-lg">
              <span className="text-2xl mr-3">⚡</span>
              <div>
                <p className="font-medium text-gray-900">Peppol Ready</p>
                <p className="text-sm text-gray-600">Belgium invoicing compliance enabled</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Placeholder components for other routes
// Contacts Management Component
const ContactsPage = () => {
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedContact, setSelectedContact] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Contact form state
  const [contactForm, setContactForm] = useState({
    name: '',
    email: '',
    phone: '',
    company: '',
    position: '',
    address: '',
    notes: ''
  });

  // Check for new parameter and open modal
  const location = useLocation();
  useEffect(() => {
    const urlParams = new URLSearchParams(location.search);
    if (urlParams.get('new') === 'true') {
      openModal();
    }
  }, [location]);

  // Fetch contacts
  useEffect(() => {
    fetchContacts();
  }, []);

  const fetchContacts = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/contacts`, { withCredentials: true });
      setContacts(response.data);
    } catch (error) {
      console.error('Error fetching contacts:', error);
    } finally {
      setLoading(false);
    }
  };

  // Filter contacts by search term
  const filteredContacts = contacts.filter(contact =>
    contact.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    contact.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    contact.company?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Modal handlers
  const openModal = (contact = null) => {
    if (contact) {
      setContactForm(contact);
      setSelectedContact(contact);
    } else {
      setContactForm({
        name: '',
        email: '',
        phone: '',
        company: '',
        position: '',
        address: '',
        notes: ''
      });
      setSelectedContact(null);
    }
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedContact(null);
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (selectedContact) {
        // Update existing contact
        await axios.put(`${API}/contacts/${selectedContact.id}`, contactForm, { withCredentials: true });
        setContacts(contacts.map(c => c.id === selectedContact.id ? { ...selectedContact, ...contactForm } : c));
      } else {
        // Create new contact
        const response = await axios.post(`${API}/contacts`, contactForm, { withCredentials: true });
        setContacts([...contacts, response.data]);
      }
      closeModal();
    } catch (error) {
      console.error('Error saving contact:', error);
    }
  };

  // Handle delete
  const handleDelete = async (contactId) => {
    if (window.confirm('Are you sure you want to delete this contact?')) {
      try {
        await axios.delete(`${API}/contacts/${contactId}`, { withCredentials: true });
        setContacts(contacts.filter(c => c.id !== contactId));
        closeModal();
      } catch (error) {
        console.error('Error deleting contact:', error);
      }
    }
  };

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-gray-200 rounded w-48"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-48 bg-gray-200 rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col items-center gap-4">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">Contacts</h1>
          <p className="text-gray-600">Manage your customers and leads</p>
        </div>
        <button
          onClick={() => openModal()}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
        >
          + Add Contact
        </button>
      </div>

      {/* Search */}
      <div className="flex justify-center">
        <div className="w-full max-w-md">
          <input
            type="text"
            placeholder="Search contacts..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full border border-gray-300 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-center"
          />
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg shadow border text-center">
          <div className="text-2xl font-bold text-blue-600">{contacts.length}</div>
          <div className="text-sm text-gray-600">Total Contacts</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border text-center">
          <div className="text-2xl font-bold text-green-600">
            {contacts.filter(c => c.company).length}
          </div>
          <div className="text-sm text-gray-600">With Companies</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border text-center">
          <div className="text-2xl font-bold text-purple-600">
            {contacts.filter(c => c.email).length}
          </div>
          <div className="text-sm text-gray-600">With Email</div>
        </div>
      </div>

      {/* Contacts Table */}
      <div className="bg-white rounded-lg shadow border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Company
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Email
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Phone
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Position
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredContacts.map((contact) => (
                <tr key={contact.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <div className="flex items-center justify-center space-x-3">
                      <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                        <span className="text-white font-semibold text-sm">
                          {contact.name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div className="font-medium text-gray-900">{contact.name}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                    {contact.company || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                    {contact.email ? (
                      <a href={`mailto:${contact.email}`} className="text-blue-600 hover:text-blue-900">
                        {contact.email}
                      </a>
                    ) : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                    {contact.phone ? (
                      <a href={`tel:${contact.phone}`} className="text-blue-600 hover:text-blue-900">
                        {contact.phone}
                      </a>
                    ) : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                    {contact.position || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-500">
                    {new Date(contact.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-medium">
                    <button
                      onClick={() => openModal(contact)}
                      className="text-blue-600 hover:text-blue-900 mr-3"
                      title="Edit Contact"
                    >
                      ✏️ Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Empty State */}
      {filteredContacts.length === 0 && !loading && (
        <div className="text-center py-12">
          <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-4xl">👥</span>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {searchTerm ? 'No contacts found' : 'No contacts yet'}
          </h3>
          <p className="text-gray-600 mb-4">
            {searchTerm 
              ? 'Try adjusting your search terms'
              : 'Start building your contact list by adding your first contact'
            }
          </p>
          {!searchTerm && (
            <button
              onClick={() => openModal()}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Add Your First Contact
            </button>
          )}
        </div>
      )}

      {/* Contact Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <div></div>
                <h3 className="text-lg font-semibold text-gray-900 text-center flex-1">
                  {selectedContact ? 'Edit Contact' : 'Add New Contact'}
                </h3>
                <button
                  onClick={closeModal}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                >
                  ×
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Full Name *
                    </label>
                    <input
                      type="text"
                      required
                      value={contactForm.name}
                      onChange={(e) => setContactForm({...contactForm, name: e.target.value})}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="John Smith"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Email
                    </label>
                    <input
                      type="email"
                      value={contactForm.email}
                      onChange={(e) => setContactForm({...contactForm, email: e.target.value})}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="john@company.com"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Phone
                    </label>
                    <input
                      type="tel"
                      value={contactForm.phone}
                      onChange={(e) => setContactForm({...contactForm, phone: e.target.value})}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="+32 2 123 4567"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Company
                    </label>
                    <input
                      type="text"
                      value={contactForm.company}
                      onChange={(e) => setContactForm({...contactForm, company: e.target.value})}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Company Name"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Position
                  </label>
                  <input
                    type="text"
                    value={contactForm.position}
                    onChange={(e) => setContactForm({...contactForm, position: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="CEO, Manager, Developer..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Address
                  </label>
                  <input
                    type="text"
                    value={contactForm.address}
                    onChange={(e) => setContactForm({...contactForm, address: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Street, City, Country"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Notes
                  </label>
                  <textarea
                    value={contactForm.notes}
                    onChange={(e) => setContactForm({...contactForm, notes: e.target.value})}
                    rows={3}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Additional notes about this contact..."
                  />
                </div>

                <div className="flex justify-between pt-4">
                  <div>
                    {selectedContact && (
                      <button
                        type="button"
                        onClick={() => handleDelete(selectedContact.id)}
                        className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors text-sm font-medium"
                      >
                        Delete Contact
                      </button>
                    )}
                  </div>
                  <div className="flex space-x-3">
                    <button
                      type="button"
                      onClick={closeModal}
                      className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition-colors text-sm font-medium"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
                    >
                      {selectedContact ? 'Update Contact' : 'Add Contact'}
                    </button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Accounts Management Component
const AccountsPage = () => {
  const [accounts, setAccounts] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Account form state
  const [accountForm, setAccountForm] = useState({
    name: '',
    contact_id: '',
    industry: '',
    website: '',
    annual_revenue: '',
    employee_count: '',
    address: '',
    vat_number: '',
    notes: ''
  });

  // Check for new parameter and open modal
  const location = useLocation();
  useEffect(() => {
    const urlParams = new URLSearchParams(location.search);
    if (urlParams.get('new') === 'true') {
      openModal();
    }
  }, [location]);

  // Fetch data
  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [accountsRes, contactsRes] = await Promise.all([
        axios.get(`${API}/accounts`, { withCredentials: true }),
        axios.get(`${API}/contacts`, { withCredentials: true })
      ]);
      setAccounts(accountsRes.data);
      setContacts(contactsRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Filter accounts by search term
  const filteredAccounts = accounts.filter(account =>
    account.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    account.industry?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    account.vat_number?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Get contact name for account
  const getContactName = (contactId) => {
    const contact = contacts.find(c => c.id === contactId);
    return contact ? contact.name : 'No contact assigned';
  };

  // Modal handlers
  const openModal = (account = null) => {
    if (account) {
      setAccountForm({
        ...account,
        annual_revenue: account.annual_revenue || '',
        employee_count: account.employee_count || '',
        contact_id: account.contact_id || ''
      });
      setSelectedAccount(account);
    } else {
      setAccountForm({
        name: '',
        contact_id: '',
        industry: '',
        website: '',
        annual_revenue: '',
        employee_count: '',
        address: '',
        vat_number: '',
        notes: ''
      });
      setSelectedAccount(null);
    }
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedAccount(null);
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const submitData = {
        ...accountForm,
        annual_revenue: accountForm.annual_revenue ? parseFloat(accountForm.annual_revenue) : null,
        employee_count: accountForm.employee_count ? parseInt(accountForm.employee_count) : null,
        contact_id: accountForm.contact_id || null
      };

      if (selectedAccount) {
        // Update existing account
        await axios.put(`${API}/accounts/${selectedAccount.id}`, submitData, { withCredentials: true });
        setAccounts(accounts.map(a => a.id === selectedAccount.id ? { ...selectedAccount, ...submitData } : a));
      } else {
        // Create new account
        const response = await axios.post(`${API}/accounts`, submitData, { withCredentials: true });
        setAccounts([...accounts, response.data]);
      }
      closeModal();
    } catch (error) {
      console.error('Error saving account:', error);
    }
  };

  // Handle delete
  const handleDelete = async (accountId) => {
    if (window.confirm('Are you sure you want to delete this account? This action cannot be undone.')) {
      try {
        await axios.delete(`${API}/accounts/${accountId}`, { withCredentials: true });
        setAccounts(accounts.filter(a => a.id !== accountId));
        closeModal();
      } catch (error) {
        console.error('Error deleting account:', error);
      }
    }
  };

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-gray-200 rounded w-48"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-56 bg-gray-200 rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col items-center gap-4">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">Accounts</h1>
          <p className="text-gray-600">Manage your company accounts and clients</p>
        </div>
        <button
          onClick={() => openModal()}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
        >
          + Add Account
        </button>
      </div>

      {/* Search */}
      <div className="flex justify-center">
        <div className="w-full max-w-md">
          <input
            type="text"
            placeholder="Search accounts..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full border border-gray-300 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-center"
          />
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg shadow border text-center">
          <div className="text-2xl font-bold text-blue-600">{accounts.length}</div>
          <div className="text-sm text-gray-600">Total Accounts</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border text-center">
          <div className="text-2xl font-bold text-green-600">
            {accounts.filter(a => a.vat_number).length}
          </div>
          <div className="text-sm text-gray-600">With VAT Number</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border text-center">
          <div className="text-2xl font-bold text-purple-600">
            {accounts.filter(a => a.website).length}
          </div>
          <div className="text-sm text-gray-600">With Website</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border text-center">
          <div className="text-2xl font-bold text-orange-600">
            {accounts.reduce((sum, a) => sum + (a.annual_revenue || 0), 0).toLocaleString()}€
          </div>
          <div className="text-sm text-gray-600">Total Revenue</div>
        </div>
      </div>

      {/* Accounts Table */}
      <div className="bg-white rounded-lg shadow border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Account Name
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Contact
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Industry
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  VAT Number
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Website
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Revenue
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Employees
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredAccounts.map((account) => (
                <tr key={account.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <div className="flex items-center justify-center space-x-3">
                      <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                        <span className="text-white font-semibold text-sm">
                          {account.name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div className="font-medium text-gray-900">{account.name}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                    {getContactName(account.contact_id)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                    {account.industry || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                    {account.vat_number || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                    {account.website ? (
                      <a 
                        href={account.website.startsWith('http') ? account.website : `https://${account.website}`}
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-900 truncate max-w-32 inline-block"
                      >
                        {account.website}
                      </a>
                    ) : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                    {account.annual_revenue ? `€${account.annual_revenue.toLocaleString()}` : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                    {account.employee_count || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-500">
                    {new Date(account.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-medium">
                    <button
                      onClick={() => openModal(account)}
                      className="text-blue-600 hover:text-blue-900 mr-3"
                      title="Edit Account"
                    >
                      ✏️ Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Empty State */}
      {filteredAccounts.length === 0 && !loading && (
        <div className="text-center py-12">
          <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-4xl">🏢</span>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {searchTerm ? 'No accounts found' : 'No accounts yet'}
          </h3>
          <p className="text-gray-600 mb-4">
            {searchTerm 
              ? 'Try adjusting your search terms'
              : 'Start building your client base by adding your first account'
            }
          </p>
          {!searchTerm && (
            <button
              onClick={() => openModal()}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Add Your First Account
            </button>
          )}
        </div>
      )}

      {/* Account Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-semibold text-gray-900">
                  {selectedAccount ? 'Edit Account' : 'Add New Account'}
                </h3>
                <button
                  onClick={closeModal}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                >
                  ×
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Account Name *
                    </label>
                    <input
                      type="text"
                      required
                      value={accountForm.name}
                      onChange={(e) => setAccountForm({...accountForm, name: e.target.value})}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Company Name"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Primary Contact
                    </label>
                    <select
                      value={accountForm.contact_id}
                      onChange={(e) => setAccountForm({...accountForm, contact_id: e.target.value})}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">Select a contact</option>
                      {contacts.map(contact => (
                        <option key={contact.id} value={contact.id}>
                          {contact.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Industry
                    </label>
                    <input
                      type="text"
                      value={accountForm.industry}
                      onChange={(e) => setAccountForm({...accountForm, industry: e.target.value})}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Technology, Healthcare, Finance..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Website
                    </label>
                    <input
                      type="url"
                      value={accountForm.website}
                      onChange={(e) => setAccountForm({...accountForm, website: e.target.value})}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="https://company.com"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Annual Revenue (€)
                    </label>
                    <input
                      type="number"
                      min="0"
                      step="1000"
                      value={accountForm.annual_revenue}
                      onChange={(e) => setAccountForm({...accountForm, annual_revenue: e.target.value})}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="1000000"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Employee Count
                    </label>
                    <input
                      type="number"
                      min="1"
                      value={accountForm.employee_count}
                      onChange={(e) => setAccountForm({...accountForm, employee_count: e.target.value})}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="50"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    VAT Number (Peppol)
                  </label>
                  <input
                    type="text"
                    value={accountForm.vat_number}
                    onChange={(e) => setAccountForm({...accountForm, vat_number: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="BE0123456789"
                  />
                  <p className="text-xs text-gray-500 mt-1">Required for Peppol invoicing</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Address
                  </label>
                  <input
                    type="text"
                    value={accountForm.address}
                    onChange={(e) => setAccountForm({...accountForm, address: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Street, City, Country"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Notes
                  </label>
                  <textarea
                    value={accountForm.notes}
                    onChange={(e) => setAccountForm({...accountForm, notes: e.target.value})}
                    rows={3}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Additional notes about this account..."
                  />
                </div>

                <div className="flex justify-between pt-4">
                  <div>
                    {selectedAccount && (
                      <button
                        type="button"
                        onClick={() => handleDelete(selectedAccount.id)}
                        className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors text-sm font-medium"
                      >
                        Delete Account
                      </button>
                    )}
                  </div>
                  <div className="flex space-x-3">
                    <button
                      type="button"
                      onClick={closeModal}
                      className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition-colors text-sm font-medium"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
                    >
                      {selectedAccount ? 'Update Account' : 'Add Account'}
                    </button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Products Management Component
const ProductsPage = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');

  // Product form state
  const [productForm, setProductForm] = useState({
    name: '',
    description: '',
    price: '',
    currency: 'EUR',
    tax_rate: 0.21,
    sku: '',
    category: '',
    active: true
  });

  // Check for new parameter and open modal
  const location = useLocation();
  useEffect(() => {
    const urlParams = new URLSearchParams(location.search);
    if (urlParams.get('new') === 'true') {
      openModal();
    }
  }, [location]);

  // Fetch products
  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/products`, { withCredentials: true });
      setProducts(response.data);
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  // Get unique categories
  const categories = [...new Set(products.filter(p => p.category).map(p => p.category))];

  // Filter products
  const filteredProducts = products.filter(product => {
    const matchesSearch = product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         product.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         product.sku?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = !categoryFilter || product.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  // Modal handlers
  const openModal = (product = null) => {
    if (product) {
      setProductForm({
        ...product,
        price: product.price.toString()
      });
      setSelectedProduct(product);
    } else {
      setProductForm({
        name: '',
        description: '',
        price: '',
        currency: 'EUR',
        tax_rate: 0.21,
        sku: '',
        category: '',
        active: true
      });
      setSelectedProduct(null);
    }
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedProduct(null);
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const submitData = {
        ...productForm,
        price: parseFloat(productForm.price),
        tax_rate: parseFloat(productForm.tax_rate)
      };

      if (selectedProduct) {
        // Update existing product
        await axios.put(`${API}/products/${selectedProduct.id}`, submitData, { withCredentials: true });
        setProducts(products.map(p => p.id === selectedProduct.id ? { ...selectedProduct, ...submitData } : p));
      } else {
        // Create new product
        const response = await axios.post(`${API}/products`, submitData, { withCredentials: true });
        setProducts([...products, response.data]);
      }
      closeModal();
    } catch (error) {
      console.error('Error saving product:', error);
    }
  };

  // Handle delete
  const handleDelete = async (productId) => {
    if (window.confirm('Are you sure you want to delete this product? This will affect any invoices that reference it.')) {
      try {
        await axios.delete(`${API}/products/${productId}`, { withCredentials: true });
        setProducts(products.filter(p => p.id !== productId));
        closeModal();
      } catch (error) {
        console.error('Error deleting product:', error);
      }
    }
  };

  // Generate SKU suggestion
  const generateSKU = () => {
    const name = productForm.name.toUpperCase().replace(/[^A-Z0-9]/g, '').substring(0, 6);
    const random = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
    return `${name}-${random}`;
  };

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-gray-200 rounded w-48"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-64 bg-gray-200 rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col items-center gap-4">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">Product Catalog</h1>
          <p className="text-gray-600">Manage your products and services</p>
        </div>
        <button
          onClick={() => openModal()}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
        >
          + Add Product
        </button>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col items-center gap-4">
        <div className="w-full max-w-md">
          <input
            type="text"
            placeholder="Search products..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full border border-gray-300 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-center"
          />
        </div>
        <div className="w-full max-w-xs">
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="w-full border border-gray-300 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-center"
          >
            <option value="">All Categories</option>
            {categories.map(category => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg shadow border text-center">
          <div className="text-2xl font-bold text-blue-600">{products.length}</div>
          <div className="text-sm text-gray-600">Total Products</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border text-center">
          <div className="text-2xl font-bold text-green-600">
            {products.filter(p => p.active).length}
          </div>
          <div className="text-sm text-gray-600">Active Products</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border text-center">
          <div className="text-2xl font-bold text-purple-600">{categories.length}</div>
          <div className="text-sm text-gray-600">Categories</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border text-center">
          <div className="text-2xl font-bold text-orange-600">
            €{products.reduce((sum, p) => sum + p.price, 0).toFixed(0)}
          </div>
          <div className="text-sm text-gray-600">Total Value</div>
        </div>
      </div>

      {/* Products Table */}
      <div className="bg-white rounded-lg shadow border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Product Name
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  SKU
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Price (Ex. VAT)
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  VAT Rate
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Price (Inc. VAT)
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredProducts.map((product) => (
                <tr key={product.id} className={`hover:bg-gray-50 ${!product.active ? 'opacity-60' : ''}`}>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <div className="flex items-center justify-center space-x-3">
                      <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
                        <span className="text-white font-semibold text-sm">
                          {product.name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div className="font-medium text-gray-900">{product.name}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                    {product.category ? (
                      <span className="inline-block px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                        {product.category}
                      </span>
                    ) : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                    {product.sku || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-semibold text-green-600">
                    €{product.price.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                    {(product.tax_rate * 100).toFixed(0)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-semibold text-gray-900">
                    €{(product.price * (1 + product.tax_rate)).toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      product.active 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {product.active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-500">
                    {new Date(product.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-medium">
                    <button
                      onClick={() => openModal(product)}
                      className="text-blue-600 hover:text-blue-900 mr-3"
                      title="Edit Product"
                    >
                      ✏️ Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Empty State */}
      {filteredProducts.length === 0 && !loading && (
        <div className="text-center py-12">
          <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-4xl">📦</span>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {searchTerm || categoryFilter ? 'No products found' : 'No products yet'}
          </h3>
          <p className="text-gray-600 mb-4">
            {searchTerm || categoryFilter
              ? 'Try adjusting your search terms or filters'
              : 'Create your first product to start building your catalog'
            }
          </p>
          {!searchTerm && !categoryFilter && (
            <button
              onClick={() => openModal()}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Add Your First Product
            </button>
          )}
        </div>
      )}

      {/* Product Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-semibold text-gray-900">
                  {selectedProduct ? 'Edit Product' : 'Add New Product'}
                </h3>
                <button
                  onClick={closeModal}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                >
                  ×
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Product Name *
                    </label>
                    <input
                      type="text"
                      required
                      value={productForm.name}
                      onChange={(e) => setProductForm({...productForm, name: e.target.value})}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Professional Consulting"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Category
                    </label>
                    <input
                      type="text"
                      value={productForm.category}
                      onChange={(e) => setProductForm({...productForm, category: e.target.value})}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Services, Software, Hardware..."
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={productForm.description}
                    onChange={(e) => setProductForm({...productForm, description: e.target.value})}
                    rows={3}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Detailed description of your product or service..."
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Price (€) *
                    </label>
                    <input
                      type="number"
                      required
                      min="0"
                      step="0.01"
                      value={productForm.price}
                      onChange={(e) => setProductForm({...productForm, price: e.target.value})}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="100.00"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Currency
                    </label>
                    <select
                      value={productForm.currency}
                      onChange={(e) => setProductForm({...productForm, currency: e.target.value})}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="EUR">EUR (€)</option>
                      <option value="USD">USD ($)</option>
                      <option value="GBP">GBP (£)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tax Rate (%)
                    </label>
                    <select
                      value={productForm.tax_rate}
                      onChange={(e) => setProductForm({...productForm, tax_rate: parseFloat(e.target.value)})}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value={0.21}>21% (Belgium Standard)</option>
                      <option value={0.12}>12% (Belgium Reduced)</option>
                      <option value={0.06}>6% (Belgium Super Reduced)</option>
                      <option value={0.00}>0% (Exempt)</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      SKU (Stock Keeping Unit)
                    </label>
                    <div className="flex">
                      <input
                        type="text"
                        value={productForm.sku}
                        onChange={(e) => setProductForm({...productForm, sku: e.target.value})}
                        className="flex-1 border border-gray-300 rounded-l-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        placeholder="PROD-001"
                      />
                      <button
                        type="button"
                        onClick={() => setProductForm({...productForm, sku: generateSKU()})}
                        className="px-3 py-2 bg-gray-100 border border-l-0 border-gray-300 rounded-r-md hover:bg-gray-200 text-sm"
                        title="Generate SKU"
                      >
                        🎲
                      </button>
                    </div>
                  </div>
                  <div className="flex items-center">
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={productForm.active}
                        onChange={(e) => setProductForm({...productForm, active: e.target.checked})}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700">Active Product</span>
                    </label>
                  </div>
                </div>

                {/* Price Preview */}
                {productForm.price && (
                  <div className="bg-gray-50 p-4 rounded-md">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Price Preview</h4>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <div className="text-gray-600">Base Price</div>
                        <div className="font-semibold">€{parseFloat(productForm.price || 0).toFixed(2)}</div>
                      </div>
                      <div>
                        <div className="text-gray-600">VAT ({(productForm.tax_rate * 100).toFixed(0)}%)</div>
                        <div className="font-semibold">€{(parseFloat(productForm.price || 0) * productForm.tax_rate).toFixed(2)}</div>
                      </div>
                      <div>
                        <div className="text-gray-600">Total Price</div>
                        <div className="font-semibold text-green-600">
                          €{(parseFloat(productForm.price || 0) * (1 + productForm.tax_rate)).toFixed(2)}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex justify-between pt-4">
                  <div>
                    {selectedProduct && (
                      <button
                        type="button"
                        onClick={() => handleDelete(selectedProduct.id)}
                        className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors text-sm font-medium"
                      >
                        Delete Product
                      </button>
                    )}
                  </div>
                  <div className="flex space-x-3">
                    <button
                      type="button"
                      onClick={closeModal}
                      className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition-colors text-sm font-medium"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
                    >
                      {selectedProduct ? 'Update Product' : 'Add Product'}
                    </button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Invoices Management Component
const InvoicesPage = () => {
  const [invoices, setInvoices] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Invoice form state
  const [invoiceForm, setInvoiceForm] = useState({
    account_id: '',
    contact_id: '',
    items: [{ product_id: '', quantity: 1, unit_price: 0, description: '' }],
    due_date: '',
    notes: '',
    invoice_type: 'invoice'
  });

  // Check for new parameter and open modal
  const location = useLocation();
  useEffect(() => {
    const urlParams = new URLSearchParams(location.search);
    if (urlParams.get('new') === 'true') {
      openModal();
    }
  }, [location]);

  // Fetch data
  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [invoicesRes, accountsRes, contactsRes, productsRes] = await Promise.all([
        axios.get(`${API}/invoices`, { withCredentials: true }),
        axios.get(`${API}/accounts`, { withCredentials: true }),
        axios.get(`${API}/contacts`, { withCredentials: true }),
        axios.get(`${API}/products`, { withCredentials: true })
      ]);
      
      setInvoices(invoicesRes.data);
      setAccounts(accountsRes.data);
      setContacts(contactsRes.data);
      setProducts(productsRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Filter invoices by search term
  const filteredInvoices = invoices.filter(invoice =>
    invoice.invoice_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    getAccountName(invoice.account_id).toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Helper functions
  const getAccountName = (accountId) => {
    const account = accounts.find(a => a.id === accountId);
    return account ? account.name : 'Unknown Account';
  };

  const getContactName = (contactId) => {
    const contact = contacts.find(c => c.id === contactId);
    return contact ? contact.name : '';
  };

  const getProductName = (productId) => {
    const product = products.find(p => p.id === productId);
    return product ? product.name : 'Unknown Product';
  };

  const getStatusColor = (status) => {
    const colors = {
      draft: 'bg-gray-100 text-gray-800',
      sent: 'bg-blue-100 text-blue-800',
      paid: 'bg-green-100 text-green-800',
      overdue: 'bg-red-100 text-red-800',
      cancelled: 'bg-red-100 text-red-800'
    };
    return colors[status] || colors.draft;
  };

  // Modal handlers
  const openModal = (invoice = null) => {
    if (invoice) {
      setInvoiceForm({
        account_id: invoice.account_id,
        contact_id: invoice.contact_id || '',
        items: invoice.items,
        due_date: invoice.due_date ? invoice.due_date.slice(0, 10) : '',
        notes: invoice.notes || '',
        invoice_type: invoice.invoice_type
      });
      setSelectedInvoice(invoice);
    } else {
      setInvoiceForm({
        account_id: '',
        contact_id: '',
        items: [{ product_id: '', quantity: 1, unit_price: 0, description: '' }],
        due_date: '',
        notes: '',
        invoice_type: 'invoice'
      });
      setSelectedInvoice(null);
    }
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedInvoice(null);
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const submitData = {
        ...invoiceForm,
        due_date: invoiceForm.due_date ? new Date(invoiceForm.due_date).toISOString() : null
      };

      if (selectedInvoice) {
        // Update existing invoice
        await axios.put(`${API}/invoices/${selectedInvoice.id}`, submitData, { withCredentials: true });
        fetchData(); // Refresh data
      } else {
        // Create new invoice
        await axios.post(`${API}/invoices`, submitData, { withCredentials: true });
        fetchData(); // Refresh data
      }
      closeModal();
    } catch (error) {
      console.error('Error saving invoice:', error);
    }
  };

  // Handle delete
  const handleDelete = async (invoiceId) => {
    if (window.confirm('Are you sure you want to delete this invoice? This action cannot be undone.')) {
      try {
        await axios.delete(`${API}/invoices/${invoiceId}`, { withCredentials: true });
        setInvoices(invoices.filter(i => i.id !== invoiceId));
        closeModal();
      } catch (error) {
        console.error('Error deleting invoice:', error);
      }
    }
  };

  // Handle PDF download
  const downloadPDF = async (invoiceId, invoiceNumber) => {
    try {
      const response = await axios.get(`${API}/invoices/${invoiceId}/pdf`, { withCredentials: true });
      
      // Decode base64 and create blob
      const pdfData = atob(response.data.pdf_data);
      const bytes = new Uint8Array(pdfData.length);
      for (let i = 0; i < pdfData.length; i++) {
        bytes[i] = pdfData.charCodeAt(i);
      }
      
      const blob = new Blob([bytes], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      
      // Create download link
      const link = document.createElement('a');
      link.href = url;
      link.download = `${invoiceNumber}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading PDF:', error);
    }
  };

  // Handle item changes
  const updateItem = (index, field, value) => {
    const newItems = [...invoiceForm.items];
    newItems[index] = { ...newItems[index], [field]: value };
    
    // Auto-fill unit price from product
    if (field === 'product_id') {
      const product = products.find(p => p.id === value);
      if (product) {
        newItems[index].unit_price = product.price;
        newItems[index].description = product.name;
      }
    }
    
    setInvoiceForm({ ...invoiceForm, items: newItems });
  };

  const addItem = () => {
    setInvoiceForm({
      ...invoiceForm,
      items: [...invoiceForm.items, { product_id: '', quantity: 1, unit_price: 0, description: '' }]
    });
  };

  const removeItem = (index) => {
    if (invoiceForm.items.length > 1) {
      const newItems = invoiceForm.items.filter((_, i) => i !== index);
      setInvoiceForm({ ...invoiceForm, items: newItems });
    }
  };

  // Calculate totals
  const calculateTotals = () => {
    const subtotal = invoiceForm.items.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0);
    const taxAmount = subtotal * 0.21; // Belgium VAT
    const total = subtotal + taxAmount;
    return { subtotal, taxAmount, total };
  };

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-gray-200 rounded w-48"></div>
        <div className="space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-16 bg-gray-200 rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  const { subtotal, taxAmount, total } = calculateTotals();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col items-center gap-4">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">Invoices</h1>
          <p className="text-gray-600">Manage invoices and generate PDFs</p>
        </div>
        <button
          onClick={() => openModal()}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
        >
          + Create Invoice
        </button>
      </div>

      {/* Search */}
      <div className="flex justify-center">
        <div className="w-full max-w-md">
          <input
            type="text"
            placeholder="Search invoices..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full border border-gray-300 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-center"
          />
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg shadow border text-center">
          <div className="text-2xl font-bold text-blue-600">{invoices.length}</div>
          <div className="text-sm text-gray-600">Total Invoices</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border text-center">
          <div className="text-2xl font-bold text-green-600">
            {invoices.filter(i => i.status === 'paid').length}
          </div>
          <div className="text-sm text-gray-600">Paid</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border text-center">
          <div className="text-2xl font-bold text-orange-600">
            {invoices.filter(i => i.status === 'sent').length}
          </div>
          <div className="text-sm text-gray-600">Pending</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border text-center">
          <div className="text-2xl font-bold text-purple-600">
            €{invoices.reduce((sum, i) => sum + i.total_amount, 0).toFixed(2)}
          </div>
          <div className="text-sm text-gray-600">Total Value</div>
        </div>
      </div>

      {/* Invoices Table */}
      <div className="bg-white rounded-lg shadow border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Invoice
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Account
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Amount
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredInvoices.map((invoice) => (
                <tr key={invoice.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-medium text-gray-900">{invoice.invoice_number}</div>
                    <div className="text-sm text-gray-500">{invoice.invoice_type}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-medium text-gray-900">{getAccountName(invoice.account_id)}</div>
                    {invoice.contact_id && (
                      <div className="text-sm text-gray-500">{getContactName(invoice.contact_id)}</div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-medium text-gray-900">€{invoice.total_amount.toFixed(2)}</div>
                    <div className="text-sm text-gray-500">€{invoice.subtotal.toFixed(2)} + VAT</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(invoice.status)}`}>
                      {invoice.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {new Date(invoice.issue_date).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                    <button
                      onClick={() => downloadPDF(invoice.id, invoice.invoice_number)}
                      className="text-green-600 hover:text-green-900"
                      title="Download PDF"
                    >
                      📄
                    </button>
                    <button
                      onClick={() => openModal(invoice)}
                      className="text-blue-600 hover:text-blue-900"
                      title="Edit"
                    >
                      ✏️
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Empty State */}
      {filteredInvoices.length === 0 && !loading && (
        <div className="text-center py-12">
          <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-4xl">🧾</span>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {searchTerm ? 'No invoices found' : 'No invoices yet'}
          </h3>
          <p className="text-gray-600 mb-4">
            {searchTerm 
              ? 'Try adjusting your search terms'
              : 'Create your first invoice to get started'
            }
          </p>
          {!searchTerm && (
            <button
              onClick={() => openModal()}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Create Your First Invoice
            </button>
          )}
        </div>
      )}

      {/* Invoice Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-semibold text-gray-900">
                  {selectedInvoice ? 'Edit Invoice' : 'Create New Invoice'}
                </h3>
                <button
                  onClick={closeModal}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                >
                  ×
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Basic Info */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Account *
                    </label>
                    <select
                      required
                      value={invoiceForm.account_id}
                      onChange={(e) => setInvoiceForm({...invoiceForm, account_id: e.target.value})}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">Select an account</option>
                      {accounts.map(account => (
                        <option key={account.id} value={account.id}>
                          {account.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Contact
                    </label>
                    <select
                      value={invoiceForm.contact_id}
                      onChange={(e) => setInvoiceForm({...invoiceForm, contact_id: e.target.value})}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">Select a contact</option>
                      {contacts.map(contact => (
                        <option key={contact.id} value={contact.id}>
                          {contact.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Due Date
                    </label>
                    <input
                      type="date"
                      value={invoiceForm.due_date}
                      onChange={(e) => setInvoiceForm({...invoiceForm, due_date: e.target.value})}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Type
                    </label>
                    <select
                      value={invoiceForm.invoice_type}
                      onChange={(e) => setInvoiceForm({...invoiceForm, invoice_type: e.target.value})}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="invoice">Invoice</option>
                      <option value="credit_note">Credit Note</option>
                    </select>
                  </div>
                </div>

                {/* Invoice Items */}
                <div>
                  <div className="flex justify-between items-center mb-4">
                    <label className="block text-sm font-medium text-gray-700">
                      Invoice Items *
                    </label>
                    <button
                      type="button"
                      onClick={addItem}
                      className="px-3 py-1 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
                    >
                      + Add Item
                    </button>
                  </div>

                  <div className="space-y-4">
                    {invoiceForm.items.map((item, index) => (
                      <div key={index} className="grid grid-cols-1 md:grid-cols-6 gap-4 p-4 border border-gray-200 rounded-md">
                        <div className="md:col-span-2">
                          <label className="block text-xs font-medium text-gray-700 mb-1">
                            Product
                          </label>
                          <select
                            value={item.product_id}
                            onChange={(e) => updateItem(index, 'product_id', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          >
                            <option value="">Select product</option>
                            {products.map(product => (
                              <option key={product.id} value={product.id}>
                                {product.name}
                              </option>
                            ))}
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">
                            Quantity
                          </label>
                          <input
                            type="number"
                            min="0.01"
                            step="0.01"
                            value={item.quantity}
                            onChange={(e) => updateItem(index, 'quantity', parseFloat(e.target.value) || 0)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">
                            Unit Price (€)
                          </label>
                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            value={item.unit_price}
                            onChange={(e) => updateItem(index, 'unit_price', parseFloat(e.target.value) || 0)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">
                            Total
                          </label>
                          <div className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm bg-gray-50">
                            €{(item.quantity * item.unit_price).toFixed(2)}
                          </div>
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">
                            Action
                          </label>
                          <button
                            type="button"
                            onClick={() => removeItem(index)}
                            disabled={invoiceForm.items.length === 1}
                            className="w-full px-3 py-2 bg-red-100 text-red-600 text-sm rounded-md hover:bg-red-200 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            Remove
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Totals */}
                  <div className="mt-6 bg-gray-50 p-4 rounded-md">
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>Subtotal:</span>
                        <span>€{subtotal.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>VAT (21%):</span>
                        <span>€{taxAmount.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between font-semibold text-lg border-t pt-2">
                        <span>Total:</span>
                        <span>€{total.toFixed(2)}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Notes */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Notes
                  </label>
                  <textarea
                    value={invoiceForm.notes}
                    onChange={(e) => setInvoiceForm({...invoiceForm, notes: e.target.value})}
                    rows={3}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Additional notes for this invoice..."
                  />
                </div>

                <div className="flex justify-between pt-4">
                  <div>
                    {selectedInvoice && (
                      <button
                        type="button"
                        onClick={() => handleDelete(selectedInvoice.id)}
                        className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors text-sm font-medium"
                      >
                        Delete Invoice
                      </button>
                    )}
                  </div>
                  <div className="flex space-x-3">
                    <button
                      type="button"
                      onClick={closeModal}
                      className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition-colors text-sm font-medium"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
                    >
                      {selectedInvoice ? 'Update Invoice' : 'Create Invoice'}
                    </button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Calendar Component
const CalendarPage = () => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [events, setEvents] = useState([]);
  const [showEventModal, setShowEventModal] = useState(false);
  const [selectedDate, setSelectedDate] = useState(null);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [contacts, setContacts] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);

  // Event form state
  const [eventForm, setEventForm] = useState({
    title: '',
    description: '',
    start_date: '',
    end_date: '',
    event_type: 'meeting',
    related_id: '',
    related_type: '',
    location: '',
    all_day: false,
    reminder_minutes: 30
  });

  // Check for new parameter and open modal
  const location = useLocation();
  useEffect(() => {
    const urlParams = new URLSearchParams(location.search);
    if (urlParams.get('new') === 'true') {
      openEventModal();
    }
  }, [location]);

  // Fetch data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [eventsRes, contactsRes, accountsRes] = await Promise.all([
          axios.get(`${API}/calendar/events`, { withCredentials: true }),
          axios.get(`${API}/contacts`, { withCredentials: true }),
          axios.get(`${API}/accounts`, { withCredentials: true })
        ]);
        
        setEvents(eventsRes.data);
        setContacts(contactsRes.data);
        setAccounts(accountsRes.data);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Date navigation
  const navigateMonth = (direction) => {
    const newDate = new Date(currentDate);
    newDate.setMonth(currentDate.getMonth() + direction);
    setCurrentDate(newDate);
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };

  // Get calendar days for current month
  const getCalendarDays = () => {
    const firstDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
    const lastDay = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - firstDay.getDay());
    
    const days = [];
    const current = new Date(startDate);
    
    // Generate 42 days (6 weeks)
    for (let i = 0; i < 42; i++) {
      days.push(new Date(current));
      current.setDate(current.getDate() + 1);
    }
    
    return days;
  };

  // Get events for a specific date
  const getEventsForDate = (date) => {
    const dateStr = date.toDateString();
    return events.filter(event => {
      const eventDate = new Date(event.start_date);
      return eventDate.toDateString() === dateStr;
    });
  };

  // Handle event form
  const openEventModal = (date = null, event = null) => {
    if (event) {
      // Edit existing event
      const startDate = new Date(event.start_date);
      const endDate = new Date(event.end_date);
      setEventForm({
        ...event,
        start_date: startDate.toISOString().slice(0, 16),
        end_date: endDate.toISOString().slice(0, 16)
      });
      setSelectedEvent(event);
    } else {
      // Create new event
      const selectedDateTime = date || new Date();
      selectedDateTime.setHours(9, 0, 0, 0);
      const endDateTime = new Date(selectedDateTime);
      endDateTime.setHours(10, 0, 0, 0);
      
      setEventForm({
        title: '',
        description: '',
        start_date: selectedDateTime.toISOString().slice(0, 16),
        end_date: endDateTime.toISOString().slice(0, 16),
        event_type: 'meeting',
        related_id: '',
        related_type: '',
        location: '',
        all_day: false,
        reminder_minutes: 30
      });
      setSelectedEvent(null);
    }
    setSelectedDate(date);
    setShowEventModal(true);
  };

  const closeEventModal = () => {
    setShowEventModal(false);
    setSelectedEvent(null);
    setSelectedDate(null);
  };

  const handleEventSubmit = async (e) => {
    e.preventDefault();
    try {
      const eventData = {
        ...eventForm,
        start_date: new Date(eventForm.start_date).toISOString(),
        end_date: new Date(eventForm.end_date).toISOString()
      };

      if (selectedEvent) {
        // Update existing event
        await axios.put(`${API}/calendar/events/${selectedEvent.id}`, eventData, { withCredentials: true });
        setEvents(events.map(e => e.id === selectedEvent.id ? { ...selectedEvent, ...eventData } : e));
      } else {
        // Create new event
        const response = await axios.post(`${API}/calendar/events`, eventData, { withCredentials: true });
        setEvents([...events, response.data]);
      }
      
      closeEventModal();
    } catch (error) {
      console.error('Error saving event:', error);
    }
  };

  const handleEventDelete = async (eventId) => {
    if (window.confirm('Are you sure you want to delete this event?')) {
      try {
        await axios.delete(`${API}/calendar/events/${eventId}`, { withCredentials: true });
        setEvents(events.filter(e => e.id !== eventId));
        closeEventModal();
      } catch (error) {
        console.error('Error deleting event:', error);
      }
    }
  };

  const eventTypeColors = {
    meeting: 'bg-blue-100 text-blue-800 border-l-4 border-blue-500',
    invoice_due: 'bg-red-100 text-red-800 border-l-4 border-red-500',
    deadline: 'bg-orange-100 text-orange-800 border-l-4 border-orange-500',
    call: 'bg-green-100 text-green-800 border-l-4 border-green-500',
  };

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-gray-200 rounded w-48"></div>
        <div className="h-96 bg-gray-200 rounded"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Calendar Header */}
      <div className="flex flex-col items-center gap-4">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">Calendar</h1>
          <p className="text-gray-600">Manage your events and schedule</p>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => navigateMonth(-1)}
            className="p-2 hover:bg-gray-100 rounded-md transition-colors"
            title="Previous month"
          >
            ← 
          </button>
          <button
            onClick={goToToday}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
          >
            Today
          </button>
          <button
            onClick={() => navigateMonth(1)}
            className="p-2 hover:bg-gray-100 rounded-md transition-colors"
            title="Next month"
          >
            →
          </button>
          <button
            onClick={() => openEventModal()}
            className="ml-4 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors text-sm font-medium"
          >
            + New Event
          </button>
        </div>
      </div>

      {/* Month/Year Display */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          {currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
        </h2>
      </div>

      {/* Calendar View Toggle */}
      <div className="flex justify-center mb-4">
        <div className="bg-white rounded-lg shadow border p-1 flex">
          <button
            onClick={() => setViewMode('calendar')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              viewMode === 'calendar' 
                ? 'bg-blue-600 text-white' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            📅 Calendar View
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              viewMode === 'list' 
                ? 'bg-blue-600 text-white' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            📋 List View
          </button>
        </div>
      </div>

      {viewMode === 'calendar' ? (
        /* Calendar Grid */
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {/* Week headers */}
          <div className="grid grid-cols-7 gap-0 bg-gray-50 border-b">
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
              <div key={day} className="p-3 text-center text-sm font-medium text-gray-700">
                {day}
              </div>
            ))}
          </div>
          
          {/* Calendar days */}
          <div className="grid grid-cols-7 gap-0">
            {getCalendarDays().map((date, index) => {
              const isCurrentMonth = date.getMonth() === currentDate.getMonth();
              const isToday = date.toDateString() === new Date().toDateString();
              const dayEvents = getEventsForDate(date);
              
              return (
                <div
                  key={index}
                  className={`min-h-[120px] p-2 border-r border-b border-gray-200 cursor-pointer hover:bg-gray-50 transition-colors ${
                    !isCurrentMonth ? 'bg-gray-50 text-gray-400' : ''
                  }`}
                  onClick={() => openEventModal(date)}
                >
                  <div className="flex justify-between items-start mb-1">
                    <span className={`text-sm font-medium ${
                      isToday ? 'bg-blue-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs' : ''
                    }`}>
                      {date.getDate()}
                    </span>
                  </div>
                  
                  <div className="space-y-1">
                    {dayEvents.slice(0, 3).map(event => (
                      <div
                        key={event.id}
                        className={`text-xs p-1 rounded truncate cursor-pointer ${eventTypeColors[event.event_type] || eventTypeColors.meeting}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          openEventModal(date, event);
                        }}
                        title={event.title}
                      >
                        {event.title}
                      </div>
                    ))}
                    {dayEvents.length > 3 && (
                      <div className="text-xs text-gray-500 pl-1">
                        +{dayEvents.length - 3} more
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        /* Events List Table */
        <div className="bg-white rounded-lg shadow border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Event Title
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date & Time
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Related To
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Location
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {events.sort((a, b) => new Date(b.start_date) - new Date(a.start_date)).map((event) => {
                  const startDate = new Date(event.start_date);
                  const endDate = new Date(event.end_date);
                  const duration = Math.round((endDate - startDate) / (1000 * 60)); // in minutes
                  
                  return (
                    <tr key={event.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <div className="font-medium text-gray-900">{event.title}</div>
                        {event.description && (
                          <div className="text-sm text-gray-500 truncate max-w-32">
                            {event.description}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          event.event_type === 'meeting' ? 'bg-blue-100 text-blue-800' :
                          event.event_type === 'call' ? 'bg-green-100 text-green-800' :
                          event.event_type === 'deadline' ? 'bg-orange-100 text-orange-800' :
                          event.event_type === 'invoice_due' ? 'bg-red-100 text-red-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {event.event_type.replace('_', ' ').toUpperCase()}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                        <div>{startDate.toLocaleDateString()}</div>
                        <div className="text-xs text-gray-500">
                          {event.all_day ? 'All Day' : `${startDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                        {event.all_day ? 'All Day' : `${duration} min`}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                        {event.related_type && event.related_id ? (
                          <span className="text-blue-600">
                            {event.related_type === 'contact' ? '👤 Contact' : '🏢 Account'}
                          </span>
                        ) : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                        {event.location || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-500">
                        {new Date(event.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-medium">
                        <button
                          onClick={() => openEventModal(null, event)}
                          className="text-blue-600 hover:text-blue-900 mr-3"
                          title="Edit Event"
                        >
                          ✏️ Edit
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Event Modal */}
      {showEventModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  {selectedEvent ? 'Edit Event' : 'New Event'}
                </h3>
                <button
                  onClick={closeEventModal}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                >
                  ×
                </button>
              </div>

              <form onSubmit={handleEventSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Event Title *
                  </label>
                  <input
                    type="text"
                    required
                    value={eventForm.title}
                    onChange={(e) => setEventForm({...eventForm, title: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter event title"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Event Type
                  </label>
                  <select
                    value={eventForm.event_type}
                    onChange={(e) => setEventForm({...eventForm, event_type: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="meeting">Meeting</option>
                    <option value="call">Phone Call</option>
                    <option value="deadline">Deadline</option>
                    <option value="invoice_due">Invoice Due</option>
                  </select>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Start Date & Time *
                    </label>
                    <input
                      type="datetime-local"
                      required
                      value={eventForm.start_date}
                      onChange={(e) => setEventForm({...eventForm, start_date: e.target.value})}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      End Date & Time *
                    </label>
                    <input
                      type="datetime-local"
                      required
                      value={eventForm.end_date}
                      onChange={(e) => setEventForm({...eventForm, end_date: e.target.value})}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Location
                  </label>
                  <input
                    type="text"
                    value={eventForm.location}
                    onChange={(e) => setEventForm({...eventForm, location: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter location or meeting link"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Related To
                  </label>
                  <div className="flex gap-2">
                    <select
                      value={eventForm.related_type}
                      onChange={(e) => {
                        setEventForm({...eventForm, related_type: e.target.value, related_id: ''});
                      }}
                      className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">None</option>
                      <option value="contact">Contact</option>
                      <option value="account">Account</option>
                    </select>
                    {eventForm.related_type && (
                      <select
                        value={eventForm.related_id}
                        onChange={(e) => setEventForm({...eventForm, related_id: e.target.value})}
                        className="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="">Select {eventForm.related_type}</option>
                        {(eventForm.related_type === 'contact' ? contacts : accounts).map(item => (
                          <option key={item.id} value={item.id}>
                            {item.name}
                          </option>
                        ))}
                      </select>
                    )}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={eventForm.description}
                    onChange={(e) => setEventForm({...eventForm, description: e.target.value})}
                    rows={3}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Event description..."
                  />
                </div>

                <div className="flex items-center space-x-4">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={eventForm.all_day}
                      onChange={(e) => setEventForm({...eventForm, all_day: e.target.checked})}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">All day</span>
                  </label>
                  
                  {!eventForm.all_day && (
                    <div className="flex items-center">
                      <label className="text-sm text-gray-700 mr-2">Reminder:</label>
                      <select
                        value={eventForm.reminder_minutes}
                        onChange={(e) => setEventForm({...eventForm, reminder_minutes: parseInt(e.target.value)})}
                        className="border border-gray-300 rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value={0}>None</option>
                        <option value={15}>15 min</option>
                        <option value={30}>30 min</option>
                        <option value={60}>1 hour</option>
                        <option value={1440}>1 day</option>
                      </select>
                    </div>
                  )}
                </div>

                <div className="flex justify-between pt-4">
                  <div>
                    {selectedEvent && (
                      <button
                        type="button"
                        onClick={() => handleEventDelete(selectedEvent.id)}
                        className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors text-sm font-medium"
                      >
                        Delete Event
                      </button>
                    )}
                  </div>
                  <div className="flex space-x-3">
                    <button
                      type="button"
                      onClick={closeEventModal}
                      className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition-colors text-sm font-medium"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
                    >
                      {selectedEvent ? 'Update Event' : 'Create Event'}
                    </button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/" element={<LoginPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <Layout>
                  <Dashboard />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/contacts" element={
              <ProtectedRoute>
                <Layout>
                  <ContactsPage />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/accounts" element={
              <ProtectedRoute>
                <Layout>
                  <AccountsPage />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/products" element={
              <ProtectedRoute>
                <Layout>
                  <ProductsPage />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/invoices" element={
              <ProtectedRoute>
                <Layout>
                  <InvoicesPage />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/calendar" element={
              <ProtectedRoute>
                <Layout>
                  <CalendarPage />
                </Layout>
              </ProtectedRoute>
            } />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;