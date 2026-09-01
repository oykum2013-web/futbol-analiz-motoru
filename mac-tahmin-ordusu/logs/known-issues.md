# Bilinen Sorunlar

`error-debugger` ajanı tarafından tespit edilen **sistemik** (tekrarlayan, tek maça özgü olmayan) veri sorunları burada kayıt altına alınır. Tek maçlık/geçici eksiklikler sadece o günün raporunda not düşülür, buraya girmez.

## Kayıt formatı

```
### YYYY-MM-DD — <sorun başlığı>
- Etkilenen kaynak/ajan: ...
- Belirti: ...
- Etki: ...
- Durum: [açık / çözüldü (YYYY-MM-DD)]
```

---

### 2026-08-19 — Colorado Rapids Batı Konferansı sıralaması kaynaklar arası çelişkili
- Etkilenen kaynak/ajan: lafc.com (8. sıra) vs sportsgambler.com (15. sıra) — aynı puan/averaj (25 puan, 8G-10M-1B) bildiriliyor ama sıralama farklı.
- Belirti: Bir önizleme kaynağı takımı üst sıralarda, diğeri alt sıralarda gösteriyor.
- Etki: Colorado Rapids – LAFC analizinde (reports/2026-08-19-mac-analizleri.md) sıralama iddia edilmedi, sadece puan/averaj kullanıldı.
- Durum: açık — bir sonraki koşuda resmi MLS puan durumu (mlssoccer.com) ile doğrulanmalı.

### 2026-08-19 — St. Louis City SC sakatlık bilgisi tek kaynaklı
- Etkilenen kaynak/ajan: sportsgambler.com (Celio Pompeu, Tyson Pearce sakat).
- Belirti: İkinci bağımsız kaynak bulunamadı.
- Etki: reports/2026-08-19-mac-analizleri.md'de "⚠️ tek kaynaklı, doğrulanamadı" notuyla verildi, kesin bilgi gibi sunulmadı.
- Durum: açık — sonraki koşuda ikinci kaynakla teyit edilmeli.

### 2026-08-19/2026-08-22 — fixture-scanner bazı gece maçlarını kaçırıyordu
- Etkilenen kaynak/ajan: fixture-scanner.
- Belirti: Kısıtlı/aklıselim bir lig listesine güvenme ve kaynakların kendi "maç günü" tarih etiketine göre gruplama yapması yüzünden, gece geç saatte oynanan bazı maçlar (Güney Amerika/Asya/gece yarısını geçen Avrupa maçları) o günün raporuna hiç girmedi.
- Etki: Bir gecenin fikstür listesi eksik çıktı, bazı maçlar hiç analiz edilmedi.
- Durum: **çözüldü (2026-08-22)** — CLAUDE.md kesin emir 9 ve agents/fixture-scanner.md güncellendi: sabit lig listesi yasaklandı, maçlar kaynağın tarih etiketine göre değil gerçek başlama saatine göre günün kapsamına dahil ediliyor, tarama sonunda logs/daily-runs/'a "bulunan toplam maç + lig dağılımı" ara logu yazılıyor (bkz. Fixture Tarama Özeti).
