# Ednaficator PRD: Conversational MCP Orchestrator

**Status**: Runt project → Revival with focused MVP scope  
**Timeline**: 2-3 weeks with AI assistance  
**Target User**: Non-technical family/housemates accessing Sandra's MCP ecosystem  
**Core Value**: Natural language wrapper for 20+ existing MCP servers  

---

## Product Definition

Ednaficator is **not** a standalone AI service. It's a **conversational MCP orchestrator** — an intermediary layer that lets family members talk naturally to the existing MCP infrastructure without needing to understand tool APIs, configuration, or technical details.

### The Problem It Solves

**Today**: Sandra configures everything. Family members can't access it without her.
```
Marion: "Is Benny's camera online?"
Sandra: "I'll SSH into Goliath, load Claude Desktop, 
         check tapo-camera-mcp... it's online."
```

**With Ednaficator**: Family members ask directly.
```
Marion: "Is Benny's camera online?"
Ednaficator: Loads tapo-camera-mcp from Claude Desktop config,
             calls get_camera_status, returns: "Yes, recording"
```

### Design Philosophy

- **Privacy-first**: All processing local (Ollama on 4090)
- **Zero-friction UX**: Single input box, conversational
- **Leverage existing work**: Load MCP registry from Claude Desktop config.json
- **Learn from interactions**: Store context in Advanced Memory MCP
- **Single user, local network**: No auth, no cloud calls

---

## V1 MVP Scope (4 weeks)

### Core Architecture

```
React UI
  ↓ (WebSocket /ws)
FastAPI Server (api_bridge.py) 
  ↓ (stdio)
EdnaCore Orchestrator
  ├→ Claude Desktop config.json (MCP registry)
  ├→ Ollama (local LLM inference)
  ├→ 20+ MCP Servers (stdio)
  └→ Advanced Memory MCP (persistent context)
```

### Backend Components (Status)

| Component | Status | Purpose |
|-----------|--------|---------|
| `api_bridge.py` | ✅ Exists (346 lines) | FastAPI + WebSocket server |
| `EdnaCore` | 🆕 Build | LLM orchestrator, tool calling |
| `MCP Loader` | 🆕 Build | Parse config.json, discover tools |
| `Tool Executor` | 🆕 Build | Call MCPs via stdio |
| `Memory Bridge` | 🆕 Build | Interface with Advanced Memory MCP |
| `Vienna Context` | 🆕 Build | Weather, transit, holidays, districts |

### V1 MCP Servers (Integrated)

**Already Available** (load from Claude Desktop config):
- `tapo-camera-mcp` - Camera status, recording
- `homecontrol-mcp` - Smart home automation
- `local-llm-mcp` - LLM inference fallback
- `advanced-memory-mcp` - Context/memory storage
- **`email-mcp` (minimail-mcp)** - Send/receive email ✨ **NEW**
- + 15+ others from your existing MCP ecosystem

**email-mcp Capabilities** (from minimail-mcp):
- **Send emails** via Gmail SMTP, SendGrid, Mailgun, Resend, or local test services (MailHog, Mailpit)
- **Check inbox** via IMAP or transactional service APIs
- **Test connections** to verify configured services working
- **Dynamic configuration** at runtime (add/switch services without restart)

---

## Real Functionality Examples

### Example 1: Holiday Email Reminder
```
User: "Remind Marion about Benny's vaccination appointment"

EdnaCore executes:
  1. Loads email-mcp from config.json
  2. LLM generates: {"tool": "email-mcp", "action": "send_email",
                     "args": {"to": "marion@example.com",
                              "subject": "Benny's Vet Appointment",
                              "body": "Benny needs vaccination on Feb 15"}}
  3. email-mcp sends via configured Gmail SMTP
  4. Stores in Advanced Memory: "Sent appointment reminder to Marion"

Response: "Sent vaccination reminder to Marion's email."
```

### Example 2: Going on Holiday
```
User: "I'm going on vacation, secure the house"

EdnaCore executes:
  1. Loads homecontrol-mcp + tapo-camera-mcp
  2. LLM chains:
     - Set homecontrol to "vacation mode" (locks, alarms)
     - Enable tapo-camera recording
     - Send Marion email with access codes via email-mcp
     - Store "Holiday mode active" in memory with return date
  3. All via existing MCPs + email-mcp

Response: "House secured. Cameras recording. Access email sent to Marion."
```

### Example 3: Status Check
```
User: "Is everything okay?"

EdnaCore executes:
  1. Loads homecontrol-mcp + tapo-camera-mcp + other monitoring MCPs
  2. Queries all systems: cameras online? doors locked? temps normal?
  3. Pulls memory: any active alerts from last check?
  4. Sends optional email notification if issues found

Response: "All systems normal. Cameras online, doors locked, temps stable."
```

### Example 4: Vienna Context
```
User: "Can we go to the beach tomorrow?"

EdnaCore executes:
  1. Checks OpenWeatherMap API (free tier, no auth)
  2. Checks hardcoded Austrian holiday calendar
  3. Checks memory for beach preferences
  4. May send email confirmation to family via email-mcp

Response: "Weather looks good tomorrow (18°C, sunny). 
          No holidays blocking travel."
```

### Example 5: Send Family Update
```
User: "Tell everyone I arrived in Tokyo safely"

EdnaCore executes:
  1. Loads email-mcp (minimail-mcp with Gmail configured)
  2. LLM generates emails to: Steve, Marion, family distribution list
  3. Sends via email-mcp using configured Gmail SMTP account
  4. Stores in Advanced Memory with "Tokyo arrival" tag

Response: "Sent arrival notification to Steve, Marion, and family."
```

### Example 6: Multiple Recipients with Personalization
```
User: "Email Steve and Marion about Benny's new training routine"

EdnaCore executes:
  1. Queries Advanced Memory for their preferences (Steve: technical details, Marion: simple summary)
  2. LLM generates two personalized emails
  3. email-mcp sends both via Gmail
  4. Stores template in memory for reuse

Response: "Sent personalized emails to Steve and Marion."
```

---

## Technical Architecture

### Data Flow: "Check Benny's camera"

1. **React UI** → WebSocket: `{"message": "Is Benny camera online?"}`
2. **api_bridge.py** receives, passes to EdnaCore
3. **EdnaCore**:
   - Loads Claude Desktop config.json
   - Extracts tapo-camera-mcp tools
   - Creates LLM context: "Available tools: [tapo-camera-mcp tools list]"
   - Calls Ollama with prompt + context
4. **Ollama** (local inference on 4090):
   - Generates: `{"tool": "tapo-camera-mcp", "action": "get_camera_status", "args": {"name": "benny-cam"}}`
5. **Tool Executor** calls tapo-camera-mcp via stdio
6. **tapo-camera-mcp** returns: `{"online": true, "recording": true, "battery": 95}`
7. **EdnaCore** formats response: "Benny's camera is online and recording (battery 95%)"
8. **Advanced Memory MCP** stores: `[tapo-camera, status-check, online, timestamp]`
9. **api_bridge.py** → WebSocket → **React UI** displays response

### Data Flow: "Send reminder email to Marion"

1. **React UI** → WebSocket: `{"message": "Remind Marion about Benny's vet appointment"}`
2. **api_bridge.py** → **EdnaCore**
3. **EdnaCore**:
   - Loads email-mcp from config.json
   - Creates LLM context with email-mcp tools (send_email, check_inbox, etc.)
   - Calls Ollama
4. **Ollama** generates:
   ```json
   {
     "tool": "email-mcp",
     "action": "send_email",
     "args": {
       "to": "marion@example.com",
       "subject": "Reminder: Benny's Vet Appointment",
       "body": "Hi Marion,\n\nBenny has a vet appointment coming up. Please mark your calendar.\n\nBest,\nSandra"
     }
   }
   ```
5. **Tool Executor** calls email-mcp via stdio
6. **email-mcp** (minimail-mcp) uses configured Gmail SMTP to send
7. Returns: `{"status": "sent", "message_id": "...", "recipient": "marion@example.com"}`
8. **Advanced Memory MCP** stores: `[email-mcp, reminder, marion, vet-appointment, 2026-02-02]`
9. **EdnaCore** formats: "Reminder email sent to Marion"
10. **api_bridge.py** → WebSocket → **React UI** displays confirmation

### Prompt Template (EdnaCore)

```python
SYSTEM_PROMPT = """You are Ednaficator, an MCP orchestrator for a home automation + 
personal assistant system. You have access to these MCP tools:

{available_tools}

When the user asks something:
1. Identify which tool(s) can help
2. Generate a tool call in this format:
   {{"tool": "service-name", "action": "method_name", "args": {{...}}}}
3. Return the result in natural language

Vienna Context (when relevant):
- Current timezone: Europe/Vienna (UTC+1/+2)
- Districts: 1-9 Bezirke (user in 9th)
- Holidays: {austrian_holidays_this_month}
- Weather: {current_forecast}

Memory context from previous interactions:
{memory_context}

Always be concise. Prefer action over explanation."""
```

---

## V1 Out of Scope (Explicitly)

❌ Austrian government APIs (Wien.gv.at, ÖBB, FinanzOnline)  
❌ OAuth/credential management (use stored config only)  
❌ Advanced UI features (minimal React, focus backend)  
❌ Multi-user support (single user, local network)  
❌ Mobile app / Voice I/O  
❌ Calendar automation (email notifications yes, calendar integration no)  
❌ Slack/Discord bot integrations (email-mcp supports them but not orchestrated yet)  

---

## Implementation Roadmap

### Week 1: Core Infrastructure
- [ ] Finalize api_bridge.py (WebSocket, error handling)
- [ ] Build MCP Loader (parse config.json, extract tool lists)
- [ ] Build Tool Executor (stdio communication with MCPs)
- [ ] Create EdnaCore orchestrator skeleton
- **Deliverable**: Can load MCPs and discover tools

### Week 2: LLM Integration & email-mcp
- [ ] Integrate Ollama (inference, latency tuning)
- [ ] Implement tool calling (parse LLM output → MCP calls)
- [ ] Build prompt templates + few-shot examples
- [ ] Error handling + fallback strategies
- [ ] **Test email-mcp integration** (send, check inbox, test connection)
- [ ] Integration: email-mcp into EdnaCore workflow
- **Deliverable**: Can orchestrate email tasks + other MCPs successfully

### Week 3: Memory & Context
- [ ] Build Memory Bridge (Advanced Memory MCP interface)
- [ ] Vienna context provider (weather, holidays, districts)
- [ ] Conversation history storage
- [ ] Minimal React UI (input box, message stream)
- **Deliverable**: Functional end-to-end flow

### Week 4: Testing & Polish
- [ ] Integration tests (20 test queries including email scenarios)
- [ ] Latency profiling (target: <2s per query)
- [ ] Error recovery testing
- [ ] GitHub CI/CD setup
- [ ] Deployment docs
- **Deliverable**: Production-ready MVP

---

## Success Metrics

| Metric | Target | Notes |
|--------|--------|-------|
| Functional Accuracy | 80%+ | 16/20 test queries succeed |
| LLM Latency | <2s | Ollama on 4090 |
| Tool Success Rate | 90%+ | MCPs execute correctly |
| Email Reliability | 95%+ | email-mcp delivers consistently |
| Memory Integration | ✅ | Can read/write/search context |
| Offline Capability | 100% | Zero cloud calls |

---

## Technical Decisions & Rationale

| Decision | Why | Trade-off |
|----------|-----|-----------|
| **FastAPI** | Already started, async-native, WebSocket built-in | Must maintain api_bridge.py |
| **Ollama** | Free, local (4090), privacy, no cloud | Limited model choice (mitigated by local-llm-mcp fallback) |
| **Advanced Memory MCP** | Already built, natural integration | Dependency on external MCP |
| **email-mcp (minimail-mcp)** | Pre-built, multi-service, FastMCP 2.14.3 compliant, zero dev cost | Already production-ready in D:\Dev\repos\email-mcp |
| **Claude Desktop config.json** | Single source of truth for MCP registry | Couples to Claude Desktop (acceptable for MVP) |
| **Minimal React** | Reduce scope, focus backend | No fancy UI (acceptable for non-tech users) |
| **No auth V1** | Single-user, local network | Not suitable for shared servers (acceptable for family LAN) |
| **GTFS over ÖBB API** | Free, no credentials needed | Limited real-time accuracy (acceptable for MVP) |

---

## Known Limitations

- **No personalization yet**: Memory exists but no learning loop (V2 feature)
- **Single LLM model**: Can't switch models on the fly (Ollama requirement)
- **No tool confidence**: Can't score "should I try this?" (basic pass/fail only)
- **Limited error recovery**: Tells user instead of trying alternatives
- **No rate limiting**: Assumes single user, trusted local network
- **Ollama-only**: No cloud LLM fallback (acceptable with Goliath's 4090)

---

## Dependencies

```
fastapi==0.104.1
uvicorn==0.24.0
websockets==12.0
pydantic==2.5.0
requests==2.31.0
python-dotenv==1.0.0
sqlite3 (stdlib)
aiohttp==3.9.1

MCP Integration via stdio (no Python SDK needed yet)
Ollama (local, not pip)
Advanced Memory MCP (existing, via config.json)
email-mcp / minimail-mcp (existing at D:\Dev\repos\email-mcp)
```

---

## Q&A: Addressing Concerns

**Q: Will this work with all 20+ MCPs?**  
A: Yes, if they follow the MCP spec (stdio communication). Your MCPs do.

**Q: Why Ollama vs Claude API?**  
A: Cost (€0 vs €2-5/day), privacy (local), latency (<500ms on 4090 vs 3-5s API). For non-critical tasks, local is superior.

**Q: Does email-mcp really work?**  
A: Yes. minimail-mcp is production-ready, tested, supports Gmail SMTP, SendGrid, Mailgun, Resend, plus MailHog/Mailpit for testing. Already packaged in D:\Dev\repos\email-mcp with .mcpb file ready for Claude Desktop.

**Q: Can it send emails to multiple people?**  
A: Yes. email-mcp's send_email action supports CC/BCC. EdnaCore can generate multiple send_email calls in sequence for bulk sends. Memory stores recipients for future reference.

**Q: How does it learn over time?**  
A: Advanced Memory MCP stores interactions with tags. EdnaCore reads memory context in prompts. V2 will add active learning (refine based on feedback).

**Q: What if Ollama crashes?**  
A: Graceful fallback to local-llm-mcp (if configured). V2 can add Claude API fallback.

**Q: How long until usable?**  
A: 2 weeks to functional MVP with AI assistance (assuming focused scope). 3-4 weeks to polish + documentation.

**Q: Can I run this on my iPad in Tokyo?**  
A: Yes. api_bridge.py runs on Goliath in Vienna. React UI connects via RustDesk reverse tunnel. All processing happens on 4090.

---

## Deployment

### Local Development
```bash
cd D:\Dev\repos\ednaficator
pip install -r requirements.txt

# Terminal 1: FastAPI server
python api_bridge.py
# → Listening on http://localhost:8000

# Terminal 2: React dev server (if building UI)
cd ui
npm start
# → http://localhost:3000

# Terminal 3: Ollama (if not already running)
ollama serve
```

### Production (Goliath)
```bash
# Setup systemd service to auto-start api_bridge.py
# Configure Claude Desktop config.json with all MCPs
# React UI deployed to simple HTTP server (nginx/python)
```

---

## Next Steps

1. **Approve scope** - Is this the right MVP?
2. **Build Week 1** - MCP loader + orchestrator skeleton
3. **Test Week 2** - Can we call email-mcp successfully?
4. **Iterate** - Adjust based on real latency/reliability

**Decision point after Week 1**: Kill, mothball, or continue based on actual progress.
