import '@/styles/globals.css';
import '@/styles/theme.css';
import type { AppProps } from 'next/app';
import { useState, useEffect } from 'react';
import Layout from '@/components/Layout';

export default function App({ Component, pageProps }: AppProps) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Check for auth token
    const token = localStorage.getItem('token');
    setIsAuthenticated(!!token);
  }, []);

  return (
    <Layout isAuthenticated={isAuthenticated} setIsAuthenticated={setIsAuthenticated}>
      <Component {...pageProps} isAuthenticated={isAuthenticated} setIsAuthenticated={setIsAuthenticated} />
    </Layout>
  );
}
