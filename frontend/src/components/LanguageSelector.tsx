import React from 'react';

type Language = 'ko' | 'en';

interface Props {
  language: Language;
  onChange: (l: Language) => void;
}

export default function LanguageSelector({ language, onChange }: Props) {
  return (
    <div>
      <p style={{ margin: '0 0 10px', fontSize: 13, color: '#6b7280' }}>
        출력 언어를 선택하세요.
      </p>
      <div style={{ display: 'flex', gap: 10 }}>
        {([
          { value: 'ko', flag: '🇰🇷', label: '한국어', desc: '국내 뉴스 / 한국어 출력' },
          { value: 'en', flag: '🇺🇸', label: 'English', desc: '해외 뉴스 / 영문 출력' },
        ] as const).map((l) => {
          const active = language === l.value;
          return (
            <button
              key={l.value}
              onClick={() => onChange(l.value)}
              style={{
                flex: 1, padding: '12px 8px',
                border: `2px solid ${active ? '#0ea5e9' : '#e5e7eb'}`,
                borderRadius: 10,
                background: active ? '#f0f9ff' : '#fff',
                color: active ? '#0369a1' : '#374151',
                fontWeight: active ? 700 : 500,
                fontSize: 14, cursor: 'pointer',
                transition: 'all 0.15s', textAlign: 'center',
              }}
            >
              <div style={{ fontSize: 20, marginBottom: 2 }}>{l.flag}</div>
              <div>{l.label}</div>
              <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 2 }}>{l.desc}</div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
