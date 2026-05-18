import React from 'react';

const DURATIONS = [
  { value: '20초', icon: '⚡', desc: '170~230자' },
  { value: '30초', icon: '📺', desc: '260~360자' },
  { value: '1분',  icon: '🎬', desc: '550~750자' },
] as const;

type Duration = '20초' | '30초' | '1분';

interface Props {
  selected: Duration;
  onChange: (d: Duration) => void;
  onGenerate: () => void;
  loading: boolean;
}

export default function ScriptGenerator({ selected, onChange, onGenerate, loading }: Props) {
  return (
    <div>
      <p style={{ margin: '0 0 12px', fontSize: 13, color: '#6b7280' }}>
        방송 낭독용 스크립트를 생성합니다. 분량을 선택하세요.
        정보형 / 감성형 / 자극형 3가지 버전을 제공합니다.
      </p>

      {/* 분량 선택 */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 14 }}>
        {DURATIONS.map((d) => {
          const active = selected === d.value;
          return (
            <button
              key={d.value}
              onClick={() => onChange(d.value)}
              style={{
                flex: 1, padding: '12px 8px',
                border: `2px solid ${active ? '#7c3aed' : '#e5e7eb'}`,
                borderRadius: 10,
                background: active ? '#fdf4ff' : '#fff',
                color: active ? '#6d28d9' : '#374151',
                fontWeight: active ? 700 : 500,
                fontSize: 14, cursor: 'pointer',
                transition: 'all 0.15s', textAlign: 'center',
              }}
            >
              <div style={{ fontSize: 20, marginBottom: 2 }}>{d.icon}</div>
              <div>{d.value}</div>
              <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 2 }}>{d.desc}</div>
            </button>
          );
        })}
      </div>

      <button
        onClick={onGenerate}
        disabled={loading}
        style={{
          width: '100%', padding: '13px',
          background: loading ? '#e5e7eb' : '#7c3aed',
          color: loading ? '#9ca3af' : '#fff',
          border: 'none', borderRadius: 10,
          fontSize: 15, fontWeight: 600,
          cursor: loading ? 'not-allowed' : 'pointer',
          transition: 'background 0.15s',
        }}
      >
        {loading ? '스크립트 생성 중...' : '🎙️ 스크립트 생성'}
      </button>
    </div>
  );
}
