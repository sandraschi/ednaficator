"""
Memory Engine - Edna's Long-term Memory System

Integrates with basic-memory MCP for conversation context,
user preferences, and workflow learning.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class MemoryEngine:
    """
    Edna's memory system for learning and context

    Provides:
    - Conversation memory across sessions
    - User preference learning
    - Workflow template storage
    - Austrian service knowledge
    """

    def __init__(self, memory_path: str):
        self.memory_path = Path(memory_path)
        self.memory_path.mkdir(exist_ok=True)

        # Memory stores
        self.conversations: list[dict] = []
        self.user_preferences: dict = {}
        self.workflow_templates: dict = {}
        self.austrian_knowledge: dict = {}

    async def initialize(self):
        """Initialize memory system and load existing data"""
        print("🧠 Initializing Edna's memory system...")

        # Load existing memory files
        await self.load_conversations()
        await self.load_user_preferences()
        await self.load_workflow_templates()
        await self.load_austrian_knowledge()

        print(f"📚 Loaded {len(self.conversations)} conversations")
        print(f"👤 Loaded {len(self.user_preferences)} user preferences")
        print(f"⚙️ Loaded {len(self.workflow_templates)} workflow templates")

    async def load_conversations(self):
        """Load conversation history"""
        conv_file = self.memory_path / "conversations.json"
        if conv_file.exists():
            with open(conv_file, encoding="utf-8") as f:
                self.conversations = json.load(f)

    async def load_user_preferences(self):
        """Load user preferences and learned patterns"""
        pref_file = self.memory_path / "user_preferences.json"
        if pref_file.exists():
            with open(pref_file, encoding="utf-8") as f:
                self.user_preferences = json.load(f)
        else:
            # Default Austrian preferences
            self.user_preferences = {
                "language": "german_austrian",
                "timezone": "Europe/Vienna",
                "currency": "EUR",
                "date_format": "DD.MM.YYYY",
                "temperature_unit": "celsius",
                "morning_routine_time": "07:00",
                "preferred_news_sources": ["orf.at", "derstandard.at"],
                "home_location": "Vienna, Austria",
            }

    async def load_workflow_templates(self):
        """Load saved workflow templates"""
        workflow_file = self.memory_path / "workflows.json"
        if workflow_file.exists():
            with open(workflow_file, encoding="utf-8") as f:
                self.workflow_templates = json.load(f)
        else:
            # Default Austrian workflows
            self.workflow_templates = {
                "vacation_mode": [
                    {"server": "homecontrol-mcp", "action": "vacation_mode", "params": {}},
                    {
                        "server": "basic-memory",
                        "action": "store_note",
                        "params": {"note": "Vacation started"},
                    },
                    {"server": "wien-services-mcp", "action": "hold_mail", "params": {}},
                ],
                "morning_routine": [
                    {"server": "homecontrol-mcp", "action": "morning_scene", "params": {}},
                    {"server": "plex-mcp", "action": "start_morning_playlist", "params": {}},
                    {"server": "wien-services-mcp", "action": "check_transport", "params": {}},
                ],
                "evening_routine": [
                    {"server": "homecontrol-mcp", "action": "evening_scene", "params": {}},
                    {"server": "calibre-mcp", "action": "suggest_book", "params": {}},
                    {"server": "basic-memory", "action": "daily_summary", "params": {}},
                ],
            }

    async def load_austrian_knowledge(self):
        """Load Austrian-specific knowledge and services"""
        austria_file = self.memory_path / "austrian_knowledge.json"
        if austria_file.exists():
            with open(austria_file, encoding="utf-8") as f:
                self.austrian_knowledge = json.load(f)
        else:
            # Default Austrian knowledge base
            self.austrian_knowledge = {
                "government_services": {
                    "wien.gv.at": "Vienna city services",
                    "help.gv.at": "Austrian government portal",
                    "finanzonline.bmf.gv.at": "Tax services",
                },
                "transport": {
                    "wienerlinien.at": "Vienna public transport",
                    "oebb.at": "Austrian railways",
                    "asfinag.at": "Highway information",
                },
                "shopping": {
                    "geizhals.at": "Price comparison",
                    "willhaben.at": "Marketplace",
                    "amazon.de": "Online shopping",
                },
                "emergency": {
                    "police": "133",
                    "fire": "122",
                    "ambulance": "144",
                    "emergency": "112",
                },
            }

    async def store_interaction(self, user_input: str, response: Any):
        """Store a conversation interaction for learning"""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "response": response.message if hasattr(response, "message") else str(response),
            "actions_taken": response.actions_taken if hasattr(response, "actions_taken") else [],
            "success": response.success if hasattr(response, "success") else True,
        }

        self.conversations.append(interaction)

        # Keep only last 1000 conversations to manage size
        if len(self.conversations) > 1000:
            self.conversations = self.conversations[-1000:]

        # Save to disk
        await self.save_conversations()

        # Learn from the interaction
        await self.learn_from_interaction(interaction)

    async def learn_from_interaction(self, interaction: dict):
        """Learn user preferences from successful interactions"""
        user_input = interaction["user_input"].lower()

        # Learn time preferences
        if "morning" in user_input and interaction["success"]:
            current_time = datetime.now().strftime("%H:%M")
            self.user_preferences["morning_routine_time"] = current_time

        # Learn language preferences
        if any(word in user_input for word in ["bitte", "danke", "grüß"]):
            self.user_preferences["language_preference"] = "german"

        # Learn service preferences
        if "wien" in user_input or "vienna" in user_input:
            self.user_preferences["location_focus"] = "vienna"

        await self.save_user_preferences()

    async def get_context(self, current_input: str) -> dict:
        """Get relevant context for current user input"""
        context = {
            "user_preferences": self.user_preferences.copy(),
            "recent_conversations": self.conversations[-5:],  # Last 5 interactions
            "relevant_workflows": [],
            "austrian_context": {},
        }

        # Find relevant workflows
        input_lower = current_input.lower()
        for workflow_name, steps in self.workflow_templates.items():
            if any(word in input_lower for word in workflow_name.split("_")):
                context["relevant_workflows"].append({"name": workflow_name, "steps": steps})

        # Add Austrian context if relevant
        if any(word in input_lower for word in ["vienna", "wien", "austria", "österreich"]):
            context["austrian_context"] = self.austrian_knowledge

        return context

    async def get_workflow_template(self, workflow_name: str) -> list[dict]:
        """Get a specific workflow template"""
        return self.workflow_templates.get(workflow_name, [])

    async def store_workflow_template(self, name: str, steps: list[dict]):
        """Store a new workflow template"""
        self.workflow_templates[name] = steps
        await self.save_workflow_templates()

    async def update_user_preference(self, key: str, value: Any):
        """Update a user preference"""
        self.user_preferences[key] = value
        await self.save_user_preferences()

    async def add_austrian_service(self, category: str, name: str, description: str):
        """Add Austrian service to knowledge base"""
        if category not in self.austrian_knowledge:
            self.austrian_knowledge[category] = {}

        self.austrian_knowledge[category][name] = description
        await self.save_austrian_knowledge()

    # Save methods
    async def save_conversations(self):
        """Save conversations to disk"""
        conv_file = self.memory_path / "conversations.json"
        with open(conv_file, "w", encoding="utf-8") as f:
            json.dump(self.conversations, f, indent=2, ensure_ascii=False)

    async def save_user_preferences(self):
        """Save user preferences to disk"""
        pref_file = self.memory_path / "user_preferences.json"
        with open(pref_file, "w", encoding="utf-8") as f:
            json.dump(self.user_preferences, f, indent=2, ensure_ascii=False)

    async def save_workflow_templates(self):
        """Save workflow templates to disk"""
        workflow_file = self.memory_path / "workflows.json"
        with open(workflow_file, "w", encoding="utf-8") as f:
            json.dump(self.workflow_templates, f, indent=2, ensure_ascii=False)

    async def save_austrian_knowledge(self):
        """Save Austrian knowledge to disk"""
        austria_file = self.memory_path / "austrian_knowledge.json"
        with open(austria_file, "w", encoding="utf-8") as f:
            json.dump(self.austrian_knowledge, f, indent=2, ensure_ascii=False)
