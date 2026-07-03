import { api } from './client';
import type { Project } from '../types/api';

export async function listProjects() {
  const { data } = await api.get<Project[]>('/projects');
  return data;
}

export async function createProject(payload: { name: string; company: string; description: string }) {
  const { data } = await api.post<Project>('/projects', payload);
  return data;
}
