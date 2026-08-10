# Agent Memory Protocol — V1

Bu protokol, Claude Code ve Codex'in aynı Obsidian vault'unu sıralı biçimde
ortak proje hafızası olarak kullanması içindir. V1 eşzamanlı yazmayı güvenli
kabul etmez.

## Oturum başlangıcı

1. Doğru projeye ait Obsidian vault'unun açık ve Local REST API eklentisinin
   çalışır olduğunu doğrula.
2. `project_get_context` çağır.
3. Yanıtta `missing`, `truncated` veya `omitted` belgeler varsa bunları açıkça
   değerlendir; eksik bağlamı varmış gibi kabul etme.
4. İlk kurulumsa yalnızca bir kez `project_init` çağır ve ardından tekrar
   `project_get_context` ile oku.
5. Özellikle `STATE`, `HANDOFF`, açık işler, engeller ve bekleyen insan
   onaylarını çalışma planına yansıt.

Agent yalnızca kullanıcının bir sorusunu yanıtlıyor ve proje üzerinde anlamlı
bir çalışma yapmıyorsa checkpoint oluşturmak zorunda değildir.

## Çalışma sırasında

- Mevcut Obsidian I/O araçları kullanılmaya devam edebilir.
- Yeni proje hafızası dosyası oluştururken `obsidian_put_content` yerine
  `project_create_file_safe` tercih edilir.
- `STATE.md` ve `HANDOFF.md` güncel görünüm; `sessions/` kayıtları geçmişin
  değiştirilmeyen kurtarma kaydıdır.
- Agent teknik ve geri alınabilir kararları `decisions` alanına yazabilir.
- Veri kaybı riski, güvenlik, geri döndürülmesi zor mimari değişiklik, önemli
  maliyet veya kullanıcı hedefini değiştiren kararlar `pending_approvals`
  alanına yazılır; onaylanmış karar gibi davranılmaz.
- Claude Code ve Codex aynı anda aynı vault'a yazmamalıdır.

## Anlamlı oturum sonu

İş tamamlandığında veya başka agente devredildiğinde `project_checkpoint`
çağır. En az şu alanlar dürüst ve doğrulanabilir olmalıdır:

- `agent_id`
- `summary`
- `completed`
- `files_changed`
- `verification`
- `decisions`
- `pending_approvals`
- `blockers`
- `next_steps`

Checkpoint başarılı olmadan kullanıcıya bağlamın kalıcılaştırıldığı söylenmez.
Kısmi hata olursa önce oluşturulan `sessions/...md` kaydı kurtarma noktası
olarak incelenir.

## Sonraki agent için minimum handoff kalitesi

Handoff şu soruları tek okumada cevaplamalıdır:

1. Son hedef neydi?
2. Gerçekte ne değişti?
3. Hangi doğrulamalar çalıştırıldı ve sonuç neydi?
4. Bilinen engel veya risk var mı?
5. İnsan onayı bekleyen konu var mı?
6. Sıradaki en küçük somut adım ne?

## Agent talimatına eklenecek kısa metin

Hedef projenin agent talimat dosyasına veya başlangıç prompt'una şu metin
eklenebilir:

> Bu proje kalıcı bağlam için `project-memory` MCP sunucusunu kullanır. Anlamlı
> çalışmaya başlamadan önce `project_get_context` çağır ve sonuçtaki eksik,
> kırpılmış veya dışarıda bırakılmış belgeleri dikkate al. İlk boş vault'ta
> `project_init` kullan. Anlamlı iş veya handoff sonunda
> `project_checkpoint` ile yapılanları, doğrulamaları, dosyaları, engelleri ve
> sıradaki adımı kaydet. Kritik kararları `decisions` içine kesinleşmiş olarak
> yazma; `pending_approvals` ile insan onayına bırak. Aynı vault'a başka bir
> agent yazarken eşzamanlı yazma yapma.
