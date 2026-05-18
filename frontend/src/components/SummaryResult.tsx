import React, { useState } from 'react';
import { SummaryVersion } from '../types/content';

interface Props {
  versions: SummaryVersion[];
  onSelect: (v: SummaryVersion) => void;
  selectedVersion?: number;
}

const STYLE_META: Record<string, {
  bg: string; color: string; border: string; icon: string;
  headerBg: string; desc: string;
}> = {
  '심층분석형': {
    bg: '#dbeafe', color: '#1d4ed8', border: '#93c5fd', icon: '🔬',
    headerBg: '#eff6ff',
    desc: '배경·원인·영향·전망까지 상세 분석',
  },
  '핵심요약형': {
    bg: '#dcfce7', color: '#15803d', border: '#86efac', icon: '📌',
    headerBg: '#f0fdf4',
    desc: '5W1H 중심으로 핵심만 간결하게 정리',
  },
  '스토리텔링형': {
    bg: '#fce7f3', color: '#be185d', border: '#f9a8d4', icon: '📖',
    headerBg: '#fdf2f8',
    desc: '사건의 흐름을 이야기처럼 풀어서 설명',
  },
};

export default function SummaryResult({ versions, onSelect, selectedVersion }: Props) {
  const [copied, setCopied] = useState<number | null>(null);

  const handleCopy = async (text: string, ver: number) => {
    try { await navigator.clipboard.writeText(text); }
    catch {
      const el = document.createElement('textarea');
      el.value = text;
      document.body.appendChild(el);
      el.select();
      document.execCommand('copy');
      document.body.removeChild(el);
    }
    setCopied(ver);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <div>
      <p style={{ margin: '0 0 14px', fontSize: 13, color: '#6b7280' }}>
        3가지 스타일의 요약본입니다. 읽고 마음에 드는 버전을 선택하세요.
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {versions.map((v) => {
          const meta = STYLE_META[v.style] || {
            bg: '#f3f4f6', color: '#374151', border: '#d1d5db',
            icon: '📄', headerBg: '#f9fafb', desc: '',
          };
          const isSelected = selectedVersion === v.version;

          return (
            <div
              key={v.version}
              style={{
                border: `2px solid ${isSelected ? '#6366f1' : '#e5e7eb'}`,
                borderRadius: 14,
                overflow: 'hidden',
                boxShadow: isSelected
                  ? '0 0 0 3px rgba(99,102,241,0.12)'
                  : '0 1px 3px rgba(0,0,0,0.04)',
                transition: 'all 0.15s',
              }}
            >
              {/* ── 헤더 ── */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 16px',
                background: isSelected ? '#f0f0ff' : meta.headerBg,
                borderBottom: '1px solid #e5e7eb',
              }}>
                {/* 왼쪽: 배지 + 설명 */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                  <span style={{
                    padding: '4px 12px',
                    borderRadius: 20,
                    fontSize: 13,
                    fontWeight: 700,
                    background: meta.bg,
                    color: meta.color,
                    border: `1px solid ${meta.border}`,
                    whiteSpace: 'nowrap',
                  }}>
                    {meta.icon} 버전{v.version} — {v.style}
                  </span>
                  <span style={{ fontSize: 12, color: '#9ca3af' }}>{meta.desc}</span>
                  <span style={{
                    fontSize: 11,
                    padding: '2px 8px',
                    background: '#f3f4f6',
                    color: '#6b7280',
                    borderRadius: 10,
                    border: '1px solid #e5e7eb',
                  }}>
                    {v.char_count}자
                  </span>
                </div>

                {/* 오른쪽: 버튼 */}
                <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
                  <button
                    onClick={() => handleCopy(v.summary, v.version)}
                    style={{
                      padding: '5px 12px',
                      border: '1px solid #d1d5db',
                      borderRadius: 7,
                      background: copied === v.version ? '#dcfce7' : '#fff',
                      color: copied === v.version ? '#15803d' : '#374151',
                      fontSize: 12,
                      cursor: 'pointer',
                      whiteSpace: 'nowrap',
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
                      fontWeight: 700,
                      cursor: 'pointer',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {isSelected ? '✓ 선택됨' : '선택'}
                  </button>
                </div>
              </div>

              {/* ── 본문 (항상 펼침) ── */}
              <div style={{
                padding: '18px 20px',
                background: '#fff',
                fontSize: 14,
                lineHeight: 2.0,
                color: '#1f2937',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}>
                {v.summary}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
