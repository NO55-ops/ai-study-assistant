import {
  BACKEND_URL_ERROR_MESSAGE,
  DEVELOPMENT_BACKEND_URL,
  resolveBackendConfig,
} from './backend';

describe('resolveBackendConfig', () => {
  it('uses the configured origin and trims trailing slashes', () => {
    expect(resolveBackendConfig('https://api.example.com/', 'production')).toEqual({
      baseUrl: 'https://api.example.com',
      error: null,
    });
  });

  it('fails fast instead of falling back to localhost in a production build', () => {
    const config = resolveBackendConfig('', 'production');

    expect(config.baseUrl).toBe('');
    expect(config.error).toBe(BACKEND_URL_ERROR_MESSAGE);
    expect(config.error).toContain('REACT_APP_BACKEND_URL');
    expect(config.error).not.toContain('localhost');
  });

  it('treats a whitespace-only value as missing', () => {
    expect(resolveBackendConfig('   ', 'production')).toEqual({
      baseUrl: '',
      error: BACKEND_URL_ERROR_MESSAGE,
    });
  });

  it('normalises a value that only differs by a trailing slash', () => {
    expect(resolveBackendConfig('  https://api.example.com//  ', 'production').baseUrl)
      .toBe('https://api.example.com');
  });

  it('keeps the localhost fallback for development', () => {
    expect(resolveBackendConfig(undefined, 'development')).toEqual({
      baseUrl: DEVELOPMENT_BACKEND_URL,
      error: null,
    });
  });

  it('keeps the localhost fallback for tests', () => {
    expect(resolveBackendConfig(null, 'test').baseUrl).toBe(DEVELOPMENT_BACKEND_URL);
  });
});
