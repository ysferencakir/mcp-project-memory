# mcp-project-memory

`mcp-project-memory`, Codex ve Claude Code gibi coding agent'larının proje
bağlamını normal Markdown dosyaları olarak bir Obsidian vault'unda kalıcı
tutmasını sağlayan stdio MCP sunucusudur.

Sunucu mevcut `mcp-obsidian` araçlarını korur ve bunların üzerine proje
başlatma, bağlam yükleme, güvenli dosya oluşturma ve checkpoint/handoff
araçlarını ekler. Uyumluluk nedeniyle Python paketi ve çalıştırılabilir komut
şimdilik `mcp-obsidian` adını kullanmaya devam eder.

## V1 çalışma modeli

```text
Codex veya Claude Code
        ↓ stdio MCP
mcp-project-memory
        ↓ HTTPS REST
Obsidian Local REST API
        ↓
Mevcut Obsidian vault'u / proje klasörü
```

V1'in amacı tek bilgisayarda güvenilir proje devamlılığıdır:

- Bağlam Markdown olarak Obsidian'da kalır.
- Agent konuşma geçmişine güvenmeden projeyi yeniden yükleyebilir.
- Codex ve Claude aynı vault ve `PROJECT_MEMORY_ROOT` değerini kullanabilir.
- Agent'lar aynı anda yazmaz; checkpoint bırakarak sırayla çalışır.
- Mevcut proje kaynak kodu container'a veya Obsidian'a kopyalanmaz.
- Vector database, embedding, authentication ve çok kullanıcılı eşzamanlılık
  V1 kapsamı dışındadır.

## Yeni bilgisayara kurulum — mevcut proje

Bu bölüm Windows + Docker Desktop için önerilen kısa kurulumdur. Ayrıntılar
için [Ana bilgisayar kurulumu](docs/MAIN_COMPUTER_SETUP.md) ve
[Docker kurulumu](docs/DOCKER_SETUP.md) belgelerine bakın.

### 1. Ön koşullar

- Git
- Docker Desktop
- Obsidian
- Obsidian Local REST API community eklentisi `4.1.7`
- Codex; daha sonra istenirse Claude Code
- Kullanılacak mevcut Obsidian vault'u ve kaynak kod reposu

V1'in 15 mevcut Obsidian aracı Local REST API `4.1.7` ile doğrulandı. Eklenti
`5.x`, bazı upstream endpoint'leri kaldırdığı için tam V1 uyumluluk sürümü
olarak kabul edilmez.

Mevcut vault önemli veri içeriyorsa kuruluma başlamadan önce normal yedeğini
alın. MCP sunucusu vault'a REST API üzerinden erişir; vault container'a mount
edilmez.

### 2. Sunucuyu klonlayın

```powershell
git clone https://github.com/ysferencakir/mcp-project-memory.git C:\Tools\mcp-project-memory
Set-Location C:\Tools\mcp-project-memory
```

### 3. Obsidian bağlantısını hazırlayın

1. Kullanılacak vault'u Obsidian'da açın.
2. Local REST API `4.1.7` eklentisini etkinleştirin.
3. HTTPS portunun `27124` olduğunu doğrulayın.
4. Eklenti ayarındaki API anahtarını kopyalayın.

API anahtarını repoya, Dockerfile'a, `.codex/config.toml` veya `.mcp.json`
içine yazmayın.

### 4. Tek komutla Work mode kurulumunu tamamlayın

`PROJECT_MEMORY_ROOT`, Obsidian vault'una göreli klasördür:

- Vault yalnız bu projeye aitse: boş değer kullanın.
- Aynı vault'ta birden fazla proje varsa: örneğin `Projects/MyExistingApp`.
- Başında `/` kullanmayın, `..` kullanmayın ve Windows `\` ayıracı
  kullanmayın.

Obsidian açıkken aşağıdaki tek komutu çalıştırın:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-work-mode.ps1
```

Betik önce vault-relative proje klasörünü sorar; vault yalnız bu projeye aitse
boş bırakıp Enter'a basın. Ardından API anahtarını ekranda göstermeden ister
ve şunları sırayla yapar:

- Docker Desktop'ın hazır olduğunu kontrol eder.
- Image'ı kilitli bağımlılıklarla oluşturur.
- Container içinde gerçek MCP `initialize` ve `tools/list` çağrılarını yapar.
- Container'dan Obsidian bağlantısını, API anahtarını ve Local REST API
  `4.1.7` sürümünü doğrular.
- Ortam değişkenlerini Windows kullanıcı kapsamında kaydeder.
- Mevcut `%USERPROFILE%\.codex\config.toml` dosyasını yedekleyip yalnız
  `project_memory` bloğunu ekler veya günceller.

Kontroller başarısız olursa betik Codex yapılandırmasını değiştirmez. Daha
önce kayıtlı anahtarı değiştirmek için `-ResetApiKey` ekleyin. Image zaten
aynı commit'ten oluşturulduysa tekrar denemede `-SkipBuild` kullanılabilir.

Yapılandırma `required = false` kullanır. Docker veya project-memory daha sonra
başlatılamazsa yeni Work sohbetleri yine açılır; yalnız ilgili MCP araçları
kullanılamaz görünür. Bağlam gerektiren proje işine `/mcp` içinde
`project_memory` bağlı görünmeden başlanmamalıdır.

Image API anahtarını içermez, kilitli `uv.lock` bağımlılıklarını kullanır ve
root olmayan `mcp` kullanıcısıyla çalışır. MCP Python SDK, mevcut düşük
seviyeli Server API'siyle uyumlu güncel bakım serisi olan `1.29.0` sürümüne
sabitlenmiştir. Kırıcı değişiklik içeren SDK 2.x'e geçiş ayrı bir çalışma
olacaktır.

### 5. Work mode bağlantısını doğrulayın

ChatGPT masaüstü uygulamasını sistem tepsisi dahil tamamen kapatıp yeniden
açın. Yeni bir Work sohbetinde `/mcp` görünümünde `project_memory` ve toplam
19 araç görünmelidir. CLI kuruluysa ek olarak:

```powershell
codex mcp list
```

Betik kullanıcı-geneli `%USERPROFILE%\.codex\config.toml` dosyasını kullanır;
repo içinde `.codex` klasörü oluşturmanız gerekmez. Masaüstü, CLI ve IDE
istemcileri aynı host yapılandırmasını paylaşır. Güncel biçim için
[resmi OpenAI MCP belgesine](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)
bakın.

Betik kullanılamazsa ayrıntılı elle kurulum için
[Ana bilgisayar kurulumu](docs/MAIN_COMPUTER_SETUP.md#elle-kurulum-yedek-yol)
bölümünü izleyin.

### 6. Claude Code'u bağlayın

Claude Code kullanılacağı zaman hedef kaynak kod reposunda:

```powershell
Copy-Item C:\Tools\mcp-project-memory\docs\config-examples\claude-docker-mcp.json.example .mcp.json
claude mcp list
```

Claude Code proje kapsamındaki `.mcp.json` için ilk açılışta güven onayı
isteyebilir. `/mcp` ile bağlantıyı doğrulayın. Şablon sır içermez ve ortam
değişkenlerini `${OBSIDIAN_API_KEY}` ile `${PROJECT_MEMORY_ROOT}` üzerinden
alır. Güncel kapsam ve değişken genişletme davranışı için
[resmi Claude Code MCP belgesine](https://code.claude.com/docs/en/mcp) bakın.

## Mevcut projeyi ilk kez hafızaya alma

`project_init` mevcut hafıza dosyalarını ezmez. Yalnız bulunmayan varsayılan
Markdown belgelerini oluşturur. Kaynak kod reposunu değiştirmez.

Codex veya Claude'a ilk bağlantıda şu prompt'u verin; kök ve proje adını
kendinize göre değiştirin:

```text
Bu mevcut proje kalıcı bağlam için project-memory MCP sunucusunu kullanacak.
Yapılandırılmış PROJECT_MEMORY_ROOT değeri Projects/MyExistingApp.

Önce project_get_context çağır. Önceki konuşmalara güvenme. Eksik, kırpılmış
veya dışarıda bırakılmış belgeleri açıkça raporla. Proje hafızası henüz
başlatılmamışsa project_init çağır:

project_name: MyExistingApp
description: Bu mevcut kod tabanının kalıcı proje bağlamı ve agent handoff'u.

Mevcut Obsidian dosyalarını ve kaynak kodu silme veya üzerine yazma. Ardından
repoyu gerçekten incele; PROJECT, STATE, ROADMAP ve TODO belgelerini yalnız
kanıtlanmış mevcut durumla doldur. Bilmediğin kararları uydurma. Değiştirdiğin
plan belgelerini geri oku. Sonunda bootstrap için project_checkpoint bırak ve
oluşan session yolunu bildir.
```

Beklenen varsayılan hafıza yapısı:

```text
PROJECT.md
STATE.md
ROADMAP.md
DECISIONS.md
TODO.md
HANDOFF.md
PROGRESS.md
sessions/
```

Dosya adları yapılandırma sınırındadır; gerekirse
`PROJECT_MEMORY_DOCUMENTS` JSON değişkeniyle değiştirilebilir.

## Agent'a kalıcı talimat ekleme

Sunucu, MCP initialization yanıtında kalıcı hafıza protokolünü
`instructions` alanıyla istemciye bildirir. ChatGPT masaüstü Work mode ve
Codex yeni bir sohbet veya anlamlı proje işi başlarken
`project_get_context`, anlamlı iş veya handoff sonunda `project_checkpoint`
kullanma yönlendirmesini bu alandan alır. Kullanıcının her sohbette başlangıç
prompt'unu yeniden vermesi beklenmez.

MCP istemcisinin talimat desteği olmadığı veya ek koruma istendiği durumda
hedef kod reposunda Codex için `AGENTS.md`, Claude Code için `CLAUDE.md` içine
aynı hafıza protokolü konabilir. Hazır metin:

[`agent-memory-instructions.md.example`](docs/config-examples/agent-memory-instructions.md.example)

Örnek kopyalama:

```powershell
Copy-Item C:\Tools\mcp-project-memory\docs\config-examples\agent-memory-instructions.md.example AGENTS.md
Copy-Item C:\Tools\mcp-project-memory\docs\config-examples\agent-memory-instructions.md.example CLAUDE.md
```

Projede mevcut bir `AGENTS.md` veya `CLAUDE.md` varsa dosyayı değiştirmek
yerine şablondaki “Project memory protocol” bölümünü mevcut talimata ekleyin.

## İsteğe bağlı kurtarma prompt'ları

Aşağıdaki prompt'lar normal günlük kullanımda zorunlu değildir. Yalnız
istemci sunucu talimatını uygulamadığında veya yarım kalan bir oturumu elle
kurtarmak gerektiğinde kullanılır.

### Oturum başlangıcı

```text
PROJECT_MEMORY_ROOT yapılandırmasını kullan. Önce project_get_context çağır.
Önceki konuşmaya güvenmeden STATE, HANDOFF, ROADMAP, TODO, bekleyen onaylar ve
engelleri özetle. Eksik veya kırpılmış bağlam varsa çalışmaya başlamadan söyle.
Son checkpoint'teki sıradaki en küçük doğrulanabilir adımdan devam et.
```

### Oturum sonu / handoff

```text
Yeni geliştirme yapmayı durdur ve bu oturumu kapat. İlgili testleri çalıştır.
ROADMAP ve TODO maddelerini yalnız doğrulanmış sonuçlarla uzlaştır; kısmi veya
belirsiz işleri açık bırak. Değiştirdiğin plan belgelerini geri oku. Ardından
project_checkpoint çağır: summary, completed, files_changed, verification,
decisions, pending_approvals, blockers ve next_steps alanlarını dürüstçe
doldur. Checkpoint başarılı olmadan bağlam kaydedildi deme.
```

### Başka agent'tan devralma

```text
Bu yeni bir agent oturumu. Önceki chat veya insan özetini kaynak kabul etme.
Önce project_get_context çağır. Son session bağlantısını, STATE ve HANDOFF'u
karşılaştır; açık TODO ve ROADMAP maddelerini doğrula. Bir tutarsızlık varsa
önce raporla. Tutarlıysa yalnız sıradaki en küçük işi uygula ve sonunda yeni
checkpoint bırak.
```

## Yazma ve güvenlik kuralları

- Claude Code ve Codex aynı vault'a eşzamanlı yazmamalıdır.
- Agent değişmeden önce aktif agent checkpoint bırakmalı ve yazmayı bırakmalıdır.
- Yeni hafıza dosyası için `project_create_file_safe` tercih edilmelidir.
- `obsidian_put_content` tam dosya overwrite eder; bilinçli kullanılmalıdır.
- Silme, güvenlik, maliyet veya geri döndürülmesi zor mimari kararlar
  `pending_approvals` olarak insana bırakılmalıdır.
- `project_checkpoint`, ROADMAP veya TODO kutularını otomatik tahminle
  tamamlamaz; agent önce belgeleri açıkça uzlaştırmalıdır.
- `.env`, `.project-memory.env.ps1` ve gerçek API anahtarı Git'e girmez.

## MCP araçları

Mevcut 15 Obsidian aracı korunur:

- Listeleme: `obsidian_list_files_in_vault`, `obsidian_list_files_in_dir`
- Okuma: `obsidian_get_file_contents`, `obsidian_batch_get_file_contents`
- Arama: `obsidian_simple_search`, `obsidian_complex_search`,
  `obsidian_search_by_tag`
- Metadata: `obsidian_get_frontmatter`
- Yazma: `obsidian_patch_content`, `obsidian_append_content`,
  `obsidian_put_content`, `obsidian_delete_file`
- Zaman/not geçmişi: `obsidian_get_periodic_note`,
  `obsidian_get_recent_periodic_notes`, `obsidian_get_recent_changes`

Proje hafızası araçları:

- `project_create_file_safe`
- `project_init`
- `project_get_context`
- `project_checkpoint`

## Yapılandırma özeti

Temel değişkenler:

```text
OBSIDIAN_API_KEY=yerel-api-anahtarı
OBSIDIAN_HOST=host.docker.internal
OBSIDIAN_PORT=27124
OBSIDIAN_PROTOCOL=https
PROJECT_MEMORY_ROOT=Projects/MyExistingApp
```

Docker Desktop Windows/macOS için `host.docker.internal` kullanılır. Linux
Docker Engine için `--network host` ve `OBSIDIAN_HOST=127.0.0.1` kullanın.

Belge yollarını değiştirme örneği:

```text
PROJECT_MEMORY_DOCUMENTS={"state":"status/CURRENT.md","progress":"PROGRESS.md"}
```

Yollar vault'a göreli Markdown yolları olmalıdır. Mutlak yol, `..`, ters slash
ve percent-encoded yol kabul edilmez.

## Doğrulama ve geliştirme

Yeni bilgisayarda gerçek projeye başlamadan önce:

```powershell
uv sync --frozen --all-groups
uv run --frozen pytest
uv run --frozen pyright
```

Docker-only kullanım için host Python kurulumu zorunlu değildir; fakat kaynak
değişikliği yapacaksanız test ve Pyright kontrollerini çalıştırın.

Canlı kabul adımları:

- [Canlı Obsidian smoke testi](docs/LIVE_OBSIDIAN_SMOKE_TEST.md)
- [Agent memory protokolü](docs/AGENT_MEMORY_PROTOCOL.md)
- [Docker ayrıntıları](docs/DOCKER_SETUP.md)
- [Kurulum hazır oluş ve risk raporu](docs/INSTALLATION_READINESS_REPORT.md)

Testler ve `openapi.yaml` geliştirme/uyumluluk varlıklarıdır; yayınlanan Docker
runtime image'ına dahil edilmezler.
