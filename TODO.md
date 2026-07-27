# Ednaficator — TODO

**Date:** 2026-07-20 · Ordered. Item 0 gates everything else.

## 0. DECIDE THE TRACK (Sandra, ~1 evening of thought, not code)

- [ ] Pick A (sunset) / B (fleet front-door) / C (voice concierge) — see STATUS.md
- [ ] Litmus test for the decision: name ONE relative and ONE task they would do
      **weekly** that ChatGPT/Gemini cannot do for them. If no answer exists → Track A
      with a clear conscience. If the answer involves camera/Plex/transit/home → Track B.
      Track C only if voice is essential to that same weekly task.

## RECOMMENDED V1 (2026-07-20): "Edna Media Concierge" — Track B, media-first

The litmus test has an answer: Edna, weekly, wants Kommissar Rex / Christie
adaptations / 70s Austropop — and ChatGPT cannot play them on her TV. Scope:

- [ ] Content first (Sandra, no code): Plex libraries curated — Kommissar Rex complete,
      Christie adaptations (Suchet Poirot, Hickson Marple, films), Austropop section
      (Ambros, Fendrich, Danzer, STS, EAV...). If it's not in the library, no AI saves it
- [x] Tool 1: `plex_resolve_and_play(query, client)` — fuzzy NL → library item →
      playback on HER named Plex client ("Wohnzimmer TV"). The whole product is this tool
      — deterministic (rapidfuzz) impl in `ednaficator/concierge/`, exposed at
      `/api/concierge/resolve_and_play`; **not yet verified against live Plex or Edna's TV**
- [x] Tool 2: `plex_browse(query)` — "was hast du mit Poirot?" → short list — impl +
      `/api/concierge/browse`, same live-verification caveat
- [x] Tool 3: music by mood/artist/era → Plex playlist play — impl + `/api/concierge/play_music`
- [ ] Front-end v1: Telegram bot. Voice notes → faster-whisper → text (voice input for
      free, no audio pipeline built). Ambiguous matches → inline buttons, tap to play
- [ ] Test "play on client" against Edna's ACTUAL TV device before promising anything —
      Plex remote-control is historically flaky per client type; fallback: Chromecast
      via catt, or a cheap dedicated Fire/Google TV stick configured once
- [x] Failure copy in German, e.g. TV off → "Schalt bitte den Fernseher ein und
      schick's nochmal" — wired into `PlexConcierge` for unreachable server/client
- [ ] Est: 2–3 days + content curation. Books/audiobooks (Calibre) deferred to v1.1

### Track B first slice — done this session (2026-07-28)

- [x] `ednaficator/concierge/plex_tools.py` — deterministic plexapi layer (resolve_media,
      resolve_music, play, list_clients, get_server), rapidfuzz matching, umlaut-normalizing
- [x] `ednaficator/concierge/tools.py` — `PlexConcierge` class mapping the three PRD verbs
      onto plex_tools; auto-plays on confident single match (score ≥90, ≥15pt margin over
      runner-up), else returns `choices` (never guesses)
- [x] `plexapi`, `rapidfuzz` added as deps (`uv add`)
- [x] `Settings` (api_bridge.py) gained `mode` (orchestrator|concierge), `plex_url`,
      `plex_token` (redacted in `/api/settings` responses), `plex_default_client`;
      mirrored in `.env.example` as `EDNA_MODE` / `EDNA_PLEX_*`
- [x] REST routes: `/api/concierge/{status,clients,resolve_and_play,browse,play_music}`
      in `api_bridge.py` — additive, always mounted regardless of `EDNA_MODE`
- [x] Tests: `tests/test_plex_tools.py` (unit + `@pytest.mark.plex_live`, auto-skips
      without `EDNA_PLEX_TOKEN`), `tests/test_concierge_tools.py` (16 tests, plex_tools
      mocked — auto-play threshold, ambiguous choices, failure copy)
- [ ] **Not done yet**: chat-path integration (EdnaCore doesn't route to concierge tools
      even when `EDNA_MODE=concierge` — routes are REST-only for now); Telegram bot;
      live Plex verification (no server reachable from this session)

## If Track B — fleet front-door (est. 3–5 AI-assisted days)

- [ ] Diff & collapse `api_bridge*.py` → one file; delete the other two
- [ ] **Delete** `ednaficator/nlp/` entirely — replace intent detection with native
      tool-calling on the LLM (qwen2.5:27b / Mistral Small both handle it)
- [ ] **Delete** custom memory engine + `edna_memory/*.json` → per-user SQLite or
      advanced-memory MCP bridge (pick one, not both)
- [ ] Curate tool whitelist per-tool, not per-server (tapo-camera, plex, mywienerlinien,
      weather, reminders). Partial: `EDNA_MCP_ALLOWLIST` filters by server name today
- [ ] Confirmation turn for side-effectful tools; results rendered from tool output,
      never from model prose
- [ ] Reachability: Cloudflare Tunnel + magic-link auth (spec §2.7) — replaces
      "LAN-only, no auth" from PRD, which excluded the actual users (they don't live here)
- [ ] Front-end decision: keep React UI vs Telegram bot (meets family in an app they
      already have; voice notes → whisper transcription = voice input nearly free)
- [ ] Onboard relative #1 in person; watch silently; log everything they say that fails
- [ ] Retire stale ASSESSMENT.md files to `docs/archive/`

## If Track C — additionally (est. +5–7 days, see ednaficator-spec.md)

- [ ] Phases 1–4 of the 2026-07-19 spec (voice loop, server memory, hardening)
- [ ] Re-validate VRAM budget against whatever LLM Track B settled on

## If Track A — sunset (half a day)

- [ ] Final commit, tag `v2.0.0-archive`, push to GitHub, archive repo
- [ ] Write 10-line post-mortem in mcp-central-docs (what the fleet learned from it)
- [ ] Set relatives up with a commodity assistant + 1 laminated cheat sheet each

## v1.2 seed — Schipal-Chronik (parallel, mostly curation)

### TAPE DIGITIZATION — high priority, no longer acute

- [x] Tapes already out of the attic → stored in a room in the flat (were in the
      attic for years; attic-era damage, if any, is done — room storage slows further
      chemistry but doesn't reverse it; vinegar syndrome, if started, still creeps)
- [ ] This year, not someday: identify tape base per reel (acetate vs polyester/PVC —
      60s BASF/AGFA are mixed); baking is for sticky-shed polyester ONLY, never acetate
- [ ] No playback attempts on unserviced machines — first playback = capture pass. Pro transfer studio for the irreplaceable reels
      (Vienna has specialists; Österreichische Mediathek / ÖAW Phonogrammarchiv publish
      guidance); DIY only with a properly serviced deck (Revox/Uher class)
- [ ] Masters: flat transfer, 24-bit/96 kHz WAV, checksums, 3-2-1 backup incl. offsite;
      restoration (denoise) on COPIES only, never the master
- [ ] Post-capture: whisper transcript + diarization → chronik intake (1960s voices of
      Sandra/Steve/Marion + parents); clips become slideshow audio beds

- [ ] Create `schipal-chronik` repo: `people/`, `events/`, `places/`, `intake/`;
      page template with provenance frontmatter (source, told_by, date, certainty)
- [ ] Write the first 5 person pages by hand (Onkel Franz first) — before ANY code
- [ ] Interview Edna informally; also ping Steve & Marion for material
- [ ] Later (post v1.1): intake queue (Telegram forwards + voice-note transcripts →
      Sandra review → merge), embedding index, `family_chat` RAG tool in the bot,
      thin chronik-MCP for Claude Desktop / learnbot consumption
- [ ] Rule enforced in prompt AND code: corpus-only answers, gaps become capture
      prompts ("erzähl du mir!"), never improvised family facts

## Literacy angle ("teach Edna to vibecode") — parallel, mostly NOT code

- [ ] Draft "KI-Führerschein für die Familie": 5 sessions — (1) asking well,
      (2) checking answers / hallucinations, (3) making things (vibecoding-lite:
      invitations, lists, little pages via Claude/ChatGPT artifacts),
      (4) scam & deepfake defense (voice-clone calls!), (5) when NOT to trust it
- [ ] Deliver via shared Claude Project / plain sessions first. Build zero software
      for this until two relatives have completed it and asked for more

## Hygiene (any track)

- [ ] Push repo to github.com/sandraschi/ednaficator (currently local-only per REVIVE)
- [ ] `git rm` the three-variant files once collapsed; commit debris cleanup separately
