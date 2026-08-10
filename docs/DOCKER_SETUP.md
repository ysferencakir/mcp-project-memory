# Docker kurulumu — V1

Docker image yalnız `mcp-project-memory` stdio sunucusunu çalıştırır. Obsidian
ve Local REST API eklentisi ana bilgisayarda çalışmaya devam eder; vault
container'a mount edilmez. Sunucu vault'a yalnız authenticated REST API
üzerinden erişir.

## Container ana bilgisayara nasıl bağlanır?

Local REST API varsayılan olarak `127.0.0.1:27124` üzerinde dinler. Container
içindeki normal `127.0.0.1` container'ın kendisidir.

- Docker Desktop Windows ve macOS'ta `OBSIDIAN_HOST=host.docker.internal`
  kullanın. Docker Desktop bu adı ana bilgisayara yönlendirir; ayrıca host
  networking özelliğini açmanız gerekmez.
- Linux Docker Engine'de container'ı `--network host` ile başlatın ve
  `OBSIDIAN_HOST=127.0.0.1` kullanın.
- Her iki durumda da Linux container kullanılır; vault container'a mount
  edilmez.

Bu ayrım, Docker Desktop'ın taşınabilir host DNS adını tercih ederken Linux'ta
yerel loopback servisine doğrudan erişimi korur.

## Image oluşturma

Repo kökünde:

```powershell
docker build --pull -t mcp-project-memory:local .
```

Dockerfile, Python ve uv image sürümlerini immutable manifest digest'leriyle
sabitler. Uygulama bağımlılıkları `uv.lock` üzerinden
`uv sync --locked --no-dev --no-editable` ile kurulur.
Image içinde API anahtarı veya vault verisi bulunmaz ve runtime root olmayan
`mcp` kullanıcısıyla çalışır.

## Manuel stdio başlatma

Repo kökündeki Git-ignore `.env` dosyası en az şu değerleri içermelidir:

```text
OBSIDIAN_API_KEY=replace-locally
OBSIDIAN_HOST=127.0.0.1
OBSIDIAN_PORT=27124
OBSIDIAN_PROTOCOL=https
PROJECT_MEMORY_ROOT=
```

Sunucuyu stdin açık biçimde başlatın:

```powershell
docker run --rm -i --env-file .env `
  -e OBSIDIAN_HOST=host.docker.internal `
  mcp-project-memory:local
```

Bu komut terminalde kullanıcı arayüzü göstermez; MCP istemcisinden newline
delimited JSON-RPC bekler. `-t` kullanmayın, çünkü pseudo-TTY stdio protokolünü
bozabilir.

## Codex ve Claude Code

- Codex örneği: `docs/config-examples/codex-docker-config.toml.example`
- Claude Code örneği: `docs/config-examples/claude-docker-mcp.json.example`

Örnekler Docker Desktop için `host.docker.internal` kullanır. Docker işlemi API
anahtarını başlatan agent sürecinin ortamından alır. Gerçek anahtarı örnek
dosyalara, Dockerfile'a veya image build argümanlarına yazmayın. Linux Docker
Engine'de örneklerden host override'ını kaldırıp `--network host` ekleyin.

Her proje için `PROJECT_MEMORY_ROOT=` argümanını vault içindeki ilgili klasörle
değiştirin. Aynı vault'a iki agent'ın eşzamanlı yazmaması V1'de hâlâ zorunludur.

## Kabul kontrolü

Docker bulunan hedef bilgisayarda sırasıyla:

1. Image build başarılı olmalı.
2. Container içinden yapılandırılan Obsidian host ve portu erişilebilir olmalı.
3. Gerçek stdio `initialize` ve `tools/list` çağrısı 19 aracı döndürmeli.
4. `project_get_context` yapılandırılmış root'taki belgeleri yüklemeli.
5. Container kapatılıp yeniden açıldıktan sonra aynı context geri gelmeli.
6. Ana testler ve demo testleri ayrıca host geliştirme ortamında geçmeli.

### Doğrulanmış test ortamı

V1 Docker kabulü Windows üzerinde Docker Desktop `4.86.0`, Linux Engine
`29.7.2` ve `host.docker.internal` bağlantısıyla çalıştırıldı. Image build,
non-root runtime, 19 MCP aracı, yedi proje belgesi ve iki ayrı container
başlangıcından sonra aynı kalıcı context doğrulandı.

Bu repoya Docker CLI kurulu olmayan bir bilgisayarda Dockerfile ve
yapılandırmalar statik test edilir; gerçek build/run sonucu başarılı olarak
varsayılmaz.

## Referanslar

- [Docker host network driver](https://docs.docker.com/engine/network/drivers/host/)
- [uv Docker integration](https://docs.astral.sh/uv/guides/integration/docker/)
