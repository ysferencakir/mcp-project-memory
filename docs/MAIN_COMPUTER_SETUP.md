# Ana Bilgisayar Kurulumu — V1

Bu rehber tek bir bilgisayarda Claude Code ve Codex'in aynı Obsidian vault'unu
ortak proje hafızası olarak kullanacağı ilk üretim-benzeri kurulumu tarif eder.
İlk doğrulama gerçek proje vault'u yerine boş bir test vault'unda yapılmalıdır.

## 1. Ön koşullar

- Git
- Python 3.11 veya üzeri
- `uv`
- Obsidian
- Obsidian Local REST API community eklentisi `4.1.7`
- Kullanılacak istemci: Codex, Claude Code veya ikisi

Her proje için ayrı vault açılması V1 çalışma modelidir. Aynı anda yalnızca
çalışılan projeye ait vault açık ve hedeflenmiş olmalıdır.

PowerShell'de `uv` komutunun gerçek yolunu şu komutla bulabilirsin:

```powershell
(Get-Command uv).Source
```

Komut bulunamıyorsa önce `uv` kurulmalı veya kurulu olduğu dizin `PATH` içine
eklenmelidir. `uv` yalnız kurulum ve geliştirme sırasında gerekir; MCP
istemcileri kurulumda oluşturulan sanal ortam giriş noktasını doğrudan çalıştırır.

## 2. Sunucuyu kur

Ana bilgisayarda repoyu kalıcı bir dizine clone et ve kilit dosyasını değiştirmeden
bağımlılıkları kur:

```powershell
git clone <REPOSITORY_URL> C:\Projects\mcp-project-memory
Set-Location C:\Projects\mcp-project-memory
uv sync --frozen --all-groups
uv run --frozen pytest
```

Testlerin tamamı geçmeden gerçek proje vault'una bağlanma. Sunucu stdio üzerinden
çalıştığı için `mcp-obsidian` komutunu tek başına başlatınca terminalde beklemesi
normaldir; asıl bağlantı doğrulaması istemci içinden yapılır.

## 3. Boş test vault'unu hazırla

1. Obsidian'da yalnız bu deneme için yeni ve boş bir vault oluştur.
2. [Local REST API 4.1.7 release](https://github.com/coddingtonbear/obsidian-local-rest-api/releases/tag/4.1.7)
   sayfasındaki `main.js`, `manifest.json` ve `styles.css` dosyalarını
   `<vault>/.obsidian/plugins/obsidian-local-rest-api/` dizinine koy; Obsidian'ı
   yeniden yükle ve eklentiyi etkinleştir. Mevcut 15 Obsidian aracının tamamı
   için V1 uyumluluk sürümü `4.1.7`'dir; community directory güncel bir 5.x
   sürümü kuruyorsa onu V1 kurulumu için kullanma.
3. HTTPS portunu doğrula; varsayılan değer `27124`.
4. API anahtarını kopyala fakat repodaki hiçbir izlenen dosyaya yazma.

Ayrıntılı kabul senaryoları için
[canlı Obsidian smoke testi](LIVE_OBSIDIAN_SMOKE_TEST.md) kullanılacaktır.

## 4. Yerel sırları hazırla

Örnek PowerShell dosyasını Git tarafından yok sayılan yerel dosyaya kopyala:

```powershell
Copy-Item docs\config-examples\project-memory.env.ps1.example .project-memory.env.ps1
```

Dosyada API anahtarını ve bu reponun mutlak yolunu doldur. Ardından Claude Code
veya Codex CLI'ı başlatacağın aynı PowerShell oturumunda yükle:

```powershell
. .\.project-memory.env.ps1
```

Bu değişkenler yalnızca o PowerShell sürecine ve onun başlattığı alt süreçlere
aktarılır. Codex masaüstü uygulaması kullanılacaksa uygulama bu değişkenleri
görebilecek şekilde başlatılmalı veya `OBSIDIAN_API_KEY` Windows kullanıcı ortam
değişkeni olarak ayrıca tanımlanıp uygulama yeniden başlatılmalıdır. Kullanıcı
ortam değişkeninin Windows profilinde düz metin olarak tutulduğu unutulmamalıdır.

Alternatif olarak sunucu repo kökündeki Git-ignore edilmiş `.env` dosyasını
okuyabilir; ancak farklı çalışma dizinleri ve istemciler arasında en açık yol,
anahtarı MCP istemcisinin ortamından sunucuya aktarmaktır.

## 5. Codex yapılandırması

[`codex-config.toml.example`](config-examples/codex-config.toml.example)
içeriğini hedef projenin `.codex/config.toml` dosyasına veya kullanıcı düzeyindeki
`~/.codex/config.toml` dosyasına ekle. `command` ve `cwd` alanlarındaki repo
yolunu ana bilgisayara göre değiştir. `command`, kurulumda oluşturulan
`.venv\Scripts\mcp-obsidian.exe` dosyasını doğrudan çalıştırır.

Proje düzeyindeki yapılandırma her kod reposunun hangi hafıza sunucusunu
kullandığını görünür kılar. API anahtarı dosyaya konmaz; `env_vars` aracılığıyla
Codex sürecinin ortamından aktarılır.

Doğrula:

```powershell
codex mcp list
```

Codex arayüzünde `/mcp` ile bağlantıyı ve 19 aracın görünürlüğünü kontrol et.
Codex'in güncel resmi MCP belgelerine göre masaüstü uygulaması, CLI ve IDE
uzantısı aynı Codex host yapılandırmasını paylaşır; proje düzeyindeki
`.codex/config.toml` yalnız güvenilen projelerde yüklenir:
[OpenAI MCP belgeleri](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).

## 6. Claude Code yapılandırması

[`claude-mcp.json.example`](config-examples/claude-mcp.json.example) dosyasını
hedef kod reposunun köküne `.mcp.json` adıyla kopyala. Şablon sır içermez;
`${OBSIDIAN_API_KEY}` ve `${MCP_PROJECT_MEMORY_REPO}` çalışma ortamından alınır.

```powershell
Copy-Item C:\Projects\mcp-project-memory\docs\config-examples\claude-mcp.json.example .mcp.json
claude mcp list
```

Claude Code proje kapsamındaki `.mcp.json` dosyasını ekipçe paylaşılabilir
yapılandırma olarak destekler ve ilk kullanımda proje sunucusuna güven/onay
isteyebilir. Ortam değişkeni genişletme sözdizimi de resmi olarak desteklenir:
[Claude Code MCP belgeleri](https://code.claude.com/docs/en/mcp).

Ekip büyüdüğünde `.mcp.json` repoya alınabilir; dosyada hiçbir sır bulunmamalıdır.
Her geliştirici yalnız kendi `OBSIDIAN_API_KEY` ve `MCP_PROJECT_MEMORY_REPO`
değerlerini yerel ortamında tanımlar.

## 7. Ortak agent davranışını tanımla

[Agent Memory Protocol](AGENT_MEMORY_PROTOCOL.md) içindeki kısa talimatı hedef
projenin agent talimatlarına ekle. MCP'nin bağlı olması tek başına devamlılığı
garanti etmez; her anlamlı oturumun başlangıcında context okunması ve sonunda
checkpoint bırakılması gerekir.

Minimum akış:

```text
ilk boş vault: project_init
her oturum başı: project_get_context
çalışma: obsidian_* ve güvenli project_* araçları
anlamlı oturum sonu: project_checkpoint
sonraki agent: project_get_context
```

## 8. Canlı kabul testi

İki istemciden en az biriyle
[LIVE_OBSIDIAN_SMOKE_TEST.md](LIVE_OBSIDIAN_SMOKE_TEST.md) adımlarını uygula.
Ardından ikinci istemciyi başlat, `project_get_context` çağır ve ilk istemcinin
checkpoint'ini değiştirmeden okuyabildiğini doğrula.

Başarılı kabul ölçütleri:

- 15 mevcut `obsidian_*` aracı kullanılabilir.
- 4 `project_*` aracı kayıtlıdır.
- `project_init` tekrar çağrıldığında mevcut içerik korunur.
- Codex'in yazdığı checkpoint Claude Code tarafından veya tersi yönde okunur.
- `PROGRESS.md` Obsidian içinde yapılan gelişmeleri gösterir.
- Bekleyen kritik kararlar `pending_approvals` olarak görünür ve otomatik olarak
  `DECISIONS.md` içine girmez.
- MCP süreci yeniden başladıktan sonra bağlam vault'tan geri yüklenir.

## 9. Günlük çalışma kuralı

V1'de Claude Code ve Codex aynı vault'a eşzamanlı yazmamalıdır. Agent değişimi
şu sırada yapılır:

1. Aktif agent işi durdurur ve `project_checkpoint` çağırır.
2. Checkpoint başarısı doğrulanır.
3. Aktif agent kapanır veya yazmayı bırakır.
4. Sonraki agent `project_get_context` ile başlar.

Bu disiplin tek bilgisayarda bağlam kaybını önleyen ilk güvenilir tabandır.
Revision/hash tabanlı eşzamanlılık koruması ancak gerçek kullanımda ihtiyaç
kanıtlanırsa sonraki sürüme eklenmelidir.
