import React, { useState } from 'react';
import ContentForm from './components/ContentForm';
import ContentResult from './components/ContentResult';
import { generateContent } from './api/content';
import { ContentRequest, ContentResponse, ApiError } from './types/content';

const styles = {
  page: {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #f0f4ff 0%, #faf5ff 100%)',
    padding: '40px 16px 80px',
    fontFamily:
      "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
  },
  container: {
    maxWidth: 680,
    margin: '0 auto',
  },
  header: {
    marginBottom: 32,
    textAlign: 'center' as const,
  },
  title: {
    fontSize: 28,
    fontWeight: 800,
    color: '#1e1b4b',
    margin: '0 0 8px',
    letterSpacing: '-0.02em',
  },
  subtitle: {
    fontSize: 15,
    color: '#6b7280',
    margin: 0,
    lineHeight: 1.5,
  },
  card: {
    background: '#fff',
    borderRadius: 16,
    padding: '28px 32px',
    boxShadow:
      '0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(99,102,241,0.08)',
    border: '1px solid rgba(99,102,241,0.1)',
  },
  errorBox: {
    marginTop: 16,
    padding: '12px 16px',
    background: '#fef2f2',
    borderRadius: 10,
    color: '#b91c1c',
    fontSize: 14,
    border: '1px solid #fecaca',
    display: 'flex',
    alignItems: 'flex-start',
    gap: 8,
  },
  errorIcon: {
    flexShrink: 0,
    marginTop: 1,
  },
  loadingOverlay: {
    marginTop: 24,
    padding: '32px',
    textAlign: 'center' as const,
    color: '#6b7280',
    fontSize: 14,
  },
  spinner: {
    display: 'inline-block',
    width: 24,
    height: 24,
    border: '3px solid #e5e7eb',
    borderTopColor: '#6366f1',
    borderRadius: '50%',
    animation: 'spin 0.8s linear infinite',
    marginBottom: 12,
  },
  footer: {
    marginTop: 40,
    textAlign: 'center' as const,
    fontSize: 12,
    color: '#d1d5db',
  },
};

// Inject keyframe animation for spinner
if (typeof document !== 'undefined') {
  const styleEl = document.createElement('style');
  styleEl.textContent = `@keyframes spin { to { transform: rotate(360deg); } }`;
  document.head.appendChild(styleEl);
}

export default function App() {
  const [result, setResult] = useState<ContentResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (req: ContentRequest) => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await generateContent(req);
      setResult(res);
    } catch (e: unknown) {
      const apiErr = e as ApiError;
      setError(apiErr?.message || '오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.container}>
        <div style={styles.header}>
          <h1 style={styles.title}>🎬 숏폼 콘텐츠 에이전트</h1>
          <p style={styles.subtitle}>
            관심사와 목적을 입력하면 Ollama LLM이 바이럴 콘텐츠 기획을 생성합니다.
          </p>
        </div>

        <div style={styles.card}>
          <ContentForm onSubmit={handleSubmit} loading={loading} />
        </div>

        {error && (
          <div style={styles.errorBox}>
            <span style={styles.errorIcon}>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        {loading && (
          <div style={styles.loadingOverlay}>
            <div style={styles.spinner} />
            <div>콘텐츠를 생성하고 있습니다...</div>
          </div>
        )}

        {result && !loading && <ContentResult result={result} />}

        <div style={styles.footer}>
          Powered by Ollama · NestJS BFF · FastAPI
        </div>
      </div>
    </div>
  );
}
