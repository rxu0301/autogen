export interface ContentRequest {
  interest: string;
  goal: string;
  target_audience: string;
  platform: string;
  tone: string;
  duration: string;
  keywords?: string;
  use_llm?: boolean;
}

export interface ContentResponse {
  content: string;
  source: 'llm' | 'fallback';
  model?: string;
}

export interface SimilarContentRequest {
  query: string;
  top_k?: number;
}

export interface SimilarContentItem {
  id: string;
  content: string;
  score: number;
  metadata?: Record<string, unknown>;
}

export interface SimilarContentResponse {
  results: SimilarContentItem[];
  total: number;
}

export interface ApiError {
  message: string;
  status?: number;
  detail?: string;
}
