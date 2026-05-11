import axios, { AxiosError } from 'axios';
import {
  ContentRequest,
  ContentResponse,
  SimilarContentRequest,
  SimilarContentResponse,
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
  if (err instanceof Error) {
    return { message: err.message };
  }
  return { message: '알 수 없는 오류가 발생했습니다.' };
}

export const generateContent = async (req: ContentRequest): Promise<ContentResponse> => {
  try {
    const res = await api.post<ContentResponse>('/content/generate', req);
    return res.data;
  } catch (err) {
    throw normalizeError(err);
  }
};

export const findSimilar = async (req: SimilarContentRequest): Promise<SimilarContentResponse> => {
  try {
    const res = await api.post<SimilarContentResponse>('/content/similar', {
      query: req.query,
      top_k: req.top_k ?? 5,
    });
    return res.data;
  } catch (err) {
    throw normalizeError(err);
  }
};

export const checkHealth = async (): Promise<{ status: string }> => {
  try {
    const res = await api.get<{ status: string }>('/content/health');
    return res.data;
  } catch (err) {
    throw normalizeError(err);
  }
};
