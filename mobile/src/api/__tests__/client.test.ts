import { ApiError, fetchBulletinDemo, fetchMatch, fetchTeams } from '../client';

function mockFetchOnce(response: Partial<Response> & { ok: boolean; status: number }) {
  global.fetch = jest.fn().mockResolvedValue(response as Response);
}

describe('api client', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('fetchBulletinDemo başarılı yanıtı olduğu gibi döner', async () => {
    const body = { title: 'demo', match_count: 0, matches: [] };
    mockFetchOnce({ ok: true, status: 200, json: async () => body });

    const result = await fetchBulletinDemo('http://localhost:8000');
    expect(result).toEqual(body);
    expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/bulletin/demo');
  });

  it('sondaki / işaretini temizleyip doğru URL oluşturur', async () => {
    mockFetchOnce({ ok: true, status: 200, json: async () => ({}) });
    await fetchBulletinDemo('http://localhost:8000/');
    expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/bulletin/demo');
  });

  it('sunucunun döndürdüğü JSON detail mesajını ApiError olarak fırlatır', async () => {
    mockFetchOnce({
      ok: false,
      status: 400,
      json: async () => ({ detail: 'FOOTBALL_DATA_API_TOKEN ortam değişkeni tanımlı değil.' }),
    });

    await expect(fetchBulletinDemo('http://localhost:8000')).rejects.toMatchObject({
      status: 400,
      message: 'FOOTBALL_DATA_API_TOKEN ortam değişkeni tanımlı değil.',
    });
  });

  it('JSON olmayan hata gövdesinde HTTP koduyla genel bir mesaj üretir', async () => {
    mockFetchOnce({
      ok: false,
      status: 502,
      json: async () => {
        throw new Error('not json');
      },
    });

    await expect(fetchBulletinDemo('http://localhost:8000')).rejects.toMatchObject({
      status: 502,
      message: 'İstek başarısız oldu (HTTP 502).',
    });
  });

  it('ağ hatasında (fetch reddi) durum 0 ile anlaşılır bir mesaj üretir', async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error('network down'));

    await expect(fetchBulletinDemo('http://localhost:8000')).rejects.toBeInstanceOf(ApiError);
    await expect(fetchBulletinDemo('http://localhost:8000')).rejects.toMatchObject({ status: 0 });
  });

  it('fetchTeams competition parametresini URL-encode ederek gönderir', async () => {
    mockFetchOnce({ ok: true, status: 200, json: async () => ({ competition: 'PL', teams: [] }) });
    await fetchTeams('http://localhost:8000', 'PL');
    expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/teams?competition=PL');
  });

  it('fetchMatch zorunlu alanları ve verilen opsiyonel alanları query string olarak gönderir', async () => {
    mockFetchOnce({ ok: true, status: 200, json: async () => ({}) });
    await fetchMatch('http://localhost:8000', {
      homeTeamId: '66',
      awayTeamId: '65',
      homeName: 'Man Utd',
      awayName: 'Man City',
      season: '2025',
    });
    const calledUrl = (global.fetch as jest.Mock).mock.calls[0][0] as string;
    const params = new URL(calledUrl).searchParams;
    expect(params.get('home_team_id')).toBe('66');
    expect(params.get('away_team_id')).toBe('65');
    expect(params.get('home_name')).toBe('Man Utd');
    expect(params.get('away_name')).toBe('Man City');
    expect(params.get('season')).toBe('2025');
    expect(params.has('sport_key')).toBe(false);
  });
});
