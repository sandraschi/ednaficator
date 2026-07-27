"""
Tests for the NLP processor module.
"""

from unittest.mock import MagicMock, patch

import pytest
from ednaficator.nlp.processor_fixed import Intent, NLPProcessor

# Test data
TEST_LLM_ENDPOINT = "http://localhost:11434"

# Test cases
TEST_CASES = [
    # Input text, expected category, expected action, min_confidence
    ("Schalte das Licht im Wohnzimmer ein", "home", "set", 0.7),
    ("Wann fährt der nächste Zug nach Wien?", "austrian_services", "query", 0.7),
    ("Wie ist das Wetter morgen?", "general", "query", 0.5),
    ("Starte den Urlaubsmodus", "workflow", "execute_workflow", 0.8),
    ("Zeig mir Filme mit Tom Hanks", "media", "search", 0.7),
]


# Fixture for NLP processor
@pytest.fixture
def nlp_processor():
    return NLPProcessor(local_llm_endpoint=TEST_LLM_ENDPOINT)


# Mock LLM response for testing
MOCK_LLM_RESPONSE = {
    "response": """
    {
        "category": "home",
        "action": "set",
        "target": "light",
        "params": {"state": "on", "location": "living room"},
        "confidence": 0.95,
        "workflow": null
    }
    """
}


# Test pattern matching
@pytest.mark.parametrize("input_text,expected_category,expected_action,min_confidence", TEST_CASES)
async def test_pattern_matching(
    nlp_processor, input_text, expected_category, expected_action, min_confidence
):
    """Test that pattern matching works for various inputs."""
    intent = nlp_processor._pattern_match_intent(input_text)
    assert intent is not None
    assert intent.category == expected_category or intent.action == expected_action
    assert intent.confidence >= min_confidence


# Test LLM fallback
@patch("httpx.AsyncClient.post")
async def test_llm_fallback(mock_post, nlp_processor):
    """Test that the LLM is called when pattern matching has low confidence."""
    # Setup mock
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_LLM_RESPONSE
    mock_post.return_value = mock_response

    # Test with input that would have low pattern matching confidence
    intent = await nlp_processor.parse_intent("Kannst du bitte das Licht anmachen?")

    # Verify
    assert intent is not None
    assert intent.category == "home"
    assert intent.action == "set"
    assert intent.target == "light"
    assert "state" in intent.params
    assert intent.confidence > 0.7


# Test error handling
@patch("httpx.AsyncClient.post")
async def test_llm_error_handling(mock_post, nlp_processor):
    """Test that the processor handles LLM errors gracefully."""
    # Setup mock to simulate error
    mock_post.side_effect = Exception("Connection error")

    # This should not raise an exception
    intent = await nlp_processor.parse_intent("This should fall back to pattern matching")

    # Should return a valid intent (possibly with lower confidence)
    assert intent is not None
    assert intent.confidence < 0.7  # Lower confidence for fallback


# Test entity extraction
def test_entity_extraction(nlp_processor):
    """Test that entities are correctly extracted from text."""
    text = "Erinner mich morgen um 14:30 in der Innenstadt"
    entities = nlp_processor.extract_entities(text)

    assert "time" in entities
    assert "vienna_district" in entities
    assert entities["vienna_district"] == "innere stadt"


# Test response generation
async def test_response_generation(nlp_processor):
    """Test that appropriate responses are generated for intents."""
    # Test home automation response
    home_intent = Intent(
        category="home", action="set", target="light", params={"state": "on"}, confidence=0.9
    )
    response = await nlp_processor.generate_response_text(home_intent)
    assert "gesichert" in response.lower() or "gesteuert" in response.lower()

    # Test media response
    media_intent = Intent(
        category="media",
        action="search",
        target="movie",
        params={"query": "Inception"},
        confidence=0.9,
    )
    response = await nlp_processor.generate_response_text(media_intent, [1, 2, 3])
    assert "3 ergebnisse" in response.lower()


# Test Austrian German normalization
def test_austrian_normalization(nlp_processor):
    """Test that Austrian German is properly normalized."""
    text = "I hätt gern an Paradeiser im Sackerl"
    normalized = nlp_processor._normalize_austrian_input(text)
    assert "tomate" in normalized
    assert "tüte" in normalized


# Run tests
if __name__ == "__main__":
    pytest.main(["-v", "test_nlp_processor.py"])
