# scripts/

Orkestrasyonun kendisi kod ile değil, `CLAUDE.md` talimatları uyarınca Claude Code'un `Agent`/`Task` aracıyla `.claude/agents/` altındaki subagent'ları sırayla çağırmasıyla yürütülür (bkz. `../CLAUDE.md` → "Orkestrasyon akışı"). Bu klasör, o akışa yardımcı olacak küçük, isteğe bağlı yardımcı scriptler içindir (örn. tarih/dosya adı üretimi, rapor dosyalarını listeleme).

## today.sh

Bugünün tarihini rapor/log dosya adı formatında (`YYYY-MM-DD`) basar. Ajanların veya orkestratörün dosya adlandırmasında tutarlılık için kullanılabilir.

```bash
./scripts/today.sh
# 2026-08-19
```
