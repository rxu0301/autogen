import React, { useState } from 'react';
import NewsSearch from './components/NewsSearch';
import NewsList from './components/NewsList';
import LanguageSelector from './components/LanguageSelector';
import SummaryGenerator from './components/SummaryGenerator';
import SummaryResult from './components/SummaryResult';
import ScriptGenerator from './components/ScriptGenerator';
import ScriptResult from './components/ScriptResult';
import ThumbnailResult from './components/ThumbnailResult';
import Library from './components/Library';
import {
  searchNews,
  generateSummary,
  generateScript,
  generateThumbnail,
  saveResult,
} from './api/content';
import {
  NewsItem,
  SummaryVersion,
  ScriptVersion,
  ThumbnailPrompt,
} from './types/content';

type Tab = 'create' | 'library';

// 단계 인덱스 (진행 표시용)
const STEPS = [
  '주제 입력',
  '뉴스 선택',
  '언어 선택',
  '요약본',
  '스크립트',
  '썸네일',
];

function Card({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{
      background: '#fff', borderRadius: 14, padding: '20px 22px',
      boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
      border: '1px solid rgba(99,102,241,0.1)', marginBottom: 16,
    }}>
      <div style={{ fontSize: 14, fontWeight: 700, color: '#374151', marginBottom: 14 }}>
        {label}
      </div>
      {children}
    </div>
  );
}

export default function App() {
  const [tab, setTab] = useState<Tab>('create');

  const [topic, setTopic] = useState('');
  const [newsList, setNewsList] = useState<NewsItem[]>([]);
  const [filteredCount, setFilteredCount] = useState(0);
  const [selectedNews, setSelectedNews] = useState<NewsItem | null>(null);
  const [language, setLanguage] = useState<'ko' | 'en'>('ko');
  const [duration, setDuration] = useState<'20초' | '30초' | '1분'>('30초');

  const [summaryVersions, setSummaryVersions] = useState<SummaryVersion[]>([]);
  const [selectedSummary, setSelectedSummary] = useState<SummaryVersion | null>(null);

  const [scriptVersions, setScriptVersions] = useState<ScriptVersion[]>([]);
  const [selectedScript, setSelectedScript] = useState<ScriptVersion | null>(null);

  const [thumbnailPrompts, setThumbnailPrompts] = useState<ThumbnailPrompt[]>([]);

  const [searchLoading, setSearchLoading] = useState(false);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [scriptLoading, setScriptLoading] = useState(false);
  const [thumbnailLoading, setThumbnailLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const [error, setError] = useState('');

  // 현재 진행 단계 계산
  const currentStep = (() => {
    if (thumbnailPrompts.length > 0) return 5;
    if (scriptVersions.length > 0) return 4;
    if (summaryVersions.length > 0) return 3;
    if (selectedNews) return 2;
    if (newsList.length > 0) return 1;
    return 0;
  })();

  // ---------------------------------------------------------------------------

  const handleSearch = async (t: string) => {
    setTopic(t);
    setError('');
    setSearchLoading(true);
    setNewsList([]);
    setFilteredCount(0);
    setSelectedNews(null);
    setSummaryVersions([]);
    setSelectedSummary(null);
    setScriptVersions([]);
    setSelectedScript(null);
    setThumbnailPrompts([]);
    setSaved(false);
    try {
      const res = await searchNews({ topic: t });
      setNewsList(res.news);
      setFilteredCount(res.filtered_count ?? 0);
    } catch (e: unknown) {
      setError((e as { message?: string }).message || '뉴스 검색 중 오류가 발생했습니다.');
    } finally {
      setSearchLoading(false);
    }
  };

  const handleSelectNews = (item: NewsItem) => {
    setSelectedNews(item);
    setSummaryVersions([]);
    setSelectedSummary(null);
    setScriptVersions([]);
    setSelectedScript(null);
    setThumbnailPrompts([]);
    setSaved(false);
  };

  const handleGenerateSummary = async () => {
    if (!selectedNews) return;
    setError('');
    setSummaryLoading(true);
    setSummaryVersions([]);
    setSelectedSummary(null);
    try {
      const res = await generateSummary({
        news_id: selectedNews.id,
        news_title: selectedNews.title,
        news_content: selectedNews.summary,
        language,
      });
      setSummaryVersions(res.versions);
    } catch (e: unknown) {
      setError((e as { message?: string }).message || '요약본 생성 중 오류가 발생했습니다.');
    } finally {
      setSummaryLoading(false);
    }
  };

  const handleGenerateScript = async () => {
    if (!selectedNews) return;
    setError('');
    setScriptLoading(true);
    setScriptVersions([]);
    setSelectedScript(null);
    setThumbnailPrompts([]);
    setSaved(false);
    try {
      const res = await generateScript({
        news_id: selectedNews.id,
        news_title: selectedNews.title,
        news_content: selectedNews.summary,
        duration,
        language,
      });
      setScriptVersions(res.versions);
    } catch (e: unknown) {
      setError((e as { message?: string }).message || '스크립트 생성 중 오류가 발생했습니다.');
    } finally {
      setScriptLoading(false);
    }
  };

  const handleGenerateThumbnail = async () => {
    if (!selectedNews || !selectedScript) return;
    setError('');
    setThumbnailLoading(true);
    setThumbnailPrompts([]);
    setSaved(false);
    try {
      const res = await generateThumbnail({
        news_id: selectedNews.id,
        news_title: selectedNews.title,
        selected_script: selectedScript.script,
        hashtags: selectedNews.hashtags,
      });
      setThumbnailPrompts(res.prompts);
    } catch (e: unknown) {
      setError((e as { message?: string }).message || '썸네일 프롬프트 생성 중 오류가 발생했습니다.');
    } finally {
      setThumbnailLoading(false);
    }
  };

  const handleSave = async () => {
    if (!selectedNews || !selectedScript || thumbnailPrompts.length === 0) return;
    setSaving(true);
    setError('');
    try {
      await saveResult({
        topic,
        news: selectedNews,
        selected_script: selectedScript,
        duration,
        thumbnail_prompts: thumbnailPrompts,
        hashtags: selectedNews.hashtags,
      });
      setSaved(true);
    } catch (e: unknown) {
      setError((e as { message?: string }).message || '저장 중 오류가 발생했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setTopic(''); setNewsList([]); setSelectedNews(null);
    setSummaryVersions([]); setSelectedSummary(null);
    setScriptVersions([]); setSelectedScript(null);
    setThumbnailPrompts([]); setSaved(false); setError('');
  };

  // ---------------------------------------------------------------------------

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #f0f4ff 0%, #faf5ff 100%)',
      padding: '32px 16px 80px',
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
    }}>
      <div style={{ maxWidth: 780, margin: '0 auto' }}>

        {/* 헤더 */}
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <h1 style={{ fontSize: 26, fontWeight: 800, color: '#1e1b4b', margin: '0 0 6px', letterSpacing: '-0.02em' }}>
            📰 뉴스 숏폼 에이전트
          </h1>
          <p style={{ fontSize: 14, color: '#6b7280', margin: 0 }}>
            주제 입력 → 뉴스 선택 → 요약본 생성 → 스크립트 생성 → 썸네일 프롬프트
          </p>
        </div>

        {/* 탭 */}
        <div style={{ display: 'flex', marginBottom: 20, border: '1px solid #e5e7eb', borderRadius: 12, overflow: 'hidden', background: '#fff' }}>
          {(['create', 'library'] as Tab[]).map((t) => (
            <button key={t} onClick={() => setTab(t)} style={{
              flex: 1, padding: '12px', border: 'none',
              background: tab === t ? '#6366f1' : '#fff',
              color: tab === t ? '#fff' : '#374151',
              fontSize: 14, fontWeight: 600, cursor: 'pointer',
            }}>
              {t === 'create' ? '✍️ 콘텐츠 생성' : '📚 라이브러리'}
            </button>
          ))}
        </div>

        {tab === 'create' && (
          <div>
            {/* 진행 단계 표시 */}
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: 20, overflowX: 'auto', paddingBottom: 4 }}>
              {STEPS.map((label, i) => (
                <React.Fragment key={i}>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, minWidth: 52 }}>
                    <div style={{
                      width: 26, height: 26, borderRadius: '50%',
                      background: i <= currentStep ? '#6366f1' : '#e5e7eb',
                      color: i <= currentStep ? '#fff' : '#9ca3af',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 11, fontWeight: 700,
                      border: i === currentStep ? '2px solid #4338ca' : 'none',
                    }}>
                      {i < currentStep ? '✓' : i + 1}
                    </div>
                    <span style={{
                      fontSize: 9, whiteSpace: 'nowrap',
                      color: i <= currentStep ? '#4338ca' : '#9ca3af',
                      fontWeight: i === currentStep ? 700 : 400,
                    }}>
                      {label}
                    </span>
                  </div>
                  {i < STEPS.length - 1 && (
                    <div style={{
                      flex: 1, height: 2, margin: '0 3px', marginBottom: 16,
                      background: i < currentStep ? '#6366f1' : '#e5e7eb',
                    }} />
                  )}
                </React.Fragment>
              ))}
            </div>

            {/* 에러 */}
            {error && (
              <div style={{ marginBottom: 16, padding: '12px 16px', background: '#fef2f2', borderRadius: 10, color: '#b91c1c', fontSize: 13, border: '1px solid #fecaca' }}>
                ⚠️ {error}
              </div>
            )}

            {/* ── 1단계: 주제 입력 ── */}
            <Card label="1️⃣ 주제 입력">
              <NewsSearch onSearch={handleSearch} loading={searchLoading} />
            </Card>

            {/* ── 2단계: 뉴스 선택 ── */}
            {newsList.length > 0 && (
              <Card label={`2️⃣ 뉴스 선택 — "${topic}" 관련 최신 뉴스`}>
                <NewsList
                  news={newsList}
                  onSelect={handleSelectNews}
                  selectedId={selectedNews?.id}
                  filteredCount={filteredCount}
                />
              </Card>
            )}

            {/* ── 3단계: 언어 선택 ── */}
            {selectedNews && (
              <Card label="3️⃣ 언어 선택">
                <LanguageSelector language={language} onChange={setLanguage} />
              </Card>
            )}

            {/* ── 4단계: 요약본 생성 ── */}
            {selectedNews && (
              <Card label="4️⃣ 뉴스 요약본 생성">
                <SummaryGenerator onGenerate={handleGenerateSummary} loading={summaryLoading} />
              </Card>
            )}

            {/* ── 요약본 결과 ── */}
            {summaryVersions.length > 0 && (
              <Card label="📄 뉴스 요약본 결과">
                <SummaryResult
                  versions={summaryVersions}
                  onSelect={setSelectedSummary}
                  selectedVersion={selectedSummary?.version}
                />
              </Card>
            )}

            {/* ── 5단계: 스크립트 생성 ── */}
            {selectedNews && (
              <Card label="5️⃣ 뉴스 스크립트 생성 (낭독용)">
                <ScriptGenerator
                  selected={duration}
                  onChange={setDuration}
                  onGenerate={handleGenerateScript}
                  loading={scriptLoading}
                />
              </Card>
            )}

            {/* ── 스크립트 결과 ── */}
            {scriptVersions.length > 0 && (
              <Card label="🎙️ 뉴스 스크립트 결과">
                <ScriptResult
                  versions={scriptVersions}
                  duration={duration}
                  onSelect={setSelectedScript}
                  selectedVersion={selectedScript?.version}
                  onGenerateThumbnail={handleGenerateThumbnail}
                  thumbnailLoading={thumbnailLoading}
                />
              </Card>
            )}

            {/* ── 6단계: 썸네일 프롬프트 ── */}
            {thumbnailPrompts.length > 0 && (
              <Card label="6️⃣ 썸네일 이미지 생성 프롬프트">
                <ThumbnailResult
                  prompts={thumbnailPrompts}
                  onSave={handleSave}
                  saving={saving}
                  saved={saved}
                />
              </Card>
            )}

            {/* 다시 시작 */}
            {newsList.length > 0 && (
              <div style={{ textAlign: 'center', marginTop: 8 }}>
                <button onClick={handleReset} style={{
                  padding: '9px 20px', background: 'transparent', color: '#6b7280',
                  border: '1px solid #e5e7eb', borderRadius: 8, fontSize: 13, cursor: 'pointer',
                }}>
                  🔄 처음부터 다시 시작
                </button>
              </div>
            )}
          </div>
        )}

        {tab === 'library' && (
          <div style={{ background: '#fff', borderRadius: 14, padding: '20px 22px', boxShadow: '0 1px 4px rgba(0,0,0,0.06)', border: '1px solid rgba(99,102,241,0.1)' }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: '#374151', marginBottom: 16 }}>
              📚 저장된 결과 라이브러리
            </div>
            <Library />
          </div>
        )}

        <div style={{ marginTop: 40, textAlign: 'center', fontSize: 12, color: '#d1d5db' }}>
          뉴스 숏폼 에이전트 v2.2 · Ollama + ChromaDB
        </div>
      </div>
    </div>
  );
}
