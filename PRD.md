# Ednaficator PRD — Edna Media Concierge (v1)

**Status:** Decided 2026-07-20 · supersedes `docs/archive/PRD-2025-orchestrator.md`
**Owner:** Sandra · **Target:** first real user (Auntie Edna) within ~1 week
**Build recipe:** `RECIPE-EDNA-V1.md` (opencode + DS4)

---

## The product in one sentence

Auntie Edna sends a message — typed or spoken, in dialect — like *"i wüll den Rex
schauen, den mit dem Zug"*, and thirty seconds later the right Kommissar Rex episode is
playing **on her television**.

## What it is NOT

- Not a chatbot. Not "an AI". Edna never learns the words fleet, MCP, model, or token.
- Not a voice assistant competing with ChatGPT/Gemini voice — they won that. We do the
  one thing they structurally cannot: play Sandra's Plex library on Edna's TV.
- Not a general fleet front-end (that was the 2025 PRD; archived). One domain: media.

## Why this is worth building (the litmus test)

A weekly task a named real user wants, that no commodity assistant can do:
watch Kommissar Rex / Agatha Christie adaptations, hear 70s Austropop — from Sandra's
curated Plex library, on Edna's own screen, requested in natural Austrian German.
The LLM earns its keep on exactly two hard-for-menus problems:

1. **Fuzzy resolution:** "den mit dem Hund" → Kommissar Rex; "die alte Dame, die
   strickt" → Miss Marple (Hickson); "spü mir an Ambros" → artist playlist.
2. **One friendly follow-up** when several matches exist — tappable buttons, not prose.

Side effect, by design: every successful request teaches Edna that you can just *tell*
computers things now. The concierge is the AI-literacy curriculum. No teaching software.

## Users

- **Edna (consumer):** non-technical, has Telegram (or gets it installed once, by
  Sandra, in person). Owns a TV with a Plex-capable device.
- **Sandra (admin):** curates the library, provisions users (Telegram ID allowlist),
  sees logs, fixes things. There is no self-service anything.

## v1 scope — three tools, one bot

| Tool | Behavior |
|---|---|
| `resolve_and_play(query, client)` | fuzzy NL → Plex item → playback on the user's named Plex client. **This is the product.** |
| `browse(query)` | "was hast du mit Poirot?" → short list (≤5), as buttons |
| `play_music(query, client)` | artist / era / mood → Plex music playback (Austropop first) |
| `photo_slideshow(query, client)` | v1.1 — person + scene + season → Immich search → generated slideshow (with music) played via Plex. See below. |

## Photo slideshows (v1.1 — specced now, ships right after the media loop)

Edna's queries: *"Hochzeitsfotos"*, *"mitm Onkel Franz beim Aussichtsturm im Winter"*.
Two difficulty tiers, one honest architecture decision:

- **Plex Photos is a dead end** — long-neglected, no face recognition, no semantic
  search. Do not build on it.
- **Immich** (Docker on Goliath, GPU ML) is the index: face recognition (Sandra labels
  Onkel Franz & co. ONCE — Immich clusters faces, labeling is minutes per person),
  CLIP smart search for scenes ("lookout tower", "snow"), EXIF date filters for
  seasons/events. REST API for all of it.
- **Query decomposition is the LLM's job:** person names (validated against the
  labeled-people list) + scene description **translated to English** by the LLM before
  hitting CLIP (default CLIP models are English-strong; LLM translation beats swapping
  in a weaker multilingual model) + season → EXIF month filter (Winter = Dez–Feb)
  combined with the visual query.
- **Display trick — reuse the pipe that already works:** top ~40 hits → ffmpeg
  slideshow MP4 (crossfade, optional Austropop bed) → dropped into a Plex
  "Diashows" library → played on her TV via the exact same `play()` path as Rex.
  No new TV client tech, no casting stack. Generation takes ~30–60 s: the bot says
  "Ich stell dir die Fotos zusammen, einen Moment…" — acceptable, even charming.
- **Honest caveats:** result quality is capped by the archive's labeling (unlabeled
  Franz = invisible Franz); CLIP will occasionally include a wrong-but-similar photo —
  for a family slideshow that's a giggle, not a bug; "beim Aussichtsturm" as a *named
  place* only works if geotags exist or Sandra makes an album — CLIP finds "a lookout
  tower", not "the one in Kahlenberg" specifically.

**Front-end:** Telegram bot. Voice notes → faster-whisper transcription server-side →
same text path (voice input for free; no audio pipeline, no TTS — the TV starting IS
the response). Per-user config maps Telegram ID → Plex client name + language.

**Backend:** existing FastAPI process on Goliath, LM Studio/Ollama local model for
tool-calling (qwen2.5:27b-class), plexapi against local Plex (localhost:32400).

**Auth:** Telegram user-ID allowlist, provisioned by Sandra. Nothing else in v1.

## Content prerequisite (not code, highest leverage)

The product is the library. Before any demo: Kommissar Rex seasons complete; Christie
adaptations (Suchet Poirot, Hickson Marple, key films); Austropop section (Ambros,
Fendrich, Danzer, STS, EAV, …) with artist metadata clean enough to match against.

## Known risk #1: Plex remote-play flakiness

"Play on client" reliability varies by client type (sleep states, registration, app
versions). **Test against Edna's actual TV device before promising anything.**
Mitigation ladder: (1) her TV's Plex app → (2) dedicated €30 streaming stick configured
once → (3) Chromecast via `catt`. Pick the rung that works and never look back.

## Failure UX (German, plain, no jargon)

- TV unreachable → "Schalt bitte den Fernseher ein und schick's nochmal."
- No match → "Das hab ich nicht gefunden. Meinst du vielleicht …?" (buttons)
- Backend down → Sandra is alerted (health check + Dispatch smoke test) before Edna asks.

## v1.2 — Schipal-Chronik (family memory, the learnbot cross-connect)

The third undupeable capability: *"erzähl mir vom Onkel Franz"*. ChatGPT has never
heard of the guy; a curated family corpus has. Design decisions (argued 2026-07-20):

- **The corpus is a thing, not a vibe.** "The fleet collectively knows" is aspiration,
  not architecture — knowledge scattered across memory servers isn't queryable family
  history. Build ONE corpus: a `schipal-chronik` repo of markdown pages (one per
  person, one per event/place), photos referenced by Immich asset IDs, provenance
  line on every claim (*who* told it, *when*, certainty). Embedding index over it.
- **Consumers, plural:** Ednaficator (RAG tool in the bot, direct file/index access in
  the hot path), learnbot-mcp (quizzes/structured sessions for grandkids, later),
  Sandra's Claude via a thin chronik-MCP wrapper. Same corpus, three doors.
- **The capture loop is the killer feature:** Edna is not just the consumer, she is
  the prime SOURCE. When the bot hits a gap it says "Das weiß ich noch nicht — erzähl
  du mir vom Franz!" → her voice-note story → whisper transcript → **Sandra-reviewed
  intake queue** → chronik page. Oral-history capture disguised as a chat. Nobody
  else's product can do this because nobody else's product is family.
- **HARD RULE — review gate:** nothing enters the chronik without Sandra approving it.
  The bot answers ONLY from the corpus and admits gaps; a model that improvises
  family history ("Franz war doch 1962 in Graz…") is poison — worse than no feature.
- **Ingestion is curation, not code** (est. code: ~1 day for intake queue + RAG tool;
  est. curation: ongoing forever). Sources: Edna's stories, Steve's & Marion's
  contributions via Telegram-forward-to-intake, scanned letters/documents (OCR),
  photo metadata. Start with 5 person pages, not a genealogy database.
- **Bridge to slideshows:** chronik answers end with "Soll ich dir Fotos vom Franz
  zeigen?" → `photo_slideshow`. Talking about him and seeing him is the product.
- **50-year design principle (2026-07-20 — the admin is also a future user):** the
  corpus must outlive the bot, the fleet, and Goliath. Plain markdown + JPEG + SQLite,
  readable in 2076 with no running service; the repo itself is the heirloom, the bot
  is merely its current reader. Corollary: the chronik captures Sandra's generation
  too, starting NOW while memory is firsthand — the Lara page (dog, 1975) gets
  written by Sandra in 2026 with provenance "firsthand", not reconstructed in 2036.

## Explicitly deferred

Books/audiobooks via Calibre (v1.2) · Wienerlinien/weather tools (only if Edna
asks) · web PWA · custom voice pipeline (STT/TTS spec of 2026-07-19 stays on the
shelf as `ednaficator-spec.md`) · multi-tenant anything · mcpb packaging (this is a
bot + service, not an MCP server).

## Success criteria

Edna plays something **without calling Sandra**, at least weekly, four weeks running.
That's it. Everything else is vanity.
