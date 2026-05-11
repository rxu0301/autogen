import React, { useState } from 'react';
import { ContentResponse } from '../types/content';

interface Props {
  result: ContentResponse;
}

const styles = {
  container: {
    marginTop: 28,
    borderRadius: 12,
    overflow: 'hidden',
    border: '1px solid #e5e7eb',
    background: '#fff',
    boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '12px 16px',
    background: '#f9fafb',
    borderBottom: '1px solid #e5e7eb',
  },
  badgeRow: {
    display: 'flex',
    gap: 8,
    alignItems: 'center',
  },
  badgeLlm: {
    padding: '3px 10px',
    borderRadius: 20,
    fontSize: 12,
    fontWeight: 600,
    background: '#dcfce7',
    color: '#15803d',
    border: '1px solid #bbf7d0',
  },
  badgeFallback: {
    padding: '3px 10px',
    borderRadius: 20,
    fontSize: 12,
    fontWeight: 600,
    background: '#fef9c3',
    color: '#854d0e',
    border: '1px solid #fde68a',
  },
  modelLabel: {
    fontSize: 12,
    color: '#9ca3af',
  },
  copyBtn: {
    padding: '6px 14px',
    borderRadius: 8,
    border: '1px solid #d1d5db',
    background: '#fff',
    fontSize: 13,
    fontWeight: 500,
    cursor: 'pointer',
    color: '#374151',
    transition: 'background 0.15s, border-color 0.15s',
    display: 'flex',
    alignItems: 'center',
    gap: 6,
  },
  copyBtnSuccess: {
    background: '#dcfce7',
    borderColor: '#86efac',
    color: '#15803d',
  },
  pre: {
    margin: 0,
    padding: '20px',
    background: '#1a1a2e',
    color: '#e2e8f0',
    whiteSpace: 'pre-wrap' as const,
    wordBreak: 'break-word' as const,
    fontSize: 14,
    lineHeight: 1.7,
    fontFamily: "'Menlo', 'Monaco', 'Consolas', monospace",
    minHeight: 120,
  },
};

export default function ContentResult({ result }: Props) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(result.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback for older browsers
      const el = document.createElement('textarea');
      el.value = result.content;
      document.body.appendChild(el);
      el.select();
      document.execCommand('copy');
      document.body.removeChild(el);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div style={styles.badgeRow}>
          <span style={result.source === 'llm' ? styles.badgeLlm : styles.badgeFallback}>
            {result.source === 'llm' ? '🤖 LLM' : '⚡ Fallback'}
          </span>
          {result.model && (
            <span style={styles.modelLabel}>{result.model}</span>
          )}
        </div>
        <button
          onClick={handleCopy}
          style={{
            ...styles.copyBtn,
            ...(copied ? styles.copyBtnSuccess : {}),
          }}
          title="클립보드에 복사"
        >
          {copied ? '✓ 복사됨!' : '📋 복사'}
        </button>
      </div>
      <pre style={styles.pre}>{result.content}</pre>
    </div>
  );
}
