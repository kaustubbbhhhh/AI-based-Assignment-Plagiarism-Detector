/**
 * Centralized API Client.
 *
 * Configured for production-ready, cookie-based session authentication:
 * - Automatically sends credentials (HttpOnly session cookies) on all requests (`credentials: 'include'`).
 * - Automatically reads and attaches `X-CSRF-Token` header for state-changing requests.
 * - Handles 401 Unauthorized globally by broadcasting an auth event to synchronize tabs and redirect to login.
 */

const API_URL = import.meta.env.VITE_API_URL || '';


/**
 * Utility to read a cookie value by name.
 */
export function getCookie(name) {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(new RegExp('(^|;\\s*)(' + name + ')=([^;]*)'));
  return match ? decodeURIComponent(match[3]) : null;
}

/**
 * Dispatches an event when any request receives 401 Unauthorized,
 * allowing the AuthContext to clear local state without polling loops.
 */
function notifyUnauthorized() {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('auth:unauthorized'));
  }
}

/**
 * Base fetch wrapper with credential and CSRF header handling.
 */
async function request(endpoint, options = {}) {
  const url = endpoint.startsWith('http') ? endpoint : `${API_URL}${endpoint}`;
  
  const headers = {
    ...options.headers,
  };

  // Attach X-CSRF-Token header for state-changing requests if csrf_token cookie exists
  const method = (options.method || 'GET').toUpperCase();
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    const csrfToken = getCookie('csrf_token');
    if (csrfToken && !headers['X-CSRF-Token']) {
      headers['X-CSRF-Token'] = csrfToken;
    }
  }

  // Set default JSON Content-Type unless body is FormData
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const config = {
    ...options,
    headers,
    credentials: 'include', // Crucial: enables browser to send and receive HttpOnly session cookies
  };

  try {
    const response = await fetch(url, config);

    // Global 401 Unauthorized interception
    if (response.status === 401) {
      // Exempt login and me endpoints to prevent recursive loops on initial load
      if (!endpoint.includes('/api/auth/login') && !endpoint.includes('/api/auth/me')) {
        notifyUnauthorized();
      }
    }

    return response;
  } catch (error) {
    if (error.name === 'TypeError' || error.message?.toLowerCase().includes('fetch')) {
      throw new Error('Unable to connect to the backend server. Please verify backend is running.');
    }
    throw error;
  }
}

export const api = {
  request,
  get: (endpoint, options = {}) => request(endpoint, { ...options, method: 'GET' }),
  post: (endpoint, body, options = {}) =>
    request(endpoint, {
      ...options,
      method: 'POST',
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),
  put: (endpoint, body, options = {}) =>
    request(endpoint, {
      ...options,
      method: 'PUT',
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),
  patch: (endpoint, body, options = {}) =>
    request(endpoint, {
      ...options,
      method: 'PATCH',
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),
  delete: (endpoint, options = {}) => request(endpoint, { ...options, method: 'DELETE' }),
  upload: (endpoint, formData, options = {}) =>
    request(endpoint, {
      ...options,
      method: 'POST',
      body: formData,
    }),
  baseUrl: API_URL,
};

export default api;
