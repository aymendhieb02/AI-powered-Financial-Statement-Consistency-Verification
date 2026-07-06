import axios, { type AxiosError } from 'axios';
import type { ApiError } from '../types/api';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api',
});

export function getApiErrorMessage(error: unknown, fallback = 'Request failed') {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as ApiError | undefined;
    return data?.detail || data?.message || error.message || fallback;
  }
  if (error instanceof Error) return error.message;
  return fallback;
}

export function isNotFound(error: unknown) {
  return axios.isAxiosError(error) && error.response?.status === 404;
}
