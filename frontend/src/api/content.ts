import axios, { AxiosError } from 'axios';
import {
  NewsSearchRequest,
  NewsSearchResponse,
  SummaryGenerateRequest,
  SummaryGenerateResponse,
  ScriptGenerateRequest,
  ScriptGenerateResponse,
  ThumbnailPromptRequest,
  ThumbnailPromptResponse,
  SaveResultRequest,
  SaveResultResponse,
  LibraryResponse,
  ApiError,
} from '../types/content';

const api = axios.create({
  baseURL: import.meta.env.VITE_BFF_URL || '/api',
});

function normalizeError(err: unknown): ApiError {
  if (err instanceof AxiosError) {
    const data = err.response?.data;
    return {
      message: data?.message || data?.detail || err.message || '요청 중 오류가 발생했습니다.',
      status: err.response?.status,
      detail: data?.detail,
    };
  }
  if (err instanceof Error) return { message: err.message };
  return { message: '알 수 없는 오류가 발생했습니다.' };
}

/** Step 1: 주제 기반 뉴스 검색 */
export const searchNews = async (req: NewsSearchRequest): Promise<NewsSearchResponse> => {
  try {
    const res = await api.post<NewsSearchResponse>('/news/search', req);
    return res.data;
  } catch (err) {
    throw normalizeError(err);
  }
};

/** Step 2-A: 뉴스 요약본 생성 */
export const generateSummary = async (
  req: SummaryGenerateRequest,
): Promise<SummaryGenerateResponse> => {
  try {
    const res = await api.post<SummaryGenerateResponse>('/news/summary', req);
    return res.data;
  } catch (err) {
    throw normalizeError(err);
  }
};

/** Step 2-B: 뉴스 요약 스크립트 생성 */
export const generateScript = async (
  req: ScriptGenerateRequest,
): Promise<ScriptGenerateResponse> => {
  try {
    const res = await api.post<ScriptGenerateResponse>('/news/script', req);
    return res.data;
  } catch (err) {
    throw normalizeError(err);
  }
};

/** Step 3: 썸네일 프롬프트 생성 */
export const generateThumbnail = async (
  req: ThumbnailPromptRequest,
): Promise<ThumbnailPromptResponse> => {
  try {
    const res = await api.post<ThumbnailPromptResponse>('/news/thumbnail', req);
    return res.data;
  } catch (err) {
    throw normalizeError(err);
  }
};

/** Step 4: 결과 저장 */
export const saveResult = async (req: SaveResultRequest): Promise<SaveResultResponse> => {
  try {
    const res = await api.post<SaveResultResponse>('/news/save', req);
    return res.data;
  } catch (err) {
    throw normalizeError(err);
  }
};

/** Step 5: 라이브러리 조회 */
export const getLibrary = async (
  hashtag?: string,
  limit?: number,
): Promise<LibraryResponse> => {
  try {
    const params: Record<string, unknown> = {};
    if (hashtag) params['hashtag'] = hashtag;
    if (limit) params['limit'] = limit;
    const res = await api.get<LibraryResponse>('/news/library', { params });
    return res.data;
  } catch (err) {
    throw normalizeError(err);
  }
};

/** 헬스 체크 */
export const checkHealth = async (): Promise<{ status: string }> => {
  try {
    const res = await api.get<{ status: string }>('/news/health');
    return res.data;
  } catch (err) {
    throw normalizeError(err);
  }
};
