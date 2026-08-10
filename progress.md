# mcp-project-memory — İlerleme Günlüğü ve Gelişim Planı

Bu dosya, deponun mevcut durumunu, alınan kararları, doğrulanmış bulguları ve sıradaki geliştirme adımlarını kaydeden yaşayan bir belgedir.

## Vizyon

Amaç, bir yapay zekâ modelinin bağlam penceresine güvenmek değil; bağlam penceresi sıfırlansa, konuşma kaybolsa veya agent değişse bile proje durumunun kalıcı kayıtlardan güvenilir biçimde yeniden kurulabilmesini sağlamaktır.

İlk hedef tek bilgisayarda proje devamlılığıdır:

- Projenin amacı, mevcut durumu, kararları ve sıradaki işleri Obsidian içindeki normal Markdown dosyalarında saklamak.
- Claude Code ve OpenAI Codex'in aynı Obsidian vault ve aynı proje dizinini ortak hafıza olarak kullanması.
- Yeni başlayan bir agent'ın eski konuşmaya erişmeden projeyi anlayıp kaldığı yerden devam edebilmesi.
- Bir agent'ın çalışma sonunda açık ve doğrulanabilir bir handoff bırakması.
- Mevcut Obsidian araçlarını bozmadan bunların üzerine proje seviyesinde küçük bir katman eklemek.

Uzun vadeli hedef, aynı yaklaşımı birden çok agent ve birden çok insan için kullanılabilir hale getirmektir. Çok kullanıcılı yetkilendirme, dağıtık senkronizasyon, vektör veritabanı, embeddings ve Graphiti ilk sürümün kapsamında değildir.

## Temel yaklaşım

Kalıcı hafıza için doğruluk kaynağı Markdown dosyaları olacaktır. Arama indeksleri, özetler, embeddings veya grafik yapıları ileride eklenirse bunlar yeniden üretilebilir yardımcı katmanlar olmalı; ana kayıt olmamalıdır.

Önerilen bilgi yaşam döngüsü:

1. Agent çalışmaya başlarken proje bağlamını yükler.
2. Çalışma sırasında önemli olaylar session kaydına eklenir.
3. Kalıcı kararlar `DECISIONS.md` gibi yapılandırılmış belgelere terfi ettirilir.
4. Güncel gerçek durum kısa ve düzenli bir state belgesinde tutulur.
5. Agent işi bırakırken handoff ve sıradaki adımları günceller.
6. Sonraki agent aynı kayıtlardan bağlamı yeniden kurar.

Dosya adları iş mantığına derin biçimde gömülmeyecektir. Proje kökü ve mantıksal belge adları yapılandırmadan gelecektir. `PROJECT.md`, `STATE.md`, `ROADMAP.md`, `DECISIONS.md`, `TODO.md` ve `HANDOFF.md` yalnızca önerilen varsayılanlardır.

## 2026-08-10 — Depo analizi ve çalışan taban

### Yapılanlar

- Deponun kaynak kodu, testleri, paket yapılandırması, README'si ve beraberindeki Local REST API OpenAPI belgesi incelendi.
- MCP sunucu entrypoint'i ve araç kayıt mekanizması doğrulandı.
- Obsidian REST istemcisinin okuma, arama, yazma, patch, silme, frontmatter, periyodik not ve yakın değişiklik davranışları incelendi.
- README ile gerçek araç kaydı karşılaştırıldı.
- Kilitli geliştirme ortamı `.venv` içinde kuruldu.
- `uv.lock` değiştirilmeden `uv sync --frozen --all-groups` ile bağımlılıklar kuruldu.
- Birim testleri, kapsam ölçümü ve statik tip denetimi çalıştırıldı.
- Sunucu gerçek stdio JSON-RPC üzerinden başlatılarak `initialize` ve `tools/list` çağrıları doğrulandı.
- Kaynak kodda uyumluluk düzeltmesine ihtiyaç olmadığı belirlendi.

### Doğrulanan taban

- Python: `3.13.13`
- MCP SDK: `1.1.0`
- Proje paketi: `mcp-obsidian 0.2.2`
- Test sonucu: `81 passed`
- Toplam test kapsamı: `%99`
- `obsidian.py` kapsamı: `%100`
- Pyright: `0 errors, 0 warnings`
- MCP protokolü: `2024-11-05`
- stdio initialization: başarılı
- stdio araç listeleme: başarılı
- Kayıtlı araç sayısı: `15`

Canlı bir Obsidian vault entegrasyon testi yapılmadı. Bunun için çalışan Obsidian Local REST API eklentisi ve gerçek API anahtarı gerekir. Mevcut HTTP davranışları mock tabanlı testlerle doğrulanmaktadır.

### Gerçekte kayıtlı Obsidian araçları

1. `obsidian_list_files_in_dir`
2. `obsidian_list_files_in_vault`
3. `obsidian_get_file_contents`
4. `obsidian_simple_search`
5. `obsidian_patch_content`
6. `obsidian_append_content`
7. `obsidian_put_content`
8. `obsidian_delete_file`
9. `obsidian_complex_search`
10. `obsidian_search_by_tag`
11. `obsidian_get_frontmatter`
12. `obsidian_batch_get_file_contents`
13. `obsidian_get_periodic_note`
14. `obsidian_get_recent_periodic_notes`
15. `obsidian_get_recent_changes`

README yalnızca eski araçların bir bölümünü belgeliyor. Özellikle overwrite/put, batch read, complex search, tag search, frontmatter, periodic notes ve recent changes yetenekleri eksik.

## Bu repo bugün bize ne sağlıyor?

Mevcut proje güçlü bir Obsidian I/O tabanı sağlıyor:

- Vault ve dizin listeleme
- Tekli ve toplu Markdown okuma
- Basit metin araması
- JsonLogic tabanlı karmaşık arama
- Etiket ve frontmatter erişimi
- Append, hedefli patch ve tam dosya overwrite
- Onay gerektiren silme
- Periyodik not erişimi
- Dataview üzerinden yakın değişiklik sorgusu
- Claude/Codex gibi MCP istemcilerinin kullanabileceği stdio sunucusu
- UTF-8 ve Windows stdio uyumluluğu
- Güçlü birim testi tabanı

Eksik olan şey, bu düşük seviyeli yetenekleri proje devamlılığına dönüştüren kurallı proje hafızası katmanıdır. Mevcut araçlar bir dosyayı okuyup yazabilir; ancak hangi belgelerin bağlam için önemli olduğunu, agent'ın başlangıçta ne okuması gerektiğini, çalışma sonunda ne bırakması gerektiğini veya çakışmaların nasıl önleneceğini bilmiyor.

## Görünen teknik borç ve riskler

### Yapılandırma

- `OBSIDIAN_API_KEY` modül import edilirken hem `server.py` hem `tools.py` içinde kontrol ediliyor.
- Host, port ve protokol değerleri import zamanında yakalanıyor.
- `OBSIDIAN_PROTOCOL` desteklenmesine rağmen README'de belgelenmiyor.
- HTTPS varsayılan olmasına rağmen SSL doğrulaması varsayılan olarak kapalı.

### Hata modeli

- REST hataları genel `Exception` türüne çevriliyor.
- HTTP durum kodu programatik olarak güvenilir biçimde ayırt edilemiyor.
- Güvenli oluşturma gibi işlemler için `404`, bağlantı hatası ve diğer sunucu hatalarının ayrıştırılması gerekiyor.

### Çalışma modeli

- Senkron `requests` çağrıları async MCP event loop içinde çalışıyor.
- Handler'lar her çağrıda yeni bir Obsidian istemcisi oluşturuyor.
- Mevcut stdio yaklaşımında Claude ve Codex ayrı sunucu süreçleri başlatabilir. Aynı dosyaya eşzamanlı yazarlarsa süreç içi bir kilit yeterli olmaz.

### Doğrulama ve dokümantasyon

- Araç şemalarındaki bazı maksimum ve tür sınırları handler seviyesinde uygulanmıyor.
- Vault yolları için proje kökü sınırı veya traversal koruması bulunmuyor.
- Canlı Obsidian smoke/integration testi yok.
- `obsidian_get_recent_changes` Dataview desteğine bağımlı.
- `/periodic/{period}/recent` endpoint'i depodaki OpenAPI belgesinde görünmüyor ve canlı plugin sürümüyle doğrulanmalı.
- `pyproject.toml` MCP bağımlılığını `mcp>=1.1.0` olarak bırakıyor; kilit dosyası ise `1.1.0` kullanıyor. Kilitli geliştirme tekrarlanabilir, fakat yayımlanmış `uvx` kurulumu ileride denenmemiş daha yeni bir SDK seçebilir.

## Hedef V1 mimarisi

```text
AI Agent
    ↓
MCP Server
    ↓
Project Memory Tools
    ↓
Project Memory Service
    ↓
Existing Obsidian Client
    ↓
Obsidian Local REST API
    ↓
Shared Obsidian Vault
```

Mevcut `obsidian_*` araçları korunacaktır. Yeni `project_*` araçları bunların yanında kayıt edilecektir.

Önerilen küçük modül ayrımı:

- `config.py`: Obsidian bağlantısı, proje kökü ve mantıksal belge eşlemeleri
- `project_memory.py`: yol sınırlandırma, bağlam toplama, checkpoint ve handoff kuralları
- `project_tools.py`: MCP tool şemaları ve sonuç biçimleri
- `obsidian.py`: mevcut REST I/O katmanı; proje kuralları buraya eklenmez

## Gelişim planı

### Aşama 0 — Çalışan taban

Durum: tamamlandı.

- Kilitli bağımlılıklar çalışıyor.
- 81 test geçiyor.
- 15 araç başarıyla kayıt oluyor.
- Gerçek stdio MCP handshake çalışıyor.
- Mevcut Obsidian işlevlerinde kaynak kod değişikliği yapılmadı.

### Aşama 1 — Tek bilgisayarda minimum devamlılık

Amaç: yeni bir agent'ın sıfır konuşma geçmişiyle projeyi anlayabilmesi ve işi başka bir agent'a bırakabilmesi.

Önerilen sıra:

1. Merkezi ve test edilebilir bir ayar nesnesi eklemek.
2. `PROJECT_MEMORY_ROOT` ve yapılandırılabilir mantıksal belge eşlemelerini tanımlamak.
3. HTTP durum kodlarını koruyan küçük bir `ObsidianApiError` türü eklemek.
4. Proje kökünden kaçışı engelleyen vault-relative yol doğrulaması eklemek.
5. `project_create_file_safe` aracını eklemek.
6. Önerilen Markdown yapısını güvenli biçimde kuran `project_init` aracını eklemek.
7. Başlangıç belgelerini tek çağrıda toplayan `project_get_context` aracını eklemek.
8. Çalışma sonu state, handoff ve session kaydı üreten küçük bir `project_checkpoint` akışı eklemek.
9. Claude Code ve Codex için aynı vault/proje kökünü kullanan örnek MCP yapılandırmaları eklemek.
10. Gerçek Obsidian eklentisiyle opt-in smoke test eklemek.

Bu aşamada yalnızca devamlılık döngüsü için gereken araçlar uygulanmalı. Karar, görev, roadmap ve araştırma için ayrı ayrı çok sayıda tool üretmek yerine ilk sürüm mevcut Obsidian araçlarını kullanabilir.

#### Aşama 1 başarı ölçütleri

- Yeni bir agent eski sohbeti görmeden projenin amacını, mevcut durumunu, aktif işi ve sıradaki adımları söyleyebiliyor.
- Claude Code bir handoff bırakıp Codex aynı yerden devam edebiliyor; tersi de geçerli.
- MCP süreci ve bilgisayar yeniden başlatıldıktan sonra bağlam kaybolmuyor.
- Güvenli araçlar proje kökü dışına yazamıyor.
- Var olan bir dosya varsayılan olarak sessizce overwrite edilmiyor.
- Her bağlam parçasının hangi Markdown dosyasından geldiği görülebiliyor.

### Aşama 2 — Aynı bilgisayarda birden çok agent

Amaç: agent'ların sırayla veya sınırlı eşzamanlılıkla güvenli çalışması.

- Her çalışmaya `agent_id`, `session_id`, başlangıç ve bitiş zamanı eklemek.
- Session kayıtlarını append-only tutmak.
- Dosya okuma sonuçlarına içerik hash/revision bilgisi eklemek.
- Güncellemede `expected_revision` kontrolü yaparak eski bağlamla yazmayı reddetmek.
- Çakışmayı sessiz overwrite yerine açık bir conflict sonucu olarak döndürmek.
- Tek ortak MCP servisi ile agent başına ayrı stdio süreçleri seçeneklerini karşılaştırmak.
- Aynı makinedeki süreçler için gerekirse OS seviyesinde advisory lock eklemek.

Dağıtık kilitleme ve ağ üzerinden çok makine senkronizasyonu bu aşamada da kapsam dışı kalabilir.

### Aşama 3 — Uzun dönem insan ve agent işbirliği

Amaç: birden çok insanın ve agent'ın proje hafızasını güvenilir biçimde geliştirebilmesi.

- Belge şemaları ve sürüm/migration yaklaşımı
- Kararların kim, ne zaman ve neden bilgisiyle kaydı
- İnsan tarafından onaylanması gereken kalıcı kararlar
- Git ile vault geçmişi ve geri alma stratejisi
- Agent ve insan katkıları için denetlenebilir olay günlüğü
- Eski/stale görev ve handoff tespiti
- Proje şablonlarının kullanıcı tarafından özelleştirilebilmesi
- Hassas alanlar için daha sonra rol ve izin modeli

### Aşama 4 — İsteğe bağlı semantik hafıza

Bu aşamaya yalnızca Markdown araması ve yapılandırılmış belgeler yetersiz kalırsa geçilmeli.

- Embeddings ve semantik arama
- Yeniden üretilebilir vektör indeksi
- Varlık/ilişki grafiği veya Graphiti değerlendirmesi
- Uzun session geçmişinden otomatik bilgi terfisi
- Kaynak Markdown'a geri bağlantı ve provenance

Semantik katman hiçbir zaman tek doğruluk kaynağı olmamalıdır.

## İlk uygulanacak araçlar için önerilen sözleşmeler

### `project_create_file_safe`

Amaç: proje kökü içinde yeni bir Markdown dosyasını, normal sıralı kullanımda mevcut dosyayı ezmeden oluşturmak.

Önerilen girdi:

```json
{
  "relative_path": "STATE.md",
  "content": "# State\n"
}
```

Kurallar:

- Mutlak, boş, `..` içeren veya proje kökünden kaçabilen yollar reddedilir.
- Dosya zaten varsa hiçbir yazma yapılmaz ve `already_exists` sonucu döner.
- Yalnızca kesin bir `404` sonrasında oluşturma yapılır.
- Bağlantı hatası dosya yokmuş gibi yorumlanmaz.
- Overwrite seçeneği bu güvenli tool'a eklenmez; mevcut tehlikeli işlem açıkça `obsidian_put_content` olarak kalır.

Local REST API atomik create-only işlemi sunmadığı için GET ve PUT arasındaki yarış tamamen önlenemez. V1 bunu dürüstçe belgelemeli. Eşzamanlı agent desteğinde revision kontrolü veya ortak servis/kilit çözümü eklenmelidir.

### `project_get_context`

Amaç: agent başlangıcında gerekli proje belgelerini tek ve deterministik çağrıda toplamak.

Önerilen çıktı bölümleri:

- Proje kimliği ve amacı
- Mevcut durum
- Aktif roadmap bölümü
- Açık görevler
- Son kararlar
- Son handoff
- Yakın session kayıtları
- Her bölüm için kaynak dosya yolu ve okunma zamanı

Bağlam büyüdüğünde sabit öncelik sırası ve açık token/karakter bütçesi kullanılmalı. Sessizce rastgele kesmek yerine hangi belgelerin dışarıda kaldığı raporlanmalıdır.

### `project_checkpoint`

Amaç: agent'ın iş sonunda devamlılık için gerekli minimum bilgiyi bırakması.

Minimum kayıt:

- Tamamlanan işler
- Değiştirilen dosyalar
- Çalıştırılan doğrulamalar ve sonuçları
- Alınan kararlar ve gerekçeleri
- Bilinen sorunlar
- Aktif çalışma ve sıradaki somut adım
- Agent/session kimliği ve zaman damgası

Checkpoint, mevcut durum belgesini güncellerken ayrıntılı çalışma geçmişini ayrı bir append-only session kaydına yazmalıdır.

## Mimari kararlar

### 2026-08-10 — Kullanıcı tarafından onaylanan kararlar

- Her proje ayrı bir Obsidian vault kullanacak.
- Proje hafızası varsayılan olarak vault kökünde yaşayacak; isteğe bağlı bir alt dizin yapılandırılabilecek.
- Claude Code ve Codex ilk sürümde çoğunlukla sırayla çalışacak ve handoff bırakacak.
- Agent teknik kararları kalıcılaştırabilecek; kritik kararlar insan onayı gerektirecek şekilde işaretlenecek.
- `STATE` ve `HANDOFF` güncel görünüm olarak güncellenebilecek; ayrıntılı geçmiş append-only session kayıtlarında korunacak.
- Vault şimdilik Git ile sürümlenmeyecek.
- Bu bilgisayar geliştirme ve mock/birim testleri için kullanılacak. Çalışan sürüm daha sonra Obsidian'ın bulunduğu ana bilgisayara kurulup canlı vault ile doğrulanacak.
- Proje gelişiminin Obsidian içinden izlenebilmesi V1 gereksinimidir. Yapılandırılabilir bir `progress` belgesi runtime proje hafızasının parçası olacak ve ileride checkpoint akışı tarafından güncellenecek.

### Hâlâ açık olan kararlar

1. Proje hafızası Obsidian vault içinde hangi üst dizinde tutulacak?
2. Varsayılan belge seti ne kadar küçük olmalı?
3. Hangi kararların "kritik" kabul edilip insan onayı istemesi gerektiği nasıl belirlenecek?
4. Proje bağlamı için öncelik ve maksimum boyut politikası ne olmalı?

## Uygulama için varsayılan kararlar

- Bir vault tek proje barındırsın ve proje hafızası varsayılan olarak vault kökünde yaşasın.
- `PROJECT_MEMORY_ROOT`, farklı bir düzen isteyen kullanıcılar için isteğe bağlı alt dizin desteği sunsun.
- İlk varsayılan belge seti `PROJECT`, `STATE`, `ROADMAP`, `DECISIONS`, `TODO` ve `HANDOFF` ile sınırlı kalsın.
- Obsidian içinden gelişimi izlemek için mantıksal `progress` belgesi de yapılandırılabilir olsun.
- `STATE` ve `HANDOFF` güncel görünüm olarak değiştirilebilsin; her checkpoint'in ayrıntısı append-only session dosyasında korunsun.
- İlk sürüm agent'ların sırayla çalıştığını varsaysın, fakat veri modeli ileride revision kontrolünü eklemeye engel olmasın.
- Hem mevcut düşük seviyeli `obsidian_*` araçları hem de güvenli/yüksek seviyeli `project_*` araçları birlikte sunulsun.
- Embeddings ve graph katmanı, deterministik Markdown devamlılığı tamamlanmadan eklenmesin.

## Bir sonraki önerilen geliştirme dilimi

İlk kod değişikliği küçük tutulmalıdır:

1. `ProjectMemoryConfig`
2. Typed Obsidian HTTP hatası
3. Proje yolu doğrulama
4. `project_create_file_safe`
5. Birim testleri ve tool registration testi
6. README'ye yeni yapılandırma ve güvenlik sınırlarının eklenmesi

Bu dilim tamamlandıktan sonra canlı Obsidian vault üzerinde create/already-exists/path-rejection senaryoları doğrulanmalı; ardından `project_get_context` tasarımına geçilmelidir.

## 2026-08-10 — İlk project-memory temel dilimi

### Uygulananlar

- Tek proje/tek vault kararını destekleyen `ProjectMemoryConfig` eklendi.
- Vault kökü varsayılan proje kökü yapıldı; `PROJECT_MEMORY_ROOT` isteğe bağlı alt dizin olarak bırakıldı.
- Varsayılan mantıksal belge eşlemelerine Obsidian'dan gelişimi izlemek için `progress: PROGRESS.md` eklendi.
- `PROJECT_MEMORY_DOCUMENTS` JSON ortam değişkeniyle belge yollarını değiştirme desteği eklendi.
- HTTP durum kodu ve Local REST API hata kodunu koruyan `ObsidianApiError` eklendi.
- Mutlak yol, `..`, boş segment, backslash, kontrol karakteri ve percent-encoded yol reddeden proje yolu doğrulaması eklendi.
- Proje hafızası dosyaları `.md` ile sınırlandırıldı.
- Mevcut dosyayı normal sıralı kullanımda overwrite etmeyen `ProjectMemory.create_file_safe` servisi eklendi.
- `project_create_file_safe` MCP aracı kaydedildi.
- README gerçek araç listesi, yeni yapılandırma ve güvenli oluşturmanın yarış sınırlamasıyla güncellendi.
- Mevcut 15 `obsidian_*` aracın kaydı korundu; toplam araç sayısı 16 oldu.

### Doğrulamalar

- Tüm eski testler geçmeye devam ediyor.
- Test sayısı 81'den 114'e çıktı.
- Pyright sonucu: `0 errors, 0 warnings`.
- Toplam kapsam: `%98`.
- Yeni yapılandırma ve Obsidian hata modülleri: `%100` kapsam.
- Canlı Obsidian testi bu geliştirme bilgisayarında yapılmadı; ana bilgisayara kurulum sonrasında çalıştırılacak.

### Bilinen sınır

Local REST API atomik create-only sağlamadığı için iki bağımsız MCP sürecinin GET ve PUT arasında yarışması hâlâ mümkündür. Onaylanan V1 çalışma modeli agent'ların sırayla çalışması ve handoff bırakmasıdır.

### Sıradaki adım

`project_init`, `project_get_context` ve `project_checkpoint` ile devamlılık döngüsünü tamamlamak. Canlı Obsidian kurulumunda ilk smoke test `created`, `already_exists` ve unsafe-path senaryolarını doğrulamalıdır.

## 2026-08-10 — Minimum devamlılık döngüsü

### Uygulananlar

- `project_init`, yapılandırılmış yedi varsayılan Markdown belgesini güvenli create davranışıyla kuracak şekilde eklendi.
- Dosya adları şablonlardan ayrıldı; şablonlar yalnızca mantıksal belge isimlerini kullanıyor.
- `project_get_context`, belgeleri `project → state → handoff → roadmap → todo → decisions → progress` sırasında yükleyecek şekilde eklendi.
- Context çıktısına kaynak yolu, `loaded/missing` durumu, truncation ve bütçe nedeniyle dışarıda kalan belge listesi eklendi.
- Context bütçesi `1–200000` karakter aralığında açıkça doğrulanıyor.
- `project_checkpoint`, ayrıntılı session kaydını önce append-only dosya olarak oluşturacak şekilde eklendi.
- Checkpoint sonrasında `STATE.md` ve `HANDOFF.md` güncel görünüm olarak değiştiriliyor, `PROGRESS.md` ise append ile büyütülüyor.
- Checkpoint içindeki onaylanmış `decisions` kayıtları `DECISIONS.md` dosyasına append ediliyor; `pending_approvals` kalıcı kararlara otomatik olarak terfi ettirilmiyor.
- Kritik kararların otomatik uygulanması yerine `pending_approvals` alanında insan onayına bırakılabilmesi sağlandı.
- Session kimliği çakışırsa güncel belgeler değiştirilmeden açık conflict hatası üretiliyor.
- Gelişmelerin Obsidian içinden izlenmesi için her checkpoint `PROGRESS.md` içine okunabilir bir kayıt ve session bağlantısı ekliyor.

### Doğrulamalar

- Test sayısı `140 passed` seviyesine çıktı.
- Pyright sonucu: `0 errors, 0 warnings`.
- Toplam test kapsamı `%99`; yeni config, template ve project tool modülleri `%100` kapsamda.
- Eski Obsidian araç testleri geçmeye devam ediyor.
- Canlı Obsidian testi ana bilgisayara kurulum sonrasına bırakıldı.
- Mevcut 15 Obsidian aracıyla birlikte toplam MCP araç sayısı 19 oldu.
- Dört `project_*` aracın gerçek stdio `tools/list` yanıtında birlikte kayıtlı olduğu doğrulandı.

### Yazma sırası ve kurtarma davranışı

Checkpoint çok dosyalı atomik transaction değildir. Kurtarılabilirliği artırmak için önce değiştirilmeyen session kaydı oluşturulur; ardından state, handoff ve progress güncellenir. Daha sonraki bir yazma başarısız olursa ayrıntılı session dosyası kurtarma kaydı olarak kalır.

### Sıradaki adım

Ana bilgisayar kurulumu için tekrarlanabilir bir smoke-test kontrol listesi ve örnek Claude Code/Codex MCP yapılandırmaları hazırlamak. Gerçek Obsidian doğrulamasından sonra revision/hash tabanlı stale-write korumasının gerekip gerekmediği değerlendirilecek.

## 2026-08-10 — Canlı Obsidian kabul testi hazırlığı

- `docs/LIVE_OBSIDIAN_SMOKE_TEST.md` eklendi.
- İlk testin gerçek proje vault'u yerine yeni ve boş bir vault üzerinde yapılması zorunlu kılındı.
- Init idempotency, context recovery, safe create, unsafe path reddi, checkpoint etkileri, decision/pending-approval ayrımı, session conflict ve süreç yeniden başlatma senaryoları tanımlandı.
- Test sonucunun hem repo `progress.md` hem de Obsidian `PROGRESS.md` içine kaydedilmesi istendi.
- Gerçek Obsidian çağrıları bu geliştirme bilgisayarında çalıştırılmadı.

## Günlük tutma kuralı

Gelecekte her anlamlı geliştirme diliminde bu dosyaya şu bilgiler eklenmelidir:

- Tarih
- Amaç
- Yapılan değişiklikler
- Alınan kararlar
- Test ve doğrulama sonuçları
- Bilinen sınırlamalar
- Sıradaki adım

Bu dosya geliştirme günlüğüdür; runtime proje hafızasının yerini tutmaz. Runtime hafıza Obsidian vault içindeki yapılandırılmış proje belgelerinde yaşayacaktır.

## 2026-08-10 — Ana bilgisayar ve ortak agent kurulumu hazırlığı

### Uygulananlar

- `docs/MAIN_COMPUTER_SETUP.md` ile Windows ana bilgisayar için kilitli bağımlılık kurulumu, boş test vault'u, istemci doğrulaması ve canlı kabul sırası belgelendi.
- Codex için proje veya kullanıcı kapsamına eklenebilecek `config.toml` örneği oluşturuldu.
- Claude Code için proje kapsamındaki `.mcp.json` örneği oluşturuldu.
- Her iki istemci de kilitli kurulumun oluşturduğu aynı `.venv/Scripts/mcp-obsidian.exe` sunucusunu ve aynı Obsidian Local REST API hedefini kullanacak şekilde yapılandırıldı.
- API anahtarı örnek yapılandırmalara gömülmedi; istemci ortamından aktarılacak şekilde tasarlandı.
- Yerel PowerShell değişkenlerini hazırlamak için `project-memory.env.ps1.example` eklendi; gerçek `.project-memory.env.ps1` dosyası Git ignore listesine alındı.
- `docs/AGENT_MEMORY_PROTOCOL.md` ile oturum başlangıcı, çalışma sırası, kritik kararlar, checkpoint ve handoff kalite ölçütleri tanımlandı.
- README'deki API anahtarı açıklaması yeni güvenli ana bilgisayar akışına yönlendirildi.

### Mimari etkisi

MCP bağlantısı ile agent davranışı birbirinden ayrıldı. Bağlantı şablonları iki istemcinin aynı araçlara ulaşmasını sağlar; devamlılık protokolü ise agent'ların oturum başında bağlamı okumasını ve anlamlı iş sonunda kalıcı checkpoint bırakmasını sağlar. Böylece V1 devamlılığı sinir ağı oturum hafızasına değil, normal Markdown dosyalarına ve açık bir çalışma disiplinine dayanır.

### Güvenlik ve işletim sınırları

- Gerçek API anahtarı repoya yazılmamalıdır.
- PowerShell oturum dosyası yalnız yerelde tutulmalıdır.
- Codex masaüstü uygulamasının ortam değişkenlerini görebilmesi için değişkenler uygulama başlamadan önce erişilebilir olmalıdır.
- V1'de Claude Code ve Codex aynı vault'a eşzamanlı yazmamalıdır; checkpoint tamamlandıktan sonra agent devri yapılmalıdır.

### Doğrulama durumu

- Yapılandırma şablonları resmi Codex MCP ve Claude Code MCP yapılandırma biçimleriyle karşılaştırıldı.
- JSON ve TOML şablonları parser ile doğrulandı; yeni dokümanlardaki yerel bağlantıların hedefleri kontrol edildi.
- Kurulu `.venv/Scripts/mcp-obsidian.exe` sürecine gerçek stdio `initialize` ve `tools/list` mesajları gönderildi; 15 `obsidian_*` ve 4 `project_*` olmak üzere 19 araç görüldü.
- Tüm test paketi yeniden çalıştırıldı: `140 passed`.
- Gerçek ana bilgisayar yolları ve Obsidian API anahtarı bu geliştirme bilgisayarında mevcut olmadığı için canlı istemci bağlantısı henüz çalıştırılmadı.
- Python kaynaklarında değişiklik yapılmadı; son başarılı statik analiz sonucu Pyright `0 errors, 0 warnings`, son kapsam sonucu `%99` olarak korunuyor.

### Sıradaki adım

Ana bilgisayarda kurulum rehberini uygulamak, boş test vault'unda canlı smoke testi tamamlamak ve bir istemcinin yazdığı checkpoint'in diğer istemci tarafından `project_get_context` ile okunabildiğini doğrulamak.

## 2026-08-10 — Canlı test ön kontrolü

### Kontrol sonucu

- Bu geliştirme bilgisayarında `.venv/Scripts/mcp-obsidian.exe` mevcut ve çalıştırılabilir durumda.
- Codex komutu mevcut.
- `OBSIDIAN_API_KEY` tanımlı değil.
- Yerel `.env` veya `.project-memory.env.ps1` bulunmuyor.
- Obsidian Local REST API'nin varsayılan `27124` portunda dinleyen bir servis yok.
- Claude Code ve `uv` bu kabuk ortamının `PATH` listesinde bulunmuyor.

### Sonuç

Gerçek Obsidian vault'una yazan smoke test bu bilgisayarda başlatılmadı. Bu beklenen bir ortam sınırıdır; kullanıcı bu bilgisayarın geliştirme/test, diğer bilgisayarın Obsidian ana bilgisayarı olduğunu daha önce belirtmiştir. Sahte bir canlı başarı kaydı üretilmedi.

### Devam koşulu

Ana bilgisayarda Obsidian, boş test vault'u ve Local REST API eklentisi açıldıktan; repo kurulduktan ve API anahtarı yerel ortamda tanımlandıktan sonra `docs/LIVE_OBSIDIAN_SMOKE_TEST.md` uygulanacaktır.

## 2026-08-10 — Test bilgisayarında gerçek Obsidian kabul testi

### Ortam

- Ana bilgisayarda test yapılamayacağı netleştiği için kabul testi bu geliştirme bilgisayarında ayrı bir test vault'unda çalıştırıldı.
- Test vault'u: `W:/Workspace/Projects/Local/vault/test`
- Vault testten önce Markdown dosyası içermiyordu.
- Obsidian sürümü: `1.13.4`
- Local REST API sürümü: `4.1.7`
- Bağlantı: HTTPS `127.0.0.1:27124`
- API anahtarı yalnız plugin'in yerel `data.json` dosyasından alt süreç belleğine alındı; repo dosyalarına veya komut çıktısına yazılmadı.

### Sürüm kararı

Mevcut 15 Obsidian aracının tamamını koruyan V1 referans sürümü Local REST API `4.1.7` olarak sabitlendi. Upstream 5.x periodic-note REST uçlarını kaldırdığı ve başka API davranışlarını değiştirdiği için 5.x tam uyumluluk ayrı bir gelecek dilimine bırakıldı. V1 kurulumu plugin'i körlemesine yükseltmeyecek.

### İlk canlı turda bulunan hata — duplicate session

`project_checkpoint` açık bir `session_id` alsa bile session dosya adına timestamp ekliyordu. Aynı kimlikle bir saniye sonra yapılan ikinci checkpoint farklı dosya yoluna yazıldığı için conflict oluşmadı ve güncel belgeler ikinci kez değiştirildi.

Düzeltme:

- Açık `session_id` verilirse append-only yol `sessions/<session_id>.md` oldu.
- Otomatik kimliklerde mevcut timestamp+UUID dosya adı korundu.
- Farklı timestamp değerleriyle aynı açık session kimliğinin reddedildiğini doğrulayan regresyon testi eklendi.
- İlk başarısız canlı kayıtlar silinmedi; kanıt olarak test vault'unda bırakıldı.
- Temiz tekrar `PROJECT_MEMORY_ROOT=acceptance-v2` altında yapıldı.

### İkinci canlı turda bulunan hata — recent changes

`obsidian_get_recent_changes`, Local REST API 4.x'te kaldırılmış Dataview DQL Content-Type'ını kullanıyordu ve gerçek API `40012` döndürüyordu.

Düzeltme:

- Tek bir JsonLogic `{"var": "stat.mtime"}` sorgusuyla dosya değişiklik zamanları alındı.
- Gün sınırı filtrelemesi, azalan zaman sıralaması ve limit istemci tarafında deterministik olarak uygulandı.
- Mock testi yeni gerçek API sözleşmesine göre değiştirildi ve canlı çağrı tekrar geçti.

### Üçüncü canlı turda bulunan hata — recent periodic notes

`obsidian_get_recent_periodic_notes`, upstream 4.1.7 route tablosunda bulunmayan `/periodic/:period/recent` endpoint'ini çağırıyordu; gerçek API isteği `40054` ile yanlış route'a düşüyordu.

Düzeltme:

- Local REST API'nin desteklediği `/periodic/<period>/<year>/<month>/<day>/` endpoint'i kullanıldı.
- Günlük, haftalık, aylık, çeyreklik ve yıllık dönem sınırları geriye doğru üretiliyor.
- Bulunan notlar path'e göre tekilleştiriliyor, içerik isteğe göre çıkarılıyor ve limite ulaşınca tarama duruyor.
- Beş dönem türü için sınır üretim testleri eklendi; gerçek daily note ile canlı current/recent çağrıları geçti.

### Canlı araç matrisi sonucu

15 mevcut `obsidian_*` aracın tamamı gerçek vault üzerinde geçti:

- Listeleme: vault ve directory
- Okuma: tek dosya ve batch
- Yazma: append, patch ve put
- Arama: simple, complex ve tag
- Metadata: frontmatter ve recent changes
- Periodic: current ve recent
- Delete: yalnız testin kendi oluşturduğu geçici dosya üzerinde

Dört `project_*` aracın tamamı geçti:

- `project_init`: ilk oluşturma ve ikinci çağrıda idempotency
- `project_get_context`: deterministik sıra, loaded durumu ve restart recovery
- `project_create_file_safe`: create, already-exists ve overwrite koruması
- `project_checkpoint`: state/handoff/progress/decision yazımı, pending approval ayrımı ve duplicate session conflict

Beş unsafe yol gerçek MCP çağrısında reddedildi. MCP süreci kapatılıp yeniden başlatıldıktan sonra state, handoff, decision ve progress bağlamı konuşma geçmişi olmadan vault'tan geri yüklendi.

### Otomatik doğrulama

- Birim/integration test sonucu: `150 passed`.
- Toplam kapsam: `%99`.
- Pyright: `0 errors, 0 warnings`.
- Gerçek stdio MCP süreci: 19 araç kayıtlı.
- `git diff --check`: temiz; yalnız Windows LF/CRLF dönüşüm uyarıları var.

### Sonuç

Tek bilgisayarda kalıcı proje devamlılığı hedefinin teknik kabul testi geçti. Ana bilgisayarda ayrı bir test zorunlu değil; ana bilgisayar kurulum hedefidir. Taşıma öncesinde bu değişiklikler gözden geçirilmeli, commit edilmeli ve `origin` remote'una gönderilmelidir.

## 2026-08-10 — Agent Handoff Demo başlangıcı

### Amaç

Konuşma geçmişine erişimi olmayan yeni bir Codex veya Claude Code oturumunun Obsidian'daki kalıcı proje bağlamından gerçek geliştirmeye devam edebildiğini sınamak.

### Oluşturulan test projesi

- Konum: `examples/agent-handoff-demo`
- Dil: Python 3.11+
- V1 bağımlılık politikası: standard library only
- İlk çalışan komut: `status`
- İlk test: CLI'ın `agent-handoff-demo: ready` çıktısını ve sıfır exit code'u doğruluyor
- Paylaşılan agent talimatları: `AGENTS.md` ve `CLAUDE.md`
- İlk roadmap: `add`, `list`, ardından `complete`, son olarak yeni agent handoff kabulü

### Obsidian proje hafızası

- Test vault içinde `PROJECT_MEMORY_ROOT=agent-handoff-demo` kullanıldı.
- Yedi varsayılan proje belgesi ilk çağrıda oluşturuldu.
- `PROJECT.md`, `ROADMAP.md` ve `TODO.md` demo hedefleriyle dolduruldu.
- `bootstrap-codex` session kaydı append-only olarak oluşturuldu.
- `STATE`, `HANDOFF`, `DECISIONS` ve `PROGRESS` checkpoint ile güncellendi.
- Checkpoint sonrasında yedi context belgesinin tamamı `loaded` olarak geri okundu.
- Sonraki küçük dilim: yeni bir agent taskında context'i yükleyip `add` ve `list` özelliklerini testleriyle uygulamak.

### Yerel Codex yapılandırması

- Demo klasöründe proje-scope `.codex/config.toml` oluşturuldu.
- Dosya bilgisayara özgü mutlak yollar içerdiği için demo `.gitignore` dosyasıyla Git dışında bırakıldı.
- MCP root'u yalnız bu demo için `agent-handoff-demo` olarak ayarlandı.
- Yapılandırma TOML parser ile doğrulandı.
- Gerçek API anahtarı yapılandırmaya yazılmadı. Yeni Codex sürecinden forward edilmeli veya server repo kökündeki Git-ignore `.env` dosyasından yüklenmelidir.

### Doğrulama

- Demo CLI: başarılı.
- Demo unittest: `1 passed`.
- Canlı Obsidian init, checkpoint ve context recovery: başarılı.
- Ana sunucu testleri: `150 passed`.
- Pyright: `0 errors, 0 warnings`.

### Devam koşulu

Yeni Codex taskı açılmadan önce `OBSIDIAN_API_KEY` yeni Codex sürecinin ortamında bulunmalı veya server repo kökünde yalnız yerelde tutulan `.env` dosyasına eklenmelidir. Ardından yeni task çalışma dizini `examples/agent-handoff-demo` seçilmeli ve ilk işlem `project_get_context` olmalıdır.
