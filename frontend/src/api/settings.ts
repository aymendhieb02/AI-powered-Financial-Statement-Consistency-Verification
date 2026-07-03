import { api } from './client';
import type { BackendSettings, Health } from '../types/api';

export async function getHealth() { const { data } = await api.get<Health>('/health'); return data; }
export async function getSettings() { const { data } = await api.get<BackendSettings>('/settings'); return data; }
