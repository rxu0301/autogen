import React, { useState } from 'react';

interface Props {
  onSearch: (topic: string) => void;
  loading: boolean;
}

export default function NewsSearch({ onSearch, loading }: Props) {
  const [topic, setTopic] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (topic.trim()) onSearch(topic.trim());
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 10 }}>
      <input
        type="text"
        value={topic}
        onChange={(e) => setTopic(e.target.value)}
        placeholder="검색할 주제를 입력하세요 (예: 인공지능, 기후변화)"
        disabled={loading}
        style={{
          flex: 1,
          padding: '12px 16px',
          border: '1.5px solid #d1d5db',
          borderRadius: 10,
          fontSize: 15,
          outline: 'none',
          color: '#111827',
          background: loading ? '#f9fafb' : '#fff',
          transition: 'border-color 0.15s',
        }}
        onFocus={(e) => (e.target.style.borderColor = '#6366f1')}
        onBlur={(e) => (e.target.style.borderColor = '#d1d5db')}
      />
      <button
        type="submit"
        disabled={loading || !topic.trim()}
        style={{
          padding: '12px 24px',
          background: loading || !topic.trim() ? '#e5e7eb' : '#6366f1',
          color: loading || !topic.trim() ? '#9ca3af' : '#fff',
          border: 'none',
          borderRadius: 10,
          fontSize: 15,
          fontWeight: 600,
          cursor: loading || !topic.trim() ? 'not-allowed' : 'pointer',
          transition: 'background 0.15s',
          whiteSpace: 'nowrap',
        }}
      >
        {loading ? '검색 중...' : '🔍 뉴스 검색'}
      </button>
    </form>
  );
}
