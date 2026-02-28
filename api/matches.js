export default async function handler(req, res) {
  const API_KEY = "sadudtmdHgrsrOu2Wnx89hDWP20YobKyifAR7wl5";

  try {
    const response = await fetch(
      `https://api.sportdb.dev/v1/football/live?apikey=${API_KEY}`
    );
    const data = await response.json();

    const analyzed = data.matches.map(match => {
      const homeStrength = Math.random() * 0.6 + 0.2;
      const awayStrength = Math.random() * 0.6 + 0.2;

      const total = homeStrength + awayStrength;
      const homeProb = (homeStrength / total) * 100;
      const awayProb = (awayStrength / total) * 100;
      const drawProb = 100 - homeProb - awayProb;

      let risk = "Orta";
      if (homeProb > 65 || awayProb > 65) risk = "Düşük";
      if (homeProb < 40 && awayProb < 40) risk = "Yüksek";

      return {
        home: match.homeTeam.name,
        away: match.awayTeam.name,
        score: `${match.score.fullTime.home}-${match.score.fullTime.away}`,
        minute: match.minute || "Başlamadı",
        homeProb: homeProb.toFixed(1),
        drawProb: drawProb.toFixed(1),
        awayProb: awayProb.toFixed(1),
        risk
      };
    });

    res.status(200).json(analyzed);
  } catch (err) {
    res.status(500).json({ error: "Veri alınamadı" });
  }
}
