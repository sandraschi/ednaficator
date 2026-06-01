# 🤖 Ednaficator - Your Private Austrian AI Concierge

<p align="center">
  <a href="https://github.com/casey/just"><img src="https://img.shields.io/badge/just-ready_to_go-7c5cfc?style=flat-square&logo=just&logoColor=white" alt="Just"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/PrefectHQ/fastmcp"><img src="https://img.shields.io/badge/FastMCP-3.2-7c5cfc?style=flat-square" alt="FastMCP"></a>
</p>


> 📖 **[Installation Guide](INSTALL.md)** — quick start, manual setup, and troubleshooting

**The AI assistant that actually remembers you and keeps your data in Austria**

## Quick Start

```powershell
git clone https://github.com/sandraschi/ednaficator
cd ednaficator
just
```

This opens an interactive dashboard showing all available commands. Run `just bootstrap` to install dependencies, then `just serve` or `just dev` to start.

### Manual Setup

If you don't have `just` installed:

## 🎯 Vision

Ednaficator is the **Austrian answer to big tech AI assistants** - providing intelligent automation and assistance while keeping your data local and private. Built on top of a powerful MCP (Model Context Protocol) ecosystem, Edna orchestrates your digital life without surveillance.

## 🏆 Key Differentiators

- ✅ **True Memory**: Remembers conversations and learns your preferences locally
- ✅ **MCP Orchestration**: Controls 20+ specialized MCP servers for real capabilities  
- ✅ **Austrian Privacy**: All processing stays local, GDPR-compliant by design
- ✅ **Local LLM**: No cloud dependencies, works during outages
- ✅ **Natural Language**: Talk to your entire digital ecosystem conversationally

## 🇦🇹 Austrian Market Focus

**Local Services Integration**:
- Wien.gv.at services automation
- ÖBB travel planning and booking
- Geizhals.at price tracking
- Austrian banking and FinanzOnline
- Local business directory and recommendations

**Privacy-First Architecture**:
- Local LLM processing (no data to US servers)
- Austrian data sovereignty compliance
- GDPR native design
- Zero surveillance, maximum privacy

## 🤖 MCP Ecosystem Integration

Edna orchestrates specialized MCP servers:

### **🏠 Home & Security**
- **homecontrol-mcp**: Smart home automation with AI
- **security-mcp**: Camera and alarm system management
- **energy-mcp**: Optimize power usage and costs

### **📱 Digital Life**
- **calendar-mcp**: Intelligent scheduling
- **email-mcp**: Smart email management  
- **notification-mcp**: Context-aware alerts

### **🇦🇹 Austrian Services**
- **wien-services-mcp**: City services automation
- **oebb-mcp**: Travel planning and booking
- **finance-austria-mcp**: Banking and tax assistance

### **🎯 Personal Productivity**
- **shopping-mcp**: Price tracking and deal finding
- **media-mcp**: Plex, Calibre, entertainment management
- **backup-mcp**: Data protection and recovery

## 🚀 Getting Started

```bash
# Clone the repository
git clone https://github.com/sandraschi/ednaficator.git
cd ednaficator

# Install dependencies
pip install -r requirements.txt

# Configure Austrian locale and services
python setup.py configure --region=austria --city=vienna

# Start Edna
python -m ednaficator.main
```

## 📋 Example Conversations

**Vacation Planning**:
```
User: "Edna, I'm going on vacation next week"
Edna: "I'll handle everything - switching home to vacation mode, 
       holding mail delivery, notifying neighbors, and setting 
       travel budget alerts. Your house will be secure!"
```

**Smart Home**:
```
User: "Edna, something feels off with the house"
Edna: "I've checked all systems - cameras show normal activity, 
       but your energy usage is 15% higher than usual. 
       Shall I investigate the heating system?"
```

**Austrian Services**:
```
User: "Edna, help me renew my parking permit"
Edna: "I've pre-filled your Wien.gv.at parking application 
       with your current details. Just review and submit - 
       should take 2 minutes instead of 20!"
```

## 🔧 Technical Architecture

**Core Components**:
- **Edna Core**: Natural language processing and workflow orchestration
- **MCP Bridge**: Communication layer for MCP server ecosystem
- **Memory Engine**: Local knowledge base and user learning (basic-memory fork)
- **Austrian Services**: Local service integrations and compliance
- **Local LLM**: Privacy-first AI processing

**Technology Stack**:
- **Python 3.11+**: Core application framework
- **FastMCP 3.2.0**: MCP server architecture
- **SQLite**: Local data storage
- **Local LLM**: Llama 3.1/Mistral for AI processing
- **Austrian APIs**: Wien.gv.at, ÖBB, Geizhals.at integrations

## 🏗️ Development Status

**Phase 1: MCP Integration** ⚡ *In Progress*
- [x] Basic MCP orchestration
- [x] Memory system integration  
- [ ] Austrian services framework
- [ ] Local LLM integration

**Phase 2: AI Enhancement** 🧠 *Planned*
- [ ] Conversation memory
- [ ] User preference learning
- [ ] Workflow optimization
- [ ] Predictive assistance

**Phase 3: Market Launch** 🇦🇹 *Q1 2025*
- [ ] Austrian market validation
- [ ] GDPR compliance verification
- [ ] Local business partnerships
- [ ] Community feedback integration

## 📄 License

MIT License - Built with Austrian engineering precision! 🇦🇹

## 🤝 Contributing

We welcome contributions that enhance Austrian digital sovereignty and user privacy!

---

**"Finally, an AI assistant that speaks Austrian, stays in Austria, and actually helps!"** 🚀
