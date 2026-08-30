# futbol-analiz-motoru

Futbol maçları için çoklu ajan (multi-agent) mimarisiyle veri toplayan,
analiz eden ve olasılık tabanlı tahmin üreten bir sistem.

## Proje yapısı

- `ajan_ordusu/` — Python çoklu ajan tahmin motoru (prototip)
  - `agents/data_collection.py` — football-data.org / OpenLigaDB çıktısını normalize eder
  - `agents/form_analysis.py` — son N maç performansı
  - `agents/h2h_analysis.py` — iki takım arası geçmiş karşılaşmalar
  - `agents/squad_analysis.py` — sakatlık/kadro etkisi (API-Football)
  - `agents/market_analysis.py` — bahis oranlarından zımni olasılık (The Odds API)
  - `agents/prediction.py` — form + H2H + kadro + piyasayı birleştirip tahmin üretir
  - `agents/orchestrator.py` — ajanları sırayla çalıştırıp tek maç için Markdown rapor üretir
  - `agents/bulletin.py` — çoklu maç sonucunu günlük/haftalık bültene dönüştürür
  - `api.py` — n8n gibi araçların çağırabilmesi için FastAPI HTTP sarmalayıcı
  - `clients/` — dış API istemcileri (football_data, openligadb, api_football, the_odds_api)
  - `schemas.py`, `config.py` — veri modelleri ve ayarlar
- `n8n/` — n8n workflow tanımları (`api.py`'yi günlük tetikler)
- `index.html` + `api/matches.js` — ajan ordusundan bağımsız, ayrı bir basit JS/Vercel canlı skor arayüzü
- `tests/` — pytest testleri (`test_agents.py`, `test_api.py`, `test_resilience.py`)

## Çalıştırma / doğrulama komutları

```bash
pip install -r requirements.txt

python -m ajan_ordusu.main --demo              # ağ/anahtar gerektirmeyen demo
python -m ajan_ordusu.main --bulletin-demo     # çok maçlı bülten demosu
pytest                                          # tüm testler
uvicorn ajan_ordusu.api:app --host 0.0.0.0 --port 8000   # HTTP API
```

## Veri bütünlüğü kuralı (kesin, ihlal edilemez)

Hiçbir ajan sahte, rastgele veya uydurma istatistik/veri üretmez. Tüm veriler
gerçek kaynaklardan gelir (OpenLigaDB, football-data.org, API-Football, The
Odds API). Gerçek veri bulunamazsa ajan bunu sessizce nötr bir değerle
doldurmaz, **açıkça "veri yok" / "yetersiz veri"** olarak raporlar. `--demo`
modu tamamen kurgusal veri kullanır ve bunu hem kodda hem çalışma zamanı
çıktısında açıkça belirtir; asla gerçek analiz gibi sunulmaz. Bu kural
eklenecek her yeni ajan için de geçerlidir.

## Bilinen durum

`api/matches.js` içinde önceden sabit kodlanmış bir API anahtarı vardı; artık
`SPORTDB_API_KEY` ortam değişkeninden okunuyor. Eski anahtar git geçmişinde
hâlâ görünür — sağlayıcı tarafında iptal/rotate edilmesi gerekiyor (kod
değişikliğiyle çözülmez).

---

## Görev Prompt Şablonu (Meta Prompt)

Bu projede benden (Claude Code) bir değişiklik isteyeceğin zaman, isteğini
doğrudan yazmak yerine önce aşağıdaki meta prompt'u kullanarak daha net bir
görev tanımına dönüştürebilirsin. Meta prompt'u bana veya başka bir Claude
sohbetine verip `{GÖREV}` yerine kabaca ne istediğini yaz; çıktı olarak bana
doğrudan verilebilecek, bu projeye özel bir görev promptu üretilir.

```
Sen deneyimli bir prompt mühendisisin ve özellikle agentic coding
assistant'lara (Claude Code gibi kod tabanı üzerinde doğrudan aksiyon alan
AI ajanlarına) verilen görev tanımlarını optimize etmede uzmansın.

Aşağıda futbol-analiz-motoru adlı bir Python projesinin bağlamı var. Kullanıcı
sana kabaca ne yapmak istediğini anlatacak. Görevin bunu alıp, ajana
verilmeye hazır, net ve eksiksiz bir görev promptu üretmek.

PROJE BAĞLAMI:
- Çoklu ajan (multi-agent) mimarisiyle çalışan futbol maç analiz/tahmin
  sistemi. Ajanlar ajan_ordusu/agents/ altında: data_collection,
  form_analysis, h2h_analysis, squad_analysis, market_analysis, prediction,
  orchestrator, bulletin. HTTP sarmalayıcı ajan_ordusu/api.py (FastAPI).
- KESİN KURAL: Hiçbir ajan sahte/uydurma veri üretemez. Veri yoksa
  "veri yok / yetersiz veri" olarak açıkça raporlanır. --demo modu hariç
  (o da kurgusal olduğunu açıkça belirtir). Bu kural her yeni koda da uygulanır.
- Test: pytest (tests/ klasörü). Demo çalıştırma: python -m ajan_ordusu.main --demo

Üreteceğin prompt şu bölümleri (gerekenleri) içermeli:

1. BAĞLAM: Değişikliğin ilgili olduğu dosya/ajan/modül.
2. HEDEF: Tam olarak ne değişmeli/eklenmeli/düzelmeli — tek cümlede net
   sonuç tanımı.
3. KAPSAM SINIRI: Ajanın dokunmaması gereken yerler, yapmaması gereken ek
   işler (aşırı refactor, gereksiz soyutlama, ilgisiz dosya değişiklikleri).
4. KABUL KRİTERLERİ: İşin "bitti" sayılması için sağlanması gereken somut,
   test edilebilir koşullar. Veri bütünlüğü kuralına aykırı bir davranış
   (sahte veri, sessiz varsayılan değer) asla kabul kriteri olarak
   GEÇMEMELİ — tam tersi, ihlal etmemesi bir kabul kriteri olmalı.
5. DOĞRULAMA ADIMI: pytest çalıştırılmalı mı, --demo ile mi test edilmeli,
   yoksa gerçek bir API anahtarıyla mı denenmeli.
6. STİL/KONVANSİYON NOTLARI: Türkçe değişken/mesaj kullanımı, mevcut
   ajan yapısına (girdi/çıktı şeması) uyum.
7. BELİRSİZLİK DURUMUNDA: Ajan emin olamadığında varsayım yapıp devam mı
   etsin, yoksa durup sorsun mu?

Kurallar:
- Kullanıcının anlattığından çıkarım yapabildiğin yerlerde mantıklı
  varsayımlarda bulun, ama kritik belirsizlikleri ayrıca madde madde
  listele ve kullanıcıya sor.
- Gereksiz uzunluktan kaçın; her madde somut ve aksiyona dönük olsun.
- Çıktı, doğrudan ajana yapıştırılabilecek şekilde yazılmış olmalı (meta
  açıklama değil, doğrudan görev talimatı).

Kullanıcının görevi: {GÖREV}
```
