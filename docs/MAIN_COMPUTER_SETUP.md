# Ana bilgisayar kurulumu — mevcut proje

Bu rehber `mcp-project-memory` sunucusunu yeni bir Windows bilgisayara kurup
çalışan bir kaynak kod projesini mevcut Obsidian vault'uyla bağlamak içindir.
Önerilen dağıtım Docker Desktop'tır: Obsidian ve vault Windows'ta, stdio MCP
sunucusu container içinde çalışır.

## 1. Kurulum sınırı

Kurulum şu üç konumu birbirinden ayırır:

1. MCP sunucu reposu: örneğin `C:\Tools\mcp-project-memory`.
2. Mevcut kaynak kod reposu: örneğin `C:\Projects\MyExistingApp`.
3. Obsidian vault'u ve içindeki hafıza kökü: örneğin
   `Projects/MyExistingApp`.

Kaynak kod ile vault aynı klasör olmak zorunda değildir. Vault container'a
mount edilmez. Mevcut vault önemli veri içeriyorsa önce yedek alın.

## 2. Ön koşullar

- Git
- Docker Desktop
- Obsidian
- Obsidian Local REST API `>=4.1.7` ve `<6.0.0`
- Codex veya Claude Code

Kurulum ve bağlantı kontrolleri Local REST API `4.1.7` ve `5.1.0` ile
çalışacak biçimde tasarlanmıştır. `>=4.1.7` ve `<6.0.0` sürümleri kabul edilir.

## 3. Sunucuyu kurun

```powershell
git clone https://github.com/ysferencakir/mcp-project-memory.git C:\Tools\mcp-project-memory
Set-Location C:\Tools\mcp-project-memory
```

## 4. Obsidian'ı hazırlayın

1. Kullanacağınız mevcut vault'u Obsidian'da açın.
2. Local REST API eklentisini etkinleştirin.
3. HTTPS portunu doğrulayın; varsayılan `27124`.
4. Eklenti ayarındaki API anahtarını kopyalayın.
5. Vault yalnız bu projeye ait değilse proje için bir alt klasör seçin.

`PROJECT_MEMORY_ROOT` vault'a göreli POSIX klasördür. Örnek:

```text
Projects/MyExistingApp
```

Başında slash, `..`, ters slash veya URL-encoded parça kullanmayın. Vault
yalnız bu projeye aitse kök boş bırakılabilir.

## 5. Önerilen tak-çalıştır Work mode kurulumu

Docker Desktop, Obsidian ve Local REST API eklentisi açıkken repo kökündeki
`INSTALL.cmd` dosyasına çift tıklayın. Yalnız vault'a göreli proje hafıza
klasörünü ve `Bearer ` öneki olmayan API anahtarını girin. Vault yalnız bu
projeye aitse ilk soruyu boş bırakın.

Kurulum tamamlanınca `CHECK.cmd` dosyasına çift tıklayın. Tüm satırlar `[OK]`
ve sonuç `ALL CHECKS PASSED` olmalıdır. Bu kontrol API anahtarını veya vault
içeriğini yazdırmaz.

PowerShell kullananlar için aynı kurulumun komut satırı karşılığı:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-work-mode.ps1
```

Betik önce vault-relative proje klasörünü sorar; vault yalnız bu projeye aitse
boş bırakıp Enter'a basın. Ardından Local REST API anahtarını güvenli girişle
ister; anahtara `Bearer ` eklemeyin.

Betik yapılandırmayı yazmadan önce Docker build, gerçek MCP `initialize`, 19
araçlık `tools/list`, uyumlu Local REST API sürümü (`>=4.1.7`, `<6.0.0`), API
anahtarı ve container'dan Obsidian erişimini kontrol eder. Ardından Windows
kullanıcı ortamını ve kullanıcı-geneli `%USERPROFILE%\.codex\config.toml`
dosyasını günceller. Var olan config önce zaman damgalı bir dosyaya yedeklenir;
diğer ayarlar korunur.

Bir kontrol başarısız olursa `project_memory` bloğu yazılmaz. Yapılandırma
`required = false` kullanır; Docker veya sunucu daha sonra çalışmazsa yalnız
MCP bağlantısı kaybolur, yeni Work sohbeti yine açılır. Daha önce kayıtlı
anahtarı değiştirmek için `-ResetApiKey`, aynı image ile yalnız kontrolleri
tekrarlamak için `-SkipBuild` ekleyin.

## 6. Work mode bağlantısını doğrulayın

ChatGPT masaüstü uygulamasını sistem tepsisi dahil tamamen kapatıp yeniden
açın. Yeni Work sohbetinde `/mcp` görünümünde `project_memory` ve 19 araç
görünmelidir. CLI kuruluysa:

```powershell
codex mcp list
```

Repo içinde `.codex` klasörü aranmaz; Work mode masaüstü, CLI ve IDE aynı
kullanıcı-geneli Codex yapılandırmasını kullanır. Resmi biçim:
[OpenAI MCP belgeleri](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).

### Work sohbeti MCP yüzünden açılamıyorsa

Repo kökündeki `DISABLE.cmd` dosyasına çift tıklayın. Betik kullanıcı-geneli
config'i yedekler ve yalnız `[mcp_servers.project_memory]` bloğunu şu güvenli
duruma getirir:

```toml
enabled = false
required = false
```

Diğer MCP sunucuları, Docker image'ı, ortam değişkenleri ve Obsidian vault'u
korunur. ChatGPT'yi sistem tepsisi dahil tamamen kapatıp açın. Sorun
giderilince `INSTALL.cmd` bağlantıyı yeniden doğrular ve etkinleştirir.

Yalnız elle müdahale gerekirse kullanıcı-geneli config'i açın:

```powershell
notepad "$env:USERPROFILE\.codex\config.toml"
```

Yalnız `[mcp_servers.project_memory]` bloğundaki `enabled` ve `required`
değerlerini yukarıdaki gibi `false` yapın; diğer tabloları değiştirmeyin.

Bu üç yardımcı dosya Docker Desktop, Obsidian veya eklentiyi kurmaz ve
ChatGPT'yi kendiliğinden kapatmaz. Windows açılışında Docker Desktop ile
Obsidian'ın başlaması ve doğru vault'un açılması işletim sistemi/uygulama
ayarlarıdır; bir kez etkinleştirilmelidir.

## Elle kurulum — yedek yol

Otomatik betik kullanılamıyorsa önce image'ı oluşturun:

```powershell
docker build --pull -t mcp-project-memory:local .
```

Sonra değişkenleri Windows kullanıcı ortamında tanımlayın:

```powershell
[Environment]::SetEnvironmentVariable("OBSIDIAN_API_KEY", "LOCAL_REST_API_KEY", "User")
[Environment]::SetEnvironmentVariable("PROJECT_MEMORY_ROOT", "Projects/MyExistingApp", "User")
```

API anahtarı Windows kullanıcı ortamında düz metin olarak saklanır; bu V1'in
tek kullanıcılı yerel kurulum tercihidir. Anahtarı Git'e veya izlenen bir
dosyaya yazmayın. Ardından kullanıcı-geneli Codex yapılandırmasını açın:

```powershell
$codexConfigDir = Join-Path $env:USERPROFILE ".codex"
New-Item -ItemType Directory -Force $codexConfigDir
notepad (Join-Path $codexConfigDir "config.toml")
```

Mevcut ayarları silmeden
`C:\Tools\mcp-project-memory\docs\config-examples\codex-docker-config.toml.example`
içindeki `[mcp_servers.project_memory]` bloğunu ekleyin. Masaüstü uygulamasını
tamamen yeniden başlatın.

## 7. Claude Code yapılandırması

Claude Code kullanılacağı zaman mevcut kaynak kod reposunda:

```powershell
Copy-Item C:\Tools\mcp-project-memory\docs\config-examples\claude-docker-mcp.json.example .mcp.json
claude mcp list
```

İlk interaktif açılışta proje MCP sunucusunu onaylayın ve `/mcp` ile kontrol
edin. `.mcp.json`, API anahtarını ve proje kökünü PowerShell ortamından alır.
Resmi biçim: [Claude Code MCP belgeleri](https://code.claude.com/docs/en/mcp).

Claude aboneliği yoksa bu adım ertelenebilir; Codex tek başına aynı kalıcı
hafıza akışını kullanabilir.

## 8. Agent talimat dosyaları

MCP sunucusu hafıza protokolünü initialization `instructions` alanıyla Work
mode ve Codex'e otomatik bildirir. Her yeni sohbete ayrıca başlangıç prompt'u
vermek gerekmez. MCP talimatlarını desteklemeyen istemciler veya ek koruma
için hazır protokol hedef kaynak kod reposuna kopyalanabilir:

```powershell
Copy-Item C:\Tools\mcp-project-memory\docs\config-examples\agent-memory-instructions.md.example AGENTS.md
Copy-Item C:\Tools\mcp-project-memory\docs\config-examples\agent-memory-instructions.md.example CLAUDE.md
```

Mevcut talimat dosyaları varsa overwrite etmeyin; şablondaki bölümü mevcut
dosyaya birleştirin.

## 9. Mevcut projeyi bootstrap edin

İlk agent'a README'deki “Mevcut projeyi ilk kez hafızaya alma” prompt'unu
verin. Güvenli sıra:

1. `project_get_context`
2. Belgeler gerçekten yoksa bir kez `project_init`
3. Kaynak repo incelemesi
4. Kanıta dayalı PROJECT/STATE/ROADMAP/TODO içeriği
5. Plan belgelerini geri okuma
6. `project_checkpoint`

`project_init` mevcut dosyaları korur. Yine de root yanlış vault klasörüne
işaret ediyorsa devam etmeyin; önce `PROJECT_MEMORY_ROOT` değerini düzeltin.

## 10. Kabul ölçütleri

- MCP sunucusu `/mcp` içinde bağlıdır.
- Toplam 19 araç görünür.
- `project_get_context` doğru vault yollarını gösterir.
- Yedi varsayılan proje belgesi yüklenir.
- Checkpoint sonrasında `sessions/...md`, STATE, HANDOFF ve PROGRESS Obsidian'da
  görünür.
- Container yeniden başladığında aynı checkpoint geri yüklenir.
- `.env`, `.project-memory.env.ps1` ve API anahtarı Git'te değildir.

Ayrıntılı test için [canlı smoke testi](LIVE_OBSIDIAN_SMOKE_TEST.md) kullanın.

## 11. Günlük agent değişimi

1. Aktif agent testlerini çalıştırır.
2. ROADMAP ve TODO'yu doğrulanmış sonuçlarla uzlaştırır.
3. `project_checkpoint` çağırır ve session yolunu doğrular.
4. Yazmayı bırakır.
5. Sonraki agent `project_get_context` ile başlar.

İki agent aynı vault/root'a aynı anda yazmamalıdır.
