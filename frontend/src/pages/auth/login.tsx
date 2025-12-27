import { useState } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import Link from 'next/link';
import { Eye, EyeOff, TrendingUp } from 'lucide-react';
import { authAPI } from '@/services/api';

export default function Login() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const data = await authAPI.login(email, password);
      localStorage.setItem('token', data.access_token);
      
      // Fetch user info
      const user = await authAPI.getMe();
      localStorage.setItem('user', JSON.stringify(user));
      
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid email or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>Login | Finance Copilot</title>
      </Head>
      
      <div style={{ minHeight: '100vh', background: 'var(--color-bg)' }} className="flex items-center justify-center">
        <div style={{ width: '100%', maxWidth: 400 }}>
          {/* Logo */}
          <div style={{ textAlign: 'center', marginBottom: 32 }}>
            <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 64, height: 64, background: 'var(--color-white)', borderRadius: 16, boxShadow: '0 2px 8px 0 rgba(124,58,237,0.08)', marginBottom: 16 }}>
              <TrendingUp style={{ width: 32, height: 32, color: 'var(--color-violet)' }} />
            </div>
            <h1 style={{ fontSize: 28, fontWeight: 700, color: 'var(--color-white)' }}>Finance Copilot</h1>
            <p style={{ color: 'var(--color-violet)', marginTop: 4 }}>AI-Powered Portfolio Management</p>
          </div>

          {/* Login Card */}
          <div className="card" style={{ borderRadius: 16, boxShadow: '0 2px 16px 0 rgba(124,58,237,0.10)', padding: 32, background: 'var(--color-bg-alt)' }}>
            <h2 style={{ fontSize: 24, fontWeight: 700, color: 'var(--color-white)', marginBottom: 24 }}>Welcome back</h2>

            {error && (
              <div style={{ marginBottom: 16, padding: 12, background: 'var(--color-negative)', color: 'var(--color-white)', borderRadius: 8, fontSize: 14 }}>
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div>
                <label style={{ display: 'block', fontSize: 14, fontWeight: 500, color: 'var(--color-text-muted)', marginBottom: 4 }}>
                  Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input"
                  placeholder="you@example.com"
                  required
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: 14, fontWeight: 500, color: 'var(--color-text-muted)', marginBottom: 4 }}>
                  Password
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="input"
                    style={{ paddingRight: 40 }}
                    placeholder="••••••••"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer' }}
                  >
                    {showPassword ? <EyeOff style={{ width: 20, height: 20 }} /> : <Eye style={{ width: 20, height: 20 }} />}
                  </button>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <label style={{ display: 'flex', alignItems: 'center' }}>
                  <input type="checkbox" style={{ borderRadius: 4, border: '1px solid var(--color-border)', accentColor: 'var(--color-violet)' }} />
                  <span style={{ marginLeft: 8, fontSize: 14, color: 'var(--color-text-muted)' }}>Remember me</span>
                </label>
                <Link href="/auth/forgot-password" style={{ fontSize: 14, color: 'var(--color-violet)', textDecoration: 'underline' }}>
                  Forgot password?
                </Link>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn"
                style={{ width: '100%', background: 'var(--color-violet)', color: 'var(--color-white)', fontWeight: 600, fontSize: 16, padding: '12px 0', borderRadius: 8, border: 'none', cursor: 'pointer' }}
              >
                {loading ? 'Signing in...' : 'Sign in'}
              </button>
            </form>

            <div style={{ marginTop: 24, textAlign: 'center' }}>
              <p style={{ color: 'var(--color-text-muted)' }}>
                Don't have an account?{' '}
                <Link href="/auth/register" style={{ color: 'var(--color-violet)', fontWeight: 500, textDecoration: 'underline' }}>
                  Sign up
                </Link>
              </p>
            </div>
          </div>

          {/* Demo Account */}
          <div style={{ marginTop: 16, textAlign: 'center' }}>
            <p style={{ color: 'var(--color-violet)', fontSize: 14 }}>
              Demo: demo@example.com / demo123
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
