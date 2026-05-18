import React, { useState } from 'react';
import { ScriptVersion } from '../types/content';

interface Props {
  versions: ScriptVersion[];
  duration: string;
  onSelect: (v: ScriptVersion) => void;
  selectedVersion?: number;
  onGenerateThumbnail: () => void;
  thumbnailLoading: boolean;
}

const STYLE_COLORS: Record<string, { bg: string; color: string; border: string }> = {
  정보형: { bg: '#dbeafe', color: '#1d4ed8', border: '#93c5fd' },
  감성형: { bg: '#fce7f3', color: '#be185d', border: '#f9a8d4' },
  자극형: { bg: '#fef3c7', color: '#b45309', border: '#fcd34d' },
};

const STYLE_ICONS: Record<string, string> = {
  정보형: '📊',
  감성형: '💝',
  자극형: '🔥',
};

export default function ScriptResult({
  versions,
  duration,
  onSelect,
  selectedVersion,
  onGenerateThumbnail,
  thumbnailLoading,
}: Props) {
  const [copied, setCopied] = useState<number | null>(null);

  const handleCopy = async (script: string, ver: number) => {
    try {
      await navigator.clipboard.writeText(script);
      setCopied(ver);
      setTimeout(() => setCopied(null), 2000);
    } catch {
      const el = document.createElement('textarea');
      el.value = script;
      document.body.appendChild(el);
      el.select();
      document.execCommand('copy');
      document.body.removeChild(el);
      setCopied(ver);
      setTimeout(() => setCopied(null), 2000);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <p style={{ margin: 0, fontSize: 13, color: '#6b7280' }}>
          {duration} 분량 스크립트 3가지 버전입니다. 썸네일 프롬프트를 만들 버전을 선택하세요.
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {versions.map((v) => {
          const colors = STYLE_COLORS[v.style] || { bg: '#f3f4f6', color: '#374151', border: '#d1d5db' };
          const icon = STYLE_ICONS[v.style] || '📝';
          const isSelected = selectedVersion === v.version;

          return (
            <div
              key={v.version}
              style={{
                border: `2px solid ${isSelected ? '#6366f1' : '#e5e7eb'}`,
                borderRadius: 12,
                overflow: 'hidden',
                boxShadow: isSelected ? '0 0 0 3px rgba(99,102,241,0.12)' : 'none',
                transition: 'all 0.15s',
              }}
            >
              {/* 헤더 */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                background: isSelected ? '#f0f0ff' : '#f9fafb',
                borderBottom: '1px solid #e5e7eb',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{
                    padding: '3px 10px',
                    borderRadius: 20,
                    fontSize: 12,
                    fontWeight: 600,
                    background: colors.bg,
                    color: colors.color,
                    border: `1px solid ${colors.border}`,
                  }}>
                    {icon} 버전{v.version} — {v.style}
                  </span>
                  <span style={{ fontSize: 12, color: '#9ca3af' }}>{v.word_count}자</span>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button
                    onClick={() => handleCopy(v.script, v.version)}
                    style={{
                      padding: '5px 12px',
                      border: '1px solid #d1d5db',
                      borderRadius: 7,
                      background: copied === v.version ? '#dcfce7' : '#fff',
                      color: copied === v.version ? '#15803d' : '#374151',
                      fontSize: 12,
                      cursor: 'pointer',
                    }}
                  >
                    {copied === v.version ? '✓ 복사됨' : '📋 복사'}
                  </button>
                  <button
                    onClick={() => onSelect(v)}
                    style={{
                      padding: '5px 14px',
                      border: `1px solid ${isSelected ? '#6366f1' : '#d1d5db'}`,
                      borderRadius: 7,
                      background: isSelected ? '#6366f1' : '#fff',
                      color: isSelected ? '#fff' : '#374151',
                      fontSize: 12,
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    {isSelected ? '✓ 선택됨' : '선택'}
                  </button>
                </div>
              </div>

              {/* 스크립트 본문 */}
              <div style={{
                padding: '14px 16px',
                background: '#fff',
                fontSize: 14,
                lineHeight: 1.8,
                color: '#1f2937',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}>
                {v.script}
              </div>
            </div>
          );
        })}
      </div>

      {selectedVersion && (
        <button
          onClick={onGenerateThumbnail}
          disabled={thumbnailLoading}
          style={{
            marginTop: 16,
            width: '100%',
            padding: '13px',
            background: thumbnailLoading ? '#e5e7eb' : '#7c3aed',
            color: thumbnailLoading ? '#9ca3af' : '#fff',
            border: 'none',
            borderRadius: 10,
            fontSize: 15,
            fontWeight: 600,
            cursor: thumbnailLoading ? 'not-allowed' : 'pointer',
            transition: 'background 0.15s',
          }}
        >
          {thumbnailLoading ? '썸네일 프롬프트 생성 중...' : '🖼️ 썸네일 프롬프트 생성'}
        </button>
      )}
    </div>
  );
}
