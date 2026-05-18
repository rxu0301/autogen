import React from 'react';

interface Props {
  onGenerate: () => void;
  loading: boolean;
}

export default function SummaryGenerator({ onGenerate, loading }: Props) {
  return (
    <div>
      <p style={{ margin: '0 0 14px', fontSize: 13, color: '#6b7280' }}>
        뉴스 내용을 500~900자 분량의 읽기용 요약본으로 생성합니다.
        심층분석형 / 핵심요약형 / 스토리텔링형 3가지 버전을 제공합니다.
      </p>
      <button
        onClick={onGenerate}
        disabled={loading}
        style={{
          width: '100%', padding: '13px',
          background: loading ? '#e5e7eb' : '#6366f1',
          color: loading ? '#9ca3af' : '#fff',
          border: 'none', borderRadius: 10,
          fontSize: 15, fontWeight: 600,
          cursor: loading ? 'not-allowed' : 'pointer',
          transition: 'background 0.15s',
        }}
      >
        {loading ? '요약본 생성 중...' : '📄 요약본 생성'}
      </button>
    </div>
  );
}
