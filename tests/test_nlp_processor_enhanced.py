"""
Tests for the enhanced NLP processor.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# Add the parent directory to the Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from ednaficator.nlp.processor_enhanced import NLPProcessor, Intent

@pytest.fixture
def nlp_processor():
    """Create an NLP processor instance for testing."""
    # Use a mock LLM endpoint for testing
    return NLPProcessor(local_llm_endpoint="http://localhost:12345/mock-llm")

@pytest.mark.asyncio
async def test_greeting_intent(nlp_processor):
    """Test greeting intent detection."""
    # Test with different greeting variations
    test_cases = [
        "Hallo Edna!",
        "Servus, wie geht's?",
        "Grüß dich, was gibt's Neues?",
        "Guten Tag, könnten Sie mir helfen?"
    ]
    
    for text in test_cases:
        intent = await nlp_processor.parse_intent(text)
        assert intent.category == "greeting"
        assert intent.action == "greet"
        assert intent.target == "user"
        assert intent.confidence >= 0.8

@pytest.mark.asyncio
async def test_weather_intent(nlp_processor):
    """Test weather intent detection."""
    # Test with different weather-related queries
    test_cases = [
        ("Wie wird das Wetter in Wien?", "wien"),
        ("Wird es morgen regnen?", None),
        ("Zeig mir die Temperatur für übermorgen", None)
    ]
    
    for text, expected_location in test_cases:
        intent = await nlp_processor.parse_intent(text)
        assert intent.category == "weather"
        assert intent.action == "get"
        assert intent.target == "weather"
        if expected_location:
            assert "location" in intent.entities
            assert intent.entities["location"].lower() == expected_location

@pytest.mark.asyncio
async def test_transport_intent(nlp_processor):
    """Test transport intent detection."""
    # Test with different transport-related queries
    test_cases = [
        ("Wann kommt die nächste U-Bahn?", "u-bahn"),
        ("Wann fährt der nächste Bus nach Hütteldorf?", "bus"),
        ("ÖBB Verbindung Wien Salzburg", "öbb")
    ]
    
    for text, expected_type in test_cases:
        intent = await nlp_processor.parse_intent(text)
        assert intent.category == "transport"
        assert intent.action == "get"
        assert intent.target == "schedule"
        if expected_type:
            assert "transport_type" in intent.entities
            assert expected_type in intent.entities["transport_type"].lower()

@pytest.mark.asyncio
async def test_austrian_terms(nlp_processor):
    """Test Austrian German term normalization."""
    # Test with Austrian terms that should be normalized
    test_cases = [
        ("Wo sind die Paradeiser?", "tomate"),
        ("Ich hätte gerne ein Erdäpfelsalat", "kartoffel"),
        ("Servus, hast du Fisolen?", ["hallo", "grüne bohnen"])
    ]
    
    for text, expected_terms in test_cases:
        normalized = nlp_processor._normalize_input(text)
        if isinstance(expected_terms, list):
            for term in expected_terms:
                assert term in normalized
        else:
            assert expected_terms in normalized

@pytest.mark.asyncio
async def test_llm_fallback(nlp_processor):
    """Test LLM fallback for complex queries."""
    # Mock the LLM response
    mock_response = {
        "response": """{
            "category": "shopping",
            "action": "find",
            "target": "product",
            "entities": {"product": "Apfelstrudel", "store": "Billa"},
            "confidence": 0.85
        }"""
    }
    
    with patch('aiohttp.ClientSession.post', new_callable=AsyncMock) as mock_post:
        # Set up the mock
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aenter__.return_value = mock_resp
        
        # Test a complex query that would trigger LLM fallback
        intent = await nlp_processor.parse_intent(
            "Wo finde ich den besten Apfelstrudel in Wien?"
        )
        
        # Verify the LLM was called
        mock_post.assert_called_once()
        
        # Verify the response
        assert intent.category == "shopping"
        assert intent.action == "find"
        assert intent.target == "product"
        assert intent.entities["product"] == "Apfelstrudel"
        assert intent.confidence == 0.85

@pytest.mark.asyncio
async def test_llm_error_handling(nlp_processor):
    """Test error handling when LLM is unavailable."""
    with patch('aiohttp.ClientSession.post', side_effect=Exception("Connection error")):
        # Test a complex query that would trigger LLM fallback
        intent = await nlp_processor.parse_intent(
            "Erzähl mir etwas über die Geschichte von Wien"
        )
        
        # Should fall back to a general intent
        assert intent.category == "general"
        assert intent.action == "unknown"
        assert intent.confidence == 0.3

def test_entity_extraction(nlp_processor):
    """Test entity extraction from text."""
    test_cases = [
        (
            "Wie wird das Wetter in Graz?", 
            {"location": [r"in\s+(\w+)"]},
            {"location": "Graz"}
        ),
        (
            "Erinnere mich morgen um 10 Uhr",
            {"time": [r"morgen", r"um\s+(\d+)\s*uhr"]},
            {"time": "morgen"}  # Should match the first pattern
        )
    ]
    
    for text, patterns, expected_entities in test_cases:
        entities = nlp_processor._extract_entities(text, patterns)
        for key, value in expected_entities.items():
            assert key in entities
            assert value.lower() in entities[key].lower()

if __name__ == "__main__":
    # Run the tests
    import sys
    import pytest
    sys.exit(pytest.main(["-v", __file__]))
