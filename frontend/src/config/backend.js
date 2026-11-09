// Single source of truth for the backend origin used by every API client.
// Create React App inlines REACT_APP_* values at build time, so a value that is
// missing when the bundle is built can never be fixed at runtime. Deployed builds
// must therefore fail loudly instead of quietly talking to the developer's localhost.

export const DEVELOPMENT_BACKEND_URL = 'http://localhost:8001';

export const BACKEND_URL_ERROR_MESSAGE =
  'REACT_APP_BACKEND_URL is not set for this production build, so the app cannot reach the API. ' +
  'Set it to your backend origin (for example https://your-service.onrender.com) in your hosting ' +
  "provider's environment variables and redeploy — Create React App inlines this value at build time.";

const withoutTrailingSlashes = (value) => value.replace(/\/+$/, '');

export const resolveBackendConfig = (rawUrl, nodeEnv = process.env.NODE_ENV) => {
  const configured = withoutTrailingSlashes(String(rawUrl ?? '').trim());

  if (configured) {
    return { baseUrl: configured, error: null };
  }

  if (nodeEnv === 'production') {
    return { baseUrl: '', error: BACKEND_URL_ERROR_MESSAGE };
  }

  return { baseUrl: DEVELOPMENT_BACKEND_URL, error: null };
};

const resolvedConfig = resolveBackendConfig(process.env.REACT_APP_BACKEND_URL, process.env.NODE_ENV);

export const BACKEND_BASE_URL = resolvedConfig.baseUrl;
export const BACKEND_URL_ERROR = resolvedConfig.error;
