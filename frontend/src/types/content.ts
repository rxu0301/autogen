// ---------------------------------------------------------------------------
// Step 1: 뉴스 검색
// ---------------------------------------------------------------------------

export interface NewsSearchRequest {
  topic: string;
}

export type CredibilityGrade = 'high' | 'medium' | 'low' | 'unverified';

export interface CredibilityInfo {
  score: number;           // 0~100
  grade: CredibilityGrade;
  grade_label: string;     // 예: "✅ 높음"
  source_score: number;    // 0~40
  source_reason: string;
  cross_score: number;     // 0~30
  cross_reason: string;
  content_score: number;   // 0~30
  content_reason: string;
  is_filtered: boolean;
}

export interface NewsItem {
  id: string;
  title: string;
  summary: string;
  source: string;
  published_at: string;
  url?: string;
  hashtags: string[];
  credibility?: CredibilityInfo;
}

export interface NewsSearchResponse {
  topic: string;
  news: NewsItem[];
  filtered_count: number;
}

// ---------------------------------------------------------------------------
// Step 2-A: 뉴스 요약본
// ---------------------------------------------------------------------------

export interface SummaryGenerateRequest {
  news_id: string;
  news_title: string;
  news_content: string;
  language: 'ko' | 'en';
}

export interface SummaryVersion {
  version: number;
  style: string;   // 심층분석형 / 핵심요약형 / 스토리텔링형
  summary: string;
  char_count: number;
}

export interface SummaryGenerateResponse {
  news_id: string;
  versions: SummaryVersion[];
}

// ---------------------------------------------------------------------------
// Step 2-B: 뉴스 스크립트
// ---------------------------------------------------------------------------

export interface ScriptGenerateRequest {
  news_id: string;
  news_title: string;
  news_content: string;
  duration: '20초' | '30초' | '1분';
  language: 'ko' | 'en';
}

export interface ScriptVersion {
  version: number;
  style: string;
  script: string;
  word_count: number;
}

export interface ScriptGenerateResponse {
  news_id: string;
  duration: string;
  versions: ScriptVersion[];
}

// ---------------------------------------------------------------------------
// Step 3: 썸네일 프롬프트 생성
// ---------------------------------------------------------------------------

export interface ThumbnailPromptRequest {
  news_id: string;
  news_title: string;
  selected_script: string;
  hashtags?: string[];
}

export interface ThumbnailPrompt {
  version: number;
  style: string;
  prompt_en: string;
  prompt_ko: string;
  image_url?: string;
}

export interface ThumbnailPromptResponse {
  news_id: string;
  prompts: ThumbnailPrompt[];
}

// ---------------------------------------------------------------------------
// Step 4: 결과 저장
// ---------------------------------------------------------------------------

export interface SaveResultRequest {
  topic: string;
  news: NewsItem;
  selected_script: ScriptVersion;
  duration: string;
  thumbnail_prompts: ThumbnailPrompt[];
  hashtags: string[];
}

export interface SaveResultResponse {
  id: string;
  message: string;
}

// ---------------------------------------------------------------------------
// Step 5: 라이브러리
// ---------------------------------------------------------------------------

export interface SavedResult {
  id: string;
  topic: string;
  news_title: string;
  news_source: string;
  published_at: string;
  duration: string;
  selected_script: ScriptVersion;
  thumbnail_prompts: ThumbnailPrompt[];
  hashtags: string[];
  created_at: string;
}

export interface LibraryResponse {
  results: SavedResult[];
  total: number;
  hashtag_filter?: string;
}

// ---------------------------------------------------------------------------
// 공통
// ---------------------------------------------------------------------------

export interface ApiError {
  message: string;
  status?: number;
  detail?: string;
}
