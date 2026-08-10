# Live Obsidian Smoke Test

Bu kontrol listesi, birim ve MCP protokol testleri geçen sürümün gerçek Obsidian Local REST API ile doğrulanması içindir.

## Güvenlik sınırı

- Test için yeni ve boş bir Obsidian vault oluşturun.
- Günlük kullandığınız vault üzerinde ilk smoke testi çalıştırmayın.
- API anahtarını `.env`, shell environment veya MCP istemci yapılandırmasında tutun; repoya commit etmeyin.
- `PROJECT_MEMORY_ROOT` boş bırakıldığında vault kökü proje hafızası olarak kullanılır.
- Smoke test sırasında `obsidian_put_content` ve `obsidian_delete_file` araçlarını doğrudan çağırmayın.

## Ön koşullar

1. Python 3.11 veya üzeri kurulu.
2. `uv` kurulu.
3. Repo ana bilgisayara klonlanmış.
4. Obsidian kurulu ve test vault'u açık.
5. Obsidian Local REST API community plugin `4.1.7` kurulu ve etkin.
6. Plugin API anahtarı alınmış.
7. HTTPS için varsayılan port `27124`; HTTP kullanılıyorsa plugin portuyla birlikte protokol açıkça ayarlanmış.

## Kurulum doğrulaması

Repo kökünde:

```powershell
uv sync --frozen --all-groups
$env:OBSIDIAN_API_KEY="<local-rest-api-key>"
$env:OBSIDIAN_HOST="127.0.0.1"
$env:OBSIDIAN_PORT="27124"
$env:OBSIDIAN_PROTOCOL="https"
$env:PROJECT_MEMORY_ROOT=""
uv run --frozen pytest -q
```

Beklenen sonuç: tüm testler geçer.

## Senaryo 1 — Vault initialization

`project_init` çağrısı:

```json
{
  "project_name": "mcp-project-memory-smoke-test",
  "description": "Live Obsidian integration smoke test"
}
```

Beklenen ilk sonuç:

- `created` içinde yedi Markdown dosyası bulunur.
- `already_exists` boştur.
- Obsidian içinde `PROJECT.md`, `STATE.md`, `ROADMAP.md`, `DECISIONS.md`, `TODO.md`, `HANDOFF.md` ve `PROGRESS.md` görünür.

Aynı çağrıyı ikinci kez çalıştırın.

Beklenen ikinci sonuç:

- `created` boştur.
- Yedi dosya `already_exists` içinde görünür.
- İlk dosyaların içerikleri değişmemiştir.

## Senaryo 2 — Context recovery

`project_get_context` çağrısı:

```json
{}
```

Beklenen sonuç:

- Belgeler `project`, `state`, `handoff`, `roadmap`, `todo`, `decisions`, `progress` sırasında gelir.
- Her belgenin gerçek vault yolu raporlanır.
- Hepsinin durumu `loaded` olur.
- `omitted` boştur.
- `truncated` alanları `false` olur.

## Senaryo 3 — Safe create ve path sınırı

İlk çağrı:

```json
{
  "relative_path": "research/SMOKE.md",
  "content": "# Smoke Test\n\nOriginal content.\n"
}
```

Beklenen sonuç: `status` değeri `created`.

Aynı yolu farklı içerikle tekrar çağırın:

```json
{
  "relative_path": "research/SMOKE.md",
  "content": "This must not overwrite the original."
}
```

Beklenen sonuç:

- `status` değeri `already_exists`.
- Obsidian'daki dosyada hâlâ `Original content.` yazılıdır.

Aşağıdaki yolların her birini ayrı çağrıda deneyin ve reddedildiğini doğrulayın:

- `../outside.md`
- `/absolute.md`
- `notes\\windows-path.md`
- `%2e%2e/encoded.md`
- `not-markdown.txt`

## Senaryo 4 — Checkpoint ve Obsidian progress görünümü

`project_checkpoint` çağrısı:

```json
{
  "agent_id": "smoke-test-agent",
  "session_id": "live-smoke-1",
  "summary": "Live Obsidian continuity flow verified.",
  "completed": [
    "Initialized the project vault.",
    "Loaded project context.",
    "Verified safe file creation."
  ],
  "files_changed": ["research/SMOKE.md"],
  "verification": ["All smoke-test scenarios passed so far."],
  "decisions": ["Use one dedicated vault per project."],
  "pending_approvals": ["Approve installation against the real project vault."],
  "blockers": [],
  "next_steps": ["Restart the MCP server and verify context recovery."]
}
```

Obsidian içinde doğrulayın:

- `sessions/live-smoke-1.md` append-only session kaydı vardır.
- `STATE.md` güncel özeti ve sıradaki adımı içerir.
- `HANDOFF.md` agent, session ve sıradaki adımı içerir.
- `PROGRESS.md` yeni checkpoint başlığını ve session bağlantısını içerir.
- `DECISIONS.md`, `Use one dedicated vault per project.` kararını içerir.
- `DECISIONS.md`, onay bekleyen `Approve installation...` maddesini içermez.
- Onay bekleyen madde `HANDOFF.md` ve session kaydında görünür.

Aynı `session_id` ile checkpoint'i tekrar çağırın.

Beklenen sonuç:

- Açık bir checkpoint conflict hatası alınır.
- `STATE.md`, `HANDOFF.md`, `PROGRESS.md` ve `DECISIONS.md` ikinci kez değiştirilmez.

## Senaryo 5 — Süreç yeniden başlatma

1. MCP sunucusunu kapatın.
2. Obsidian'ı açık bırakın.
3. MCP sunucusunu aynı environment değerleriyle yeniden başlatın.
4. `project_get_context` çağrısını tekrar çalıştırın.

Beklenen sonuç:

- Önceki konuşmaya ihtiyaç duymadan güncel state, handoff, decision ve progress içerikleri geri gelir.
- `STATE.md` içindeki sıradaki adım yeni agent tarafından görülebilir.
- Session bağlantıları gerçek Obsidian notlarını açar.

Bu senaryo tek bilgisayarda minimum proje devamlılığı hedefinin kabul testidir.

## Sonuç kaydı

Smoke test sonunda aşağıdaki bilgileri repo `progress.md` dosyasına ve gerçek proje vault'undaki `PROGRESS.md` dosyasına kaydedin:

- Tarih ve bilgisayar
- Obsidian sürümü
- Local REST API plugin sürümü
- Kullanılan protokol ve port
- Geçen/kalan senaryolar
- Gözlenen hata mesajları
- Gerçek proje vault'una geçiş kararı

## Doğrulanmış V1 referans sonucu — 2026-08-10

- Test bilgisayarı, ayrı ve boş test vault'u
- Obsidian `1.13.4`
- Local REST API `4.1.7`
- HTTPS `127.0.0.1:27124`
- 15 `obsidian_*` aracın tamamı canlı testten geçti
- 4 `project_*` aracın tamamı canlı testten geçti
- Init idempotency, beş unsafe path reddi, safe-create overwrite koruması,
  checkpoint, decision/pending-approval ayrımı ve süreç yeniden başlatma sonrası
  context recovery geçti
- Canlı testin ilk turunda açık `session_id` dosya yoluna timestamp eklenmesi
  nedeniyle duplicate checkpoint'in reddedilmediği bulundu; açık kimlikler için
  `sessions/<session_id>.md` kullanılarak düzeltildi ve tekrar test edildi
- Eski DQL tabanlı recent-changes isteğinin Local REST API 4.x'te çalışmadığı
  bulundu; `stat.mtime` JsonLogic sorgusu ve yerel sıralama ile düzeltildi
- Var olmayan `/periodic/:period/recent` endpoint kullanımı bulundu; desteklenen
  tarihli periodic endpoint'leriyle sınırlı geriye tarama uygulanarak düzeltildi
