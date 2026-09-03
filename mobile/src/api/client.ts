import type { BulletinResponse } from './types';

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function getJson<T>(baseUrl: string, path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${baseUrl.replace(/\/$/, '')}${path}`);
  } catch (err) {
    throw new ApiError(
      0,
      `API adresine ulaşılamadı (${baseUrl}). Adresin doğru ve sunucunun ` +
        'çalışır durumda olduğundan emin olun.'
    );
  }

  if (!response.ok) {
    let detail = `İstek başarısız oldu (HTTP ${response.status}).`;
    try {
      const body = await response.json();
      if (typeof body?.detail === 'string') {
        detail = body.detail;
      }
    } catch {
      // gövde JSON değilse durum koduyla yetin
    }
    throw new ApiError(response.status, detail);
  }

  return response.json() as Promise<T>;
}

export function fetchBulletinDemo(baseUrl: string): Promise<BulletinResponse> {
  return getJson<BulletinResponse>(baseUrl, '/bulletin/demo');
}

export type MatchQuery = {
  homeTeamId: string;
  awayTeamId: string;
  homeName: string;
  awayName: string;
  season?: string;
  sportKey?: string;
};

export function fetchMatch(baseUrl: string, query: MatchQuery): Promise<BulletinResponse> {
  const params = new URLSearchParams({
    home_team_id: query.homeTeamId,
    away_team_id: query.awayTeamId,
    home_name: query.homeName,
    away_name: query.awayName,
  });
  if (query.season) params.set('season', query.season);
  if (query.sportKey) params.set('sport_key', query.sportKey);

  return getJson<BulletinResponse>(baseUrl, `/match?${params.toString()}`);
}
