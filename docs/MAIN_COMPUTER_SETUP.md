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
- Obsidian Local REST API `4.1.7`
- Codex veya Claude Code

V1'in 15 upstream Obsidian aracı `4.1.7` ile doğrulanmıştır. Local REST API
`5.x`, periodic-note endpoint'lerini kaldırdığı için tam V1 uyumluluk sürümü
değildir.

## 3. Sunucuyu kurun

```powershell
git clone https://github.com/ysferencakir/mcp-project-memory.git C:\Tools\mcp-project-memory
Set-Location C:\Tools\mcp-project-memory
docker build --pull -t mcp-project-memory:local .
```

Docker Desktop çalışmıyorsa build başlamaz. Image root olmayan kullanıcıyla
çalışır ve API anahtarı içermez.

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

## 5. Yerel ortamı hazırlayın

Sunucu reposunda:

```powershell
Copy-Item docs\config-examples\project-memory.env.ps1.example .project-memory.env.ps1
```

Git-ignore edilen dosyada değerleri düzenleyin:

```powershell
$env:OBSIDIAN_API_KEY = "LOCAL_REST_API_KEY"
$env:MCP_PROJECT_MEMORY_REPO = "C:\Tools\mcp-project-memory"
$env:PROJECT_MEMORY_ROOT = "Projects/MyExistingApp"
```

Codex CLI veya Claude Code'u başlatacağınız PowerShell'de yükleyin:

```powershell
. C:\Tools\mcp-project-memory\.project-memory.env.ps1
```

Bu değişkenler yalnız o süreç ve alt süreçleri için geçerlidir. Masaüstü
uygulaması kullanılacaksa değişkenleri görecek biçimde yeniden başlatılmalıdır.
API anahtarını izlenen dosyaya yazmayın.

## 6. Codex yapılandırması

Mevcut kaynak kod reposunda:

```powershell
Set-Location C:\Projects\MyExistingApp
New-Item -ItemType Directory -Force .codex
Copy-Item C:\Tools\mcp-project-memory\docs\config-examples\codex-docker-config.toml.example .codex\config.toml
codex mcp list
```

Codex'te `/mcp` görünümünde `project_memory` ve 19 araç görünmelidir. Proje
kapsamındaki `.codex/config.toml` yalnız güvenilen projelerde yüklenir. Resmi
biçim: [OpenAI MCP belgeleri](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).

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

Hazır protokolü hedef kaynak kod reposuna kopyalayın:

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
