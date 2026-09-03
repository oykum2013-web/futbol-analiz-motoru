export type TeamRef = {
  id: string;
  name: string;
};

export type TeamListItem = {
  id: number;
  name: string;
  short_name: string | null;
};

export type TeamsResponse = {
  competition: string;
  teams: TeamListItem[];
};

export type FormReport = {
  team: TeamRef;
  matches_considered: number;
  wins: number;
  draws: number;
  losses: number;
  goals_for: number;
  goals_against: number;
  points: number;
  form_string: string;
  avg_goals_for: number;
  avg_goals_against: number;
};

export type MatchResultItem = {
  date: string;
  home: TeamRef;
  away: TeamRef;
  home_goals: number | null;
  away_goals: number | null;
  competition: string | null;
};

export type H2HReport = {
  home: TeamRef;
  away: TeamRef;
  matches_considered: number;
  home_wins: number;
  away_wins: number;
  draws: number;
  home_goals: number;
  away_goals: number;
  last_meetings: MatchResultItem[];
};

export type InjuryEntry = {
  player: { id: string; name: string; position: string | null };
  reason: string;
  importance: number;
};

export type SquadReport = {
  team: TeamRef;
  missing_players: InjuryEntry[];
  impact_score: number;
  impact_level: 'Yok' | 'Düşük' | 'Orta' | 'Yüksek' | 'Bilinmiyor' | string;
  notes: string[];
};

export type OddsQuote = {
  bookmaker: string;
  home_odds: number | null;
  draw_odds: number | null;
  away_odds: number | null;
};

export type MarketReport = {
  home: TeamRef;
  away: TeamRef;
  data_available: boolean;
  quotes: OddsQuote[];
  consensus_home_prob: number | null;
  consensus_draw_prob: number | null;
  consensus_away_prob: number | null;
  notes: string[];
};

export type Prediction = {
  home: TeamRef;
  away: TeamRef;
  home_win_prob: number;
  draw_prob: number;
  away_win_prob: number;
  confidence: string;
  rationale: string[];
  disclaimer: string;
};

export type BulletinMatchItem = {
  home: TeamRef;
  away: TeamRef;
  form: { home: FormReport; away: FormReport };
  h2h: H2HReport;
  squad: { home: SquadReport; away: SquadReport };
  market: MarketReport;
  prediction: Prediction;
  data_gaps: string[];
};

export type BulletinResponse = {
  title: string;
  generated_at: string;
  risk_warning: string;
  match_count: number;
  matches: BulletinMatchItem[];
  markdown: string;
  demo?: boolean;
  demo_warning?: string;
};
