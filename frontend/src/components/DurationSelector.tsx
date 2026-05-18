import React from 'react';

const DURATIONS = [
  { value: '20초', label: '20초', desc: '280~340자' },
  { value: '30초', label: '30초', desc: '430~520자' },
  { value: '1분',  label: '1분',  desc: '860~1040자' },
] as const;

type Duration = '20초' | '30초' | '1분';
type Language = 'ko' | 'en';

interface Props {
  selected: Duration;
  onChange: (d: Duration) => void;
  language: Language;
  onLanguageChange: (l: Language) => void;
  onGenerateSummary: () => void;
  onGenerateScript: () => void;
  summaryLoading: boolean;
  scriptLoading: boolean;
}

export default function DurationSelector({
  selected, onChange, language, onLanguageChange,
  onGenerateSummary, onGenerateScript,
  summaryLoading, scriptLoading,
}: Props) {
  return (
    <div>
      {/* 언어 선택 */}
      <p style={{ margin: '0 0 10px', fontSize: 13, color: '#6b7280' }}>출력 언어를 선택하세요.</p>
      <div style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
        {([
          { value: 'ko', label: '한국어', flag: '🇰🇷', desc: '국내 뉴스 / 한국어 출력' },
          { value: 'en', label: 'English', flag: '🇺🇸', desc: '해외 뉴스 / 영문 출력' },
        ] as const).map((l) => {
          const active = language === l.value;
          return (
            <button
              key={l.value}
              onClick={() => onLanguageChange(l.value)}
              style={{
                flex: 1, padding: '12px 8px',
                border: `2px solid ${active ? '#0ea5e9' : '#e5e7eb'}`,
                borderRadius: 10,
                background: active ? '#f0f9ff' : '#fff',
                color: active ? '#0369a1' : '#374151',
                fontWeight: active ? 700 : 500,
                fontSize: 14, cursor: 'pointer', transition: 'all 0.15s', textAlign: 'center',
              }}
            >
              <div style={{ fontSize: 20, marginBottom: 2 }}>{l.flag}</div>
              <div>{l.label}</div>
              <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 2 }}>{l.desc}</div>
            </button>
          );
        })}
      </div>

      {/* 구분선 */}
      <div style={{ borderTop: '1px solid #f3f4f6', margin: '0 0 18px' }} />

      {/* 요약본 생성 */}
      <div style={{
        padding: '16px',
        background: '#f8faff',
        borderRadius: 10,
        border: '1.5px solid #e0e7ff',
        marginBottom: 14,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: '#1e1b4b' }}>📄 뉴스 요약본</div>
            <div style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>
              읽기용 텍스트 · 500~900자 · 3가지 스타일
            </div>
          </div>
          <button
            onClick={onGenerateSummary}
            disabled={summaryLoading}
            style={{
              padding: '9px 18px',
              background: summaryLoading ? '#e5e7eb' : '#6366f1',
              color: summaryLoading ? '#9ca3af' : '#fff',
              border: 'none', borderRadius: 8,
              fontSize: 13, fontWeight: 600,
              cursor: summaryLoading ? 'not-allowed' : 'pointer',
              whiteSpace: 'nowrap',
            }}
          >
            {summaryLoading ? '생성 중...' : '📄 요약본 생성'}
          </button>
        </div>
      </div>

      {/* 스크립트 생성 */}
      <div style={{
        padding: '16px',
        background: '#fdf8ff',
        borderRadius: 10,
        border: '1.5px solid #ede9fe',
      }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: '#1e1b4b', marginBottom: 10 }}>
          🎙️ 뉴스 스크립트 (낭독용)
        </div>
        <p style={{ margin: '0 0 10px', fontSize: 12, color: '#6b7280' }}>
          방송 낭독 분량을 선택하세요.
        </p>
        <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
          {DURATIONS.map((d) => {
            const active = selected === d.value;
            return (
              <button
                key={d.value}
                onClick={() => onChange(d.value)}
                style={{
                  flex: 1, padding: '10px 6px',
                  border: `2px solid ${active ? '#7c3aed' : '#e5e7eb'}`,
                  borderRadius: 8,
                  background: active ? '#fdf4ff' : '#fff',
                  color: active ? '#6d28d9' : '#374151',
                  fontWeight: active ? 700 : 500,
                  fontSize: 13, cursor: 'pointer', transition: 'all 0.15s', textAlign: 'center',
                }}
              >
                <div style={{ fontSize: 16, marginBottom: 2 }}>
                  {d.value === '20초' ? '⚡' : d.value === '30초' ? '📺' : '🎬'}
                </div>
                <div>{d.label}</div>
                <div style={{ fontSize: 10, color: '#9ca3af', marginTop: 1 }}>{d.desc}</div>
              </button>
            );
          })}
        </div>
        <button
          onClick={onGenerateScript}
          disabled={scriptLoading}
          style={{
            width: '100%', padding: '11px',
            background: scriptLoading ? '#e5e7eb' : '#7c3aed',
            color: scriptLoading ? '#9ca3af' : '#fff',
            border: 'none', borderRadius: 8,
            fontSize: 13, fontWeight: 600,
            cursor: scriptLoading ? 'not-allowed' : 'pointer',
          }}
        >
          {scriptLoading ? '스크립트 생성 중...' : '🎙️ 스크립트 생성'}
        </button>
      </div>
    </div>
  );
}
