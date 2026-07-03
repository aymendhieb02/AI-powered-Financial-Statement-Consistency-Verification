import { api } from './client';
export async function listRules() { const { data } = await api.get('/rules'); return data; }
export async function listHistory() { const { data } = await api.get('/verification/history'); return data; }
export async function getRunConfidence(runId: string) { const { data } = await api.get('/verification/' + runId + '/confidence'); return data; }
export async function getEvidence(runId: string, lineId: string) { const { data } = await api.get('/verification/' + runId + '/evidence/' + lineId); return data; }
