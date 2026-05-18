import React, { useState } from 'react';
import { NewsItem, CredibilityInfo } from '../types/content';

interface Props {
  news: NewsItem[];
  onSelect: (item: NewsItem) => void;
  selectedId?: string;
  filteredCount?: number;
}

const GRADE_STYLE: Record<string, { bg: string; color: string; border: string }> = {
  high:       { bg: '#dcfce7', color: '#15803d', border: '#86efac' },
  medium:     { bg: '#fef9c3', color: '#854d0e', border: '#fde68a' },
  low:        { bg: '#fee2e2', color: '#b91c1c', border: '#fca5a5' },
  unverified: { bg: '#f3f4f6', color: '#6b7280', border: '#d1d5db' },
};

function CredibilityBadge({ info }: { info: CredibilityInfo }) {
  const [open, setOpen] = useState(false);
  const style = GRADE_STYLE[info.grade] || GRADE_STYLE.unverified;

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <button
        onClick={(e) => { e.stopPropagation(); setOpen(!open); }}
        title="신뢰도 상세 보기"
        style={{
          padding: '3px 10px',
          borderRadius: 20,
          fontSize: 12,
          fontWeight: 600,
          background: style.bg,
          color: style.color,
          border: `1px solid ${style.border}`,
          cursor: 'pointer',
          whiteSpace: 'nowrap',
        }}
      >
        {info.grade_label} {info.score}점
      </button>

      {open && (
        <div
          onClick={(e) => e.stopPropagation()}
          style={{
            position: 'absolute',
            top: '110%',
            right: 0,
            zIndex: 100,
            background: '#fff',
            border: '1px solid #e5e7eb',
            borderRadius: 10,
            padding: '12px 14px',
            width: 260,
            boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
            fontSize: 12,
            lineHeight: 1.7,
          }}
        >
          <div style={{ fontWeight: 700, marginBottom: 8, color: '#1e1b4b', fontSize: 13 }}>
            📊 신뢰도 분석 ({info.score}/100)
          </div>

          {/* 점수 바 */}
          <div style={{ marginBottom: 10 }}>
            <div style={{ height: 6, background: '#f3f4f6', borderRadius: 3, overflow: 'hidden' }}>
              <div style={{
                height: '100%',
                width: `${info.score}%`,
                background: info.score >= 75 ? '#22c55e' : info.score >= 50 ? '#f59e0b' : '#ef4444',
                borderRadius: 3,
                transition: 'width 0.4s',
              }} />
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
            <div>
              <span style={{ color: '#9ca3af' }}>출처 ({info.source_score}/40)</span>
              <div style={{ color: '#374151' }}>{info.source_reason}</div>
            </div>
            <div>
              <span style={{ color: '#9ca3af' }}>교차검증 ({info.cross_score}/30)</span>
              <div style={{ color: '#374151' }}>{info.cross_reason}</div>
            </div>
            <div>
              <span style={{ color: '#9ca3af' }}>콘텐츠 ({info.content_score}/30)</span>
              <div style={{ color: '#374151' }}>{info.content_reason}</div>
            </div>
          </div>

          <button
            onClick={() => setOpen(false)}
            style={{
              marginTop: 10,
              width: '100%',
              padding: '5px',
              border: '1px solid #e5e7eb',
              borderRadius: 6,
              background: '#f9fafb',
              color: '#6b7280',
              fontSize: 11,
              cursor: 'pointer',
            }}
          >
            닫기
          </button>
        </div>
      )}
    </div>
  );
}

export default function NewsList({ news, onSelect, selectedId, filteredCount = 0 }: Props) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <p style={{ margin: 0, fontSize: 13, color: '#6b7280' }}>
          관련 뉴스 {news.length}개 · 신뢰도 순 정렬
        </p>
        {filteredCount > 0 && (
          <span style={{
            padding: '3px 10px',
            background: '#fef2f2',
            color: '#b91c1c',
            border: '1px solid #fecaca',
            borderRadius: 20,
            fontSize: 11,
            fontWeight: 600,
          }}>
            🚨 신뢰도 미달 {filteredCount}개 제외됨
          </span>
        )}
      </div>

      {news.map((item) => {
        const selected = item.id === selectedId;
        return (
          <div
            key={item.id}
            onClick={() => onSelect(item)}
            style={{
              padding: '16px 18px',
              border: `2px solid ${selected ? '#6366f1' : '#e5e7eb'}`,
              borderRadius: 12,
              cursor: 'pointer',
              background: selected ? '#f0f0ff' : '#fff',
              transition: 'border-color 0.15s, background 0.15s',
              boxShadow: selected ? '0 0 0 3px rgba(99,102,241,0.12)' : 'none',
            }}
          >
            {/* 제목 + 선택 배지 */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8, marginBottom: 6 }}>
              <h3 style={{ margin: 0, fontSize: 15, fontWeight: 700, color: '#1e1b4b', lineHeight: 1.4, flex: 1 }}>
                {item.title}
              </h3>
              {selected && (
                <span style={{
                  flexShrink: 0,
                  padding: '2px 10px',
                  background: '#6366f1',
                  color: '#fff',
                  borderRadius: 20,
                  fontSize: 12,
                  fontWeight: 600,
                }}>
                  선택됨
                </span>
              )}
            </div>

            {/* 요약 */}
            <p style={{ margin: '0 0 10px', fontSize: 13, color: '#4b5563', lineHeight: 1.6 }}>
              {item.summary}
            </p>

            {/* 메타 정보 + 신뢰도 */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                <span style={{ fontSize: 12, color: '#9ca3af' }}>
                  📰 {item.source} · {item.published_at}
                </span>
                {item.url && (
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    style={{ fontSize: 12, color: '#6366f1', textDecoration: 'none' }}
                  >
                    원문 보기 →
                  </a>
                )}
              </div>

              {/* 신뢰도 배지 */}
              {item.credibility && (
                <CredibilityBadge info={item.credibility} />
              )}
            </div>

            {/* 해시태그 */}
            {item.hashtags.length > 0 && (
              <div style={{ marginTop: 8, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {item.hashtags.map((tag) => (
                  <span
                    key={tag}
                    style={{
                      padding: '2px 8px',
                      background: '#ede9fe',
                      color: '#7c3aed',
                      borderRadius: 20,
                      fontSize: 11,
                      fontWeight: 500,
                    }}
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
