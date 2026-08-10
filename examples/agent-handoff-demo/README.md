# Agent Handoff Demo

Bu küçük proje, Codex ve Claude Code'un konuşma geçmişini paylaşmadan aynı
Obsidian proje hafızasından sırayla devam edebildiğini sınamak içindir.

Uygulama, görevleri yerel bir JSON dosyasında tutan bağımlılıksız bir Python
CLI'a dönüşecektir. Başlangıç iskeleti yalnız `status` komutunu sağlar; sonraki
agent oturumları roadmap'teki özellikleri küçük dilimler halinde ekleyecektir.

## Çalıştırma

Repo kökünden:

```powershell
.\.venv\Scripts\python.exe examples\agent-handoff-demo\src\agent_handoff_demo\cli.py status
.\.venv\Scripts\python.exe -m unittest discover -s examples\agent-handoff-demo\tests -v
```

Beklenen ilk CLI çıktısı:

```text
agent-handoff-demo: ready
```

## Hafıza sınırı

Bu projenin MCP sunucusu şu değerle başlatılmalıdır:

```text
PROJECT_MEMORY_ROOT=agent-handoff-demo
```

Her anlamlı oturum `project_get_context` ile başlar ve `project_checkpoint` ile
biter. Ayrıntılı kurallar [AGENTS.md](AGENTS.md) içindedir.

## İlk geliştirme sırası

1. `add` ve `list` komutlarını ekle.
2. JSON depolamayı atomik dosya değiştirme ile uygula.
3. `complete` komutunu ekle.
4. Hatalı giriş ve bozuk veri dosyası senaryolarını test et.
5. Codex → Claude Code veya Claude Code → Codex handoff'unu doğrula.

