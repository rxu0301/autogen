import React, { useState, useEffect } from 'react';
import { SavedResult } from '../types/content';
import { getLibrary } from '../api/content';

export default function Library() {
  const [results, setResults] = useState<SavedResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [hashtag, setHashtag] = useState('');
  const [filterInput, setFilterInput] = useState('');
  const [expanded, setExpanded] = useState<string | null>(null);
  const [error, setError] = useState('');

  const load = async (tag?: string) => {
    setLoading(true);
    setError('');
    try {
      const res = await getLibrary(tag || undefined);
      setResults(res.results);
    } catch (e: unknown) {
      const err = e as { message?: string };
      setError(err.message || '라이브러리 조회 실패');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleFilter = (e: React.FormEvent) => {
    e.preventDefault();
    const tag = filterInput.trim();
    setHashtag(tag);
    load(tag || undefined);
  };

  const clearFilter = () => {
    setFilterInput('');
    setHashtag('');
    load();
  };

  // 전체 해시태그 목록 추출
  const allTags = Array.from(
    new Set(results.flatMap((r) => r.hashtags))
  ).slice(0, 20);

  return (
    <div>
      {/* 해시태그 필터 */}
      <form onSubmit={handleFilter} style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
        <input
          type="text"
          value={filterInput}
          onChange={(e) => setFilterInput(e.target.value)}
          placeholder="#해시태그로 필터링 (예: #AI)"
          style={{
            flex: 1,
            padding: '9px 12px',
            border: '1.5px solid #d1d5db',
            borderRadius: 8,
            fontSize: 13,
            outline: 'none',
          }}
        />
        <button
          type="submit"
          style={{
            padding: '9px 16px',
            background: '#6366f1',
            color: '#fff',
            border: 'none',
            borderRadius: 8,
            fontSize: 13,
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          필터
        </button>
        {hashtag && (
          <button
            type="button"
            onClick={clearFilter}
            style={{
              padding: '9px 12px',
              background: '#f3f4f6',
              color: '#374151',
              border: '1px solid #e5e7eb',
              borderRadius: 8,
              fontSize: 13,
              cursor: 'pointer',
            }}
          >
            초기화
          </button>
        )}
      </form>

      {/* 해시태그 빠른 선택 */}
      {allTags.length > 0 && (
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 14 }}>
          {allTags.map((tag) => (
            <button
              key={tag}
              onClick={() => {
                setFilterInput(tag);
                setHashtag(tag);
                load(tag);
              }}
              style={{
                padding: '3px 10px',
                background: hashtag === tag ? '#6366f1' : '#ede9fe',
                color: hashtag === tag ? '#fff' : '#7c3aed',
                border: 'none',
                borderRadius: 20,
                fontSize: 12,
                fontWeight: 500,
                cursor: 'pointer',
              }}
            >
              {tag}
            </button>
          ))}
        </div>
      )}

      {/* 상태 표시 */}
      {loading && (
        <div style={{ textAlign: 'center', padding: '24px', color: '#6b7280', fontSize: 14 }}>
          불러오는 중...
        </div>
      )}
      {error && (
        <div style={{ padding: '12px', background: '#fef2f2', borderRadius: 8, color: '#b91c1c', fontSize: 13 }}>
          {error}
        </div>
      )}
      {!loading && !error && results.length === 0 && (
        <div style={{ textAlign: 'center', padding: '32px', color: '#9ca3af', fontSize: 14 }}>
          {hashtag ? `'${hashtag}' 태그의 저장된 결과가 없습니다.` : '저장된 결과가 없습니다.'}
        </div>
      )}

      {/* 결과 목록 */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {results.map((item) => {
          const isOpen = expanded === item.id;
          return (
            <div
              key={item.id}
              style={{
                border: '1.5px solid #e5e7eb',
                borderRadius: 12,
                overflow: 'hidden',
                background: '#fff',
              }}
            >
              {/* 요약 헤더 */}
              <div
                onClick={() => setExpanded(isOpen ? null : item.id)}
                style={{
                  padding: '14px 16px',
                  cursor: 'pointer',
                  background: isOpen ? '#f5f3ff' : '#fff',
                  borderBottom: isOpen ? '1px solid #e5e7eb' : 'none',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 15, fontWeight: 700, color: '#1e1b4b', marginBottom: 4 }}>
                      {item.news_title}
                    </div>
                    <div style={{ fontSize: 12, color: '#9ca3af' }}>
                      📰 {item.news_source} · {item.published_at} · {item.duration} · {item.selected_script.style}
                    </div>
                    <div style={{ marginTop: 6, display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                      {item.hashtags.map((tag) => (
                        <span
                          key={tag}
                          style={{
                            padding: '2px 7px',
                            background: '#ede9fe',
                            color: '#7c3aed',
                            borderRadius: 20,
                            fontSize: 11,
                          }}
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                  <span style={{ fontSize: 18, color: '#9ca3af', marginLeft: 8 }}>
                    {isOpen ? '▲' : '▼'}
                  </span>
                </div>
              </div>

              {/* 상세 내용 */}
              {isOpen && (
                <div style={{ padding: '16px' }}>
                  {/* 스크립트 */}
                  <div style={{ marginBottom: 16 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#374151', marginBottom: 8 }}>
                      📝 요약 스크립트 ({item.selected_script.style})
                    </div>
                    <div style={{
                      padding: '12px 14px',
                      background: '#f9fafb',
                      borderRadius: 8,
                      fontSize: 13,
                      lineHeight: 1.7,
                      color: '#1f2937',
                      whiteSpace: 'pre-wrap',
                    }}>
                      {item.selected_script.script}
                    </div>
                  </div>

                  {/* 썸네일 프롬프트 */}
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#374151', marginBottom: 8 }}>
                      🖼️ 썸네일 프롬프트
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {item.thumbnail_prompts.map((p) => (
                        <div
                          key={p.version}
                          style={{
                            padding: '10px 12px',
                            background: '#1a1a2e',
                            borderRadius: 8,
                            fontSize: 12,
                            color: '#e2e8f0',
                            lineHeight: 1.6,
                            fontFamily: 'monospace',
                          }}
                        >
                          <div style={{ color: '#a78bfa', marginBottom: 4, fontWeight: 600 }}>
                            버전{p.version} — {p.style}
                          </div>
                          {p.prompt_en}
                        </div>
                      ))}
                    </div>
                  </div>

                  <div style={{ marginTop: 10, fontSize: 11, color: '#d1d5db', textAlign: 'right' }}>
                    저장일: {new Date(item.created_at).toLocaleString('ko-KR')}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
