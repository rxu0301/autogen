import React, { useState } from 'react';
import { ThumbnailPrompt } from '../types/content';

interface Props {
  prompts: ThumbnailPrompt[];
  onSave: () => void;
  saving: boolean;
  saved: boolean;
}

const STYLE_META: Record<string, { bg: string; color: string; border: string; icon: string; desc: string }> = {
  '애니메이션': { bg: '#fce7f3', color: '#be185d', border: '#f9a8d4', icon: '🎌', desc: 'Anime / Studio Ghibli 스타일' },
  '실사':       { bg: '#dbeafe', color: '#1d4ed8', border: '#93c5fd', icon: '📷', desc: '시네마틱 실사 사진 스타일' },
  '카툰':       { bg: '#fef9c3', color: '#854d0e', border: '#fde68a', icon: '🎨', desc: '카툰 / 만화 일러스트 스타일' },
};

function ImagePreview({ url, style, alt }: { url: string; style: string; alt: string }) {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);

  return (
    <div style={{
      position: 'relative',
      width: '100%',
      aspectRatio: '16/9',
      background: '#f3f4f6',
      borderRadius: 8,
      overflow: 'hidden',
      border: '1px solid #e5e7eb',
    }}>
      {!loaded && !error && (
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          gap: 8, color: '#9ca3af', fontSize: 13,
        }}>
          <div style={{
            width: 28, height: 28,
            border: '3px solid #e5e7eb',
            borderTopColor: '#6366f1',
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
          }} />
          이미지 생성 중...
        </div>
      )}
      {error && (
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          gap: 6, color: '#9ca3af', fontSize: 12,
        }}>
          <span style={{ fontSize: 28 }}>🖼️</span>
          이미지 생성 실패
          <a href={url} target="_blank" rel="noopener noreferrer"
            style={{ fontSize: 11, color: '#6366f1' }}>
            직접 열기 →
          </a>
        </div>
      )}
      <img
        src={url}
        alt={alt}
        onLoad={() => setLoaded(true)}
        onError={() => setError(true)}
        style={{
          width: '100%', height: '100%',
          objectFit: 'cover',
          display: loaded ? 'block' : 'none',
        }}
      />
    </div>
  );
}

export default function ThumbnailResult({ prompts, onSave, saving, saved }: Props) {
  const [copied, setCopied] = useState<number | null>(null);
  const [lang, setLang] = useState<'en' | 'ko'>('en');
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);

  const handleCopy = async (text: string, ver: number) => {
    try { await navigator.clipboard.writeText(text); }
    catch {
      const el = document.createElement('textarea');
      el.value = text; document.body.appendChild(el);
      el.select(); document.execCommand('copy');
      document.body.removeChild(el);
    }
    setCopied(ver);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <div>
      {/* 안내 + 언어 토글 */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
        <p style={{ margin: 0, fontSize: 13, color: '#6b7280' }}>
          뉴스 장면을 시각화한 이미지 3가지입니다. 마음에 드는 스타일을 선택하세요.
        </p>
        <div style={{ display: 'flex', border: '1px solid #e5e7eb', borderRadius: 8, overflow: 'hidden', flexShrink: 0 }}>
          {(['en', 'ko'] as const).map((l) => (
            <button key={l} onClick={() => setLang(l)} style={{
              padding: '5px 12px', border: 'none',
              background: lang === l ? '#6366f1' : '#fff',
              color: lang === l ? '#fff' : '#374151',
              fontSize: 12, fontWeight: 600, cursor: 'pointer',
            }}>
              {l === 'en' ? '🇺🇸 EN' : '🇰🇷 KO'}
            </button>
          ))}
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {prompts.map((p) => {
          const meta = STYLE_META[p.style] || { bg: '#f3f4f6', color: '#374151', border: '#d1d5db', icon: '🖼️', desc: '' };
          const text = lang === 'en' ? p.prompt_en : p.prompt_ko;
          const isSelected = selectedVersion === p.version;

          return (
            <div key={p.version} style={{
              border: `2px solid ${isSelected ? '#6366f1' : '#e5e7eb'}`,
              borderRadius: 14,
              overflow: 'hidden',
              boxShadow: isSelected ? '0 0 0 3px rgba(99,102,241,0.12)' : 'none',
              transition: 'all 0.15s',
            }}>
              {/* 헤더 */}
              <div style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '11px 14px',
                background: isSelected ? '#f0f0ff' : '#f9fafb',
                borderBottom: '1px solid #e5e7eb',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{
                    padding: '3px 10px', borderRadius: 20, fontSize: 12, fontWeight: 700,
                    background: meta.bg, color: meta.color, border: `1px solid ${meta.border}`,
                  }}>
                    {meta.icon} 버전{p.version} — {p.style}
                  </span>
                  <span style={{ fontSize: 11, color: '#9ca3af' }}>{meta.desc}</span>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button onClick={() => handleCopy(text, p.version)} style={{
                    padding: '5px 10px', border: '1px solid #d1d5db', borderRadius: 6,
                    background: copied === p.version ? '#dcfce7' : '#fff',
                    color: copied === p.version ? '#15803d' : '#374151',
                    fontSize: 11, cursor: 'pointer',
                  }}>
                    {copied === p.version ? '✓ 복사됨' : '📋 복사'}
                  </button>
                  <button onClick={() => setSelectedVersion(isSelected ? null : p.version)} style={{
                    padding: '5px 12px',
                    border: `1px solid ${isSelected ? '#6366f1' : '#d1d5db'}`,
                    borderRadius: 6,
                    background: isSelected ? '#6366f1' : '#fff',
                    color: isSelected ? '#fff' : '#374151',
                    fontSize: 11, fontWeight: 700, cursor: 'pointer',
                  }}>
                    {isSelected ? '✓ 선택됨' : '선택'}
                  </button>
                </div>
              </div>

              {/* 이미지 미리보기 */}
              {p.image_url && (
                <div style={{ padding: '14px 16px 0', background: '#fff' }}>
                  <ImagePreview url={p.image_url} style={p.style} alt={`${p.style} 스타일 썸네일`} />
                  <div style={{ marginTop: 6, marginBottom: 2, textAlign: 'right' }}>
                    <a href={p.image_url} target="_blank" rel="noopener noreferrer"
                      style={{ fontSize: 11, color: '#6366f1', textDecoration: 'none' }}>
                      원본 크기로 보기 →
                    </a>
                  </div>
                </div>
              )}

              {/* 프롬프트 텍스트 */}
              <div style={{
                padding: '12px 16px 14px',
                background: '#1a1a2e',
                color: '#e2e8f0',
                fontSize: 12,
                lineHeight: 1.7,
                fontFamily: "'Menlo', 'Monaco', 'Consolas', monospace",
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}>
                <span style={{ color: '#a78bfa', fontSize: 11, display: 'block', marginBottom: 4 }}>
                  {lang === 'en' ? '// Image Generation Prompt (EN)' : '// 이미지 생성 프롬프트 설명 (KO)'}
                </span>
                {text}
              </div>
            </div>
          );
        })}
      </div>

      {/* 저장 버튼 */}
      <button
        onClick={onSave}
        disabled={saving || saved || !selectedVersion}
        style={{
          marginTop: 20, width: '100%', padding: '13px',
          background: saved ? '#dcfce7' : (saving || !selectedVersion) ? '#e5e7eb' : '#059669',
          color: saved ? '#15803d' : (saving || !selectedVersion) ? '#9ca3af' : '#fff',
          border: saved ? '1.5px solid #86efac' : 'none',
          borderRadius: 10, fontSize: 15, fontWeight: 600,
          cursor: (saving || saved || !selectedVersion) ? 'not-allowed' : 'pointer',
          transition: 'background 0.15s',
        }}
      >
        {saved ? '✅ 라이브러리에 저장됨!' : saving ? '저장 중...' : !selectedVersion ? '썸네일 스타일을 선택하세요' : '💾 라이브러리에 저장'}
      </button>

      {/* 스핀 애니메이션 */}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
