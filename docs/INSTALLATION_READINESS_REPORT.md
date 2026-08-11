# Kurulum hazır oluş ve risk raporu

Tarih: 2026-08-10

Bu rapor V1 hedefini esas alır: tek bilgisayarda, bir Obsidian vault'u
üzerinden Codex/Work ve daha sonra Claude Code arasında kalıcı proje bağlamı.
Çok kullanıcı, eşzamanlı yazma, vektör veritabanı ve dağıtık senkronizasyon bu
değerlendirmenin dışındadır.

## Mevcut durum

- 15 upstream Obsidian aracı korunuyor.
- `project_create_file_safe`, `project_init`, `project_get_context` ve
  `project_checkpoint` ile toplam 19 MCP aracı sunuluyor.
- Proje yolları vault'a göreli `PROJECT_MEMORY_ROOT` altında doğrulanıyor.
- MCP initialization talimatı yeni agent'a bağlamı önce yüklemesini ve anlamlı
  iş sonunda checkpoint bırakmasını bildiriyor.
- Docker runtime kilitli bağımlılıklar ve root olmayan kullanıcıyla çalışıyor.
- Windows Work mode kurulumu `scripts/setup-work-mode.ps1` ile tek komuta
  indirildi.

## Bu incelemede doğrulananlar

- MCP Python SDK `1.29.0` kilitlendi ve temiz ortam senkronizasyonu geçti.
- Gerçek subprocess stdio `initialize` + `tools/list` entegrasyon testi geçti.
- Test paketi: 160 başarılı.
- Kod kapsamı: %99.
- Pyright: 0 hata, 0 uyarı.
- `pip check`: kırık bağımlılık yok.
- `uv lock --check`: kilit dosyası güncel.
- PowerShell kurulum betiği sözdizimi kontrolünden geçti.
- Config birleştirme testi diğer MCP sunucusunu ve takip eden TOML tablolarını
  korudu; bir yedek oluşturdu, UTF-8 BOM eklemedi ve ikinci çalıştırmada aynı
  sonucu değiştirmeden bıraktı.
- Docker Desktop `4.86.0` / Engine `29.7.2` üzerinde image build geçti.
- Image içinde gerçek stdio `initialize` + `tools/list`, 19 araç ve sunucu
  talimatları doğrulandı.
- Runtime'ın root olmayan `mcp` kullanıcısıyla çalıştığı doğrulandı.
- Container'dan `host.docker.internal:27124` üzerindeki korumalı Obsidian
  endpoint'ine erişildi; geçersiz test anahtarı beklendiği gibi `401` aldı.

Bu bilgisayarda gerçek Obsidian API anahtarı kayıtlı olmadığı için vault
içeriğini okuyan authenticated canlı test bilinçli olarak çalıştırılmadı. Bu
kontrol kurulum betiğinde yer alır ve yarın ana bilgisayardaki son dış bağımlı
kabul kapısıdır.

## Yarın kurulumu engelleyebilecek riskler

| Öncelik | Risk | Etki | Mevcut önlem |
|---|---|---|---|
| P0 | Docker Desktop veya Obsidian eklentisi hazır değil | Proje hafızası kullanılamaz | Kurulum betiği config'i yazmadan ön kontrol yapar; `required = false` sayesinde Work sohbeti yine açılır |
| P0 | Yanlış/eski image | Initialization yanıtı kapanabilir veya araç sayısı farklı olabilir | Image her normal kurulumda yeniden build edilir; SDK sürümü ve 19 araç doğrulanır |
| P0 | Yanlış API anahtarı veya `Bearer ` öneki | Obsidian çağrıları 401 verir | Anahtar gizli girişle alınır, önek reddedilir, container'dan canlı bağlantı sınanır |
| P0 | Yanlış `PROJECT_MEMORY_ROOT` | Yanlış proje hafızası okunur/yazılır | Güvensiz yol biçimleri reddedilir; ilk kabulte dönen yollar insan tarafından kontrol edilir |
| P1 | Local REST API 5.x endpoint farkları | Özellikle periodic-note araçları bozulur | V1 için doğrulanmış `4.1.7` sürümü belgelenmiştir |
| P1 | Work uygulaması eski ortamı tutar | Docker'a değişkenler aktarılmaz | Kurulum sonrası sistem tepsisi dahil tam yeniden başlatma zorunludur |
| P1 | Birden çok agent aynı anda yazar | Son yazan öncekinin STATE/HANDOFF değişikliğini ezebilir | V1 protokolü sırayla çalışma ve handoff öncesi checkpoint gerektirir |

## Bilinen tasarım sınırları

1. Initialization `instructions` güçlü bir varsayılan sağlar fakat agent'ın
   bunu her koşulda uygulamasını mekanik olarak zorlamaz. Kritik repolarda aynı
   protokolün `AGENTS.md` veya `CLAUDE.md` içine eklenmesi ikinci korumadır.
2. Sohbet veya uygulama aniden kapanırsa sunucunun otomatik bir "oturum
   kapanıyor" olayı yoktur. Son başarılı checkpoint'ten sonraki sohbet bağlamı
   kaybolabilir.
3. `project_checkpoint` tek bir atomik REST işlemi değildir. Session kaydı,
   STATE, HANDOFF, DECISIONS ve PROGRESS güncellemelerinden biri ağ hatasıyla
   yarım kalabilir. Append-only session dosyası kurtarma dayanağıdır; araç
   sonucu kontrol edilmelidir.
4. Checkpoint, ROADMAP ve TODO maddelerinin gerçekten bittiğini tahmin edip
   kutuları otomatik işaretlemez. Agent bunları kanıta göre checkpoint'ten önce
   uzlaştırmalıdır.
5. `project_create_file_safe` ardışık kullanımda güvenlidir fakat GET + PUT
   atomik değildir. Eşzamanlı iki writer aynı dosyayı oluşturmaya çalışırsa
   yarış oluşabilir; V1 zaten eşzamanlı yazmayı desteklemez.
6. Proje araçları root sınırını uygular. Uyumluluk için korunan genel Obsidian
   araçları vault genelinde çalışabilir; bu nedenle agent talimatı ve kullanıcı
   onayı hâlâ önemlidir.
7. Windows kullanıcı ortamındaki API anahtarı düz metindir. Bu, tek kullanıcılı
   V1 için kabul edilen ödündür; anahtar Git'e veya Codex config'e yazılmaz.
8. Yerel REST eklentisinin self-signed HTTPS sertifikası nedeniyle TLS
   doğrulaması kapalıdır. Bağlantı yalnız yerel ana bilgisayara yöneltilmelidir.
9. Bir Work uygulaması oturumunda tek bir `PROJECT_MEMORY_ROOT` aktiftir.
   Başka projeye geçiş ortam değişkeni değişikliği ve uygulamanın yeniden
   başlatılmasını gerektirir.
10. `required = false` Work'ün bir MCP arızası yüzünden tamamen kilitlenmesini
    önler; bunun karşılığında kullanıcı MCP bağlı değilken sohbet açabilir.
    Kalıcı bağlam gerektiren işe başlamadan `/mcp` durumu kontrol edilmelidir.

## V1 sonrası iyileştirme sırası

1. Checkpoint işlem günlüğü ve yarım yazım kurtarma testi.
2. ROADMAP/TODO uzlaştırmasını tahmin etmeden yapan açık, opt-in bir araç.
3. Birden fazla yerel proje için adlandırılmış profil veya launcher desteği.
4. Local REST API'nin yeni ana sürümü için endpoint uyumluluk katmanı.
5. Ancak gerçek ihtiyaç oluşursa writer lock ve çok kullanıcılı model.

## Ana bilgisayar kabul kapısı

Kurulum tamamlanmış sayılmadan şu sıra doğrulanmalıdır:

1. Tek komut kurulum betiği hatasız biter.
2. ChatGPT masaüstü tamamen yeniden başlatılır.
3. Yeni Work sohbetinde `/mcp`, `project_memory` ve 19 aracı gösterir.
4. `project_get_context` yalnız beklenen vault root'undaki yolları döndürür.
5. Küçük bir görev add/list/complete akışıyla doğrulanır.
6. `project_checkpoint` session yolu döndürür.
7. Yeni bir Work sohbeti yalnız hafızadan kaldığı yeri doğru açıklar.

İlk dört maddeden biri başarısızsa gerçek proje dosyalarına yazma testi
yapılmamalıdır.
