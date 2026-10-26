"""
Unit Tests for Cinevora Gemini AI Movie Concierge
Tests verify:
1. Zero API key leakage or external network dependency (100% mocked)
2. Safe fallbacks when Gemini is unconfigured or encounters upstream errors
3. Robust natural-language genre detection and decade/year constraint parsing
4. Application-enforced genre-plus-decade constraints (e.g. 90s Action movies)
5. Strict handling of unsatisfiable / no-match criteria without returning out-of-decade films
6. Verification of the configured Gemini model (gemini-3.5-flash-lite)
"""

import sys
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from google.genai import errors
from app.assistant import GeminiAssistant
from app.config import settings
from src.recommender import CinevoraRecommender


@pytest.fixture(scope="module")
def recommender_instance():
    """Loads the trained Cinevora recommender artifact for grounding tests."""
    model_path = settings.MODEL_ARTIFACT_PATH
    assert model_path.exists(), "Recommender artifact must exist to run assistant tests."
    return CinevoraRecommender.load(str(model_path))


# -----------------------------------------------------------------------------
# 1. Model Configuration Verification
# -----------------------------------------------------------------------------
def test_configured_model_name():
    """Verifies that the configured model defaults to gemini-3.5-flash-lite."""
    assistant = GeminiAssistant(api_key="")
    assert assistant.model_name == "gemini-3.5-flash-lite"
    assert settings.GEMINI_MODEL == "gemini-3.5-flash-lite"


# -----------------------------------------------------------------------------
# 2. Natural Language Genre & Decade Parsing Tests
# -----------------------------------------------------------------------------
def test_genre_detection_keywords():
    """Verifies that common natural-language movie phrases map accurately to official genres."""
    assistant = GeminiAssistant(api_key="")

    assert assistant.detect_genre_from_text("I need a hilarious and funny comedy") == "Comedy"
    assert assistant.detect_genre_from_text("Show me an intense scary horror film") == "Horror"
    assert assistant.detect_genre_from_text("Looking for a cool space alien sci-fi flick") == "Sci-Fi"
    assert assistant.detect_genre_from_text("I love cowboy and western adventures") == "Western"
    assert assistant.detect_genre_from_text("Any emotional romantic love story?") == "Romance"
    assert assistant.detect_genre_from_text("Just a regular movie please") is None


def test_decade_and_year_detection():
    """Verifies parsing of release decade and year constraints."""
    assistant = GeminiAssistant(api_key="")

    # 2-digit decade
    res_90s = assistant.detect_decade_or_year("an exciting, fast-paced action movie from the 90s")
    assert res_90s == (1990, 1999, "1990s")

    # 4-digit decade
    res_1980s = assistant.detect_decade_or_year("classic 1980s sci fi")
    assert res_1980s == (1980, 1989, "1980s")

    # Word decade
    res_nineties = assistant.detect_decade_or_year("great comedies from the nineties")
    assert res_nineties == (1990, 1999, "1990s")

    # Exact year
    res_1994 = assistant.detect_decade_or_year("drama released in 1994")
    assert res_1994 == (1994, 1994, "1994")

    # No decade/year mentioned
    assert assistant.detect_decade_or_year("just a good movie") is None


# -----------------------------------------------------------------------------
# 3. Application-Enforced Genre + Decade Filtering (90s Action)
# -----------------------------------------------------------------------------
def test_genre_plus_decade_filtering_action(recommender_instance):
    """
    Verifies that 'an exciting, fast-paced action movie from 2023' returns
    recommendations that satisfy BOTH the Action genre AND the 2023 release window.
    Enforced in application code, not solely by the LLM prompt.
    """
    assistant = GeminiAssistant(api_key="")

    res = assistant.chat(
        message="an exciting, fast-paced action movie from 2023",
        recommender=recommender_instance,
        limit=5
    )

    assert res.detected_genre == "Action"
    assert res.detected_decade == "2023"
    assert len(res.recommendations) > 0

    for item in res.recommendations:
        # Must contain Action
        assert "Action" in item.genres, f"Movie {item.movie_title} does not have Action genre"

        # Must be released in 2023
        m_year = re.search(r"(\d{4})", item.release_date or item.movie_title)
        assert m_year is not None, f"Could not determine year for {item.movie_title}"
        year = int(m_year.group(1))
        assert year == 2023, f"Movie {item.movie_title} with year {year} is not 2023!"


# -----------------------------------------------------------------------------
# 4. Unsatisfiable / No-Match Constraint Case
# -----------------------------------------------------------------------------
def test_no_match_decade_genre_returns_empty_with_explanation(recommender_instance):
    """
    Verifies that an unsatisfiable constraint (e.g. Action movie from the 1920s)
    returns 0 recommendations and a clear explanation, rather than returning
    movies from outside the requested decade.
    """
    assistant = GeminiAssistant(api_key="")

    res = assistant.chat(
        message="Action movie from the 1920s",
        recommender=recommender_instance,
        limit=5
    )

    assert res.detected_genre == "Action"
    assert res.detected_decade == "1920s"
    assert len(res.recommendations) == 0, "Must not return movies outside the requested 1920s era"
    assert "No movies in Cinevora's catalog matched" in res.reply
    assert "1920s" in res.reply


# -----------------------------------------------------------------------------
# 5. Unconfigured / Missing API Key Fallback Test
# -----------------------------------------------------------------------------
def test_assistant_unconfigured_fallback(recommender_instance):
    """
    Verifies that when no API key is provided, the assistant does NOT crash,
    and returns valid catalog recommendations in fallback mode.
    """
    assistant = GeminiAssistant(api_key="")
    assert not assistant.is_available

    res = assistant.chat(
        message="Recommend me some good 2023 action movies",
        recommender=recommender_instance,
        user_id=1,
        limit=3
    )

    assert res.assistant_mode == "catalog_fallback"
    assert len(res.recommendations) == 3
    assert "catalog" in res.reply.lower() or "recommendations" in res.reply.lower()
    assert all(r.movie_id for r in res.recommendations)


# -----------------------------------------------------------------------------
# 6. Mocked Gemini Success Test (Zero Cost / Offline)
# -----------------------------------------------------------------------------
def test_mocked_gemini_chat_success(recommender_instance):
    """
    Verifies that a valid Gemini response is processed properly
    without incurring API calls or requiring a live key.
    """
    with patch("app.assistant.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # Mock generate_content response
        mock_response = MagicMock()
        mock_response.text = (
            "Here are two fantastic Sci-Fi classics! Star Wars is an epic space journey, "
            "and Contact offers thoughtful scientific exploration."
        )
        mock_client.models.generate_content.return_value = mock_response

        assistant = GeminiAssistant(api_key="mocked_fake_key_12345")
        assert assistant.is_available

        res = assistant.chat(
            message="I want an epic sci-fi movie",
            recommender=recommender_instance,
            user_id=1,
            genre_override="Sci-Fi",
            limit=2
        )

        assert res.assistant_mode == "gemini_flash"
        assert res.reply == mock_response.text
        assert res.detected_genre == "Sci-Fi"
        assert len(res.recommendations) == 2
        for rec in res.recommendations:
            assert "Sci-Fi" in rec.genres


# -----------------------------------------------------------------------------
# 7. Mocked Gemini Upstream API Error & Quota Limit Test
# -----------------------------------------------------------------------------
def test_mocked_gemini_api_error_fallback(recommender_instance):
    """
    Verifies that when Gemini raises an API error (e.g. quota 429 or server error 500),
    the assistant catches it cleanly, logs safely, does not leak secrets,
    and returns catalog recommendations.
    """
    with patch("app.assistant.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # Simulate Gemini 429 Quota Exceeded error
        mock_client.models.generate_content.side_effect = errors.APIError(
            429,
            {"error": {"message": "Resource has been exhausted (quota limit reached).", "status": "RESOURCE_EXHAUSTED"}}
        )

        assistant = GeminiAssistant(api_key="secret_do_not_leak_key")
        res = assistant.chat(
            message="Recommend an action movie",
            recommender=recommender_instance,
            limit=2
        )

        assert res.assistant_mode == "catalog_fallback"
        assert "secret_do_not_leak_key" not in res.reply
        assert "upstream service limit" in res.reply
        assert len(res.recommendations) == 2


# -----------------------------------------------------------------------------
# 8. Strict Grounding Verification
# -----------------------------------------------------------------------------
def test_recommendation_grounding_matches_catalog(recommender_instance):
    """Verifies that all returned recommendation items exist in Cinevora's true catalog."""
    from src.catalog_service import load_master_catalog
    assistant = GeminiAssistant(api_key="")
    res = assistant.chat(
        message="Give me top drama movies",
        recommender=recommender_instance,
        limit=5
    )

    df_master = load_master_catalog()
    catalog_ids = set(df_master["catalog_id"].astype(str)).union(set(df_master["movie_id"].astype(str)))
    for rec in res.recommendations:
        assert str(rec.movie_id) in catalog_ids, f"Movie ID {rec.movie_id} is not in Cinevora catalog!"
        assert 1.0 <= rec.predicted_rating <= 10.0


# -----------------------------------------------------------------------------
# 9. Verification State Tests (Missing, Connected, Failed, Quota, Fallbacks)
# -----------------------------------------------------------------------------
def test_verify_connection_missing_key():
    """Verifies that empty or None API key returns 'configuration_missing'."""
    assistant = GeminiAssistant(api_key="")
    status = assistant.verify_connection(force=True)
    assert status["status_state"] == "configuration_missing"
    assert status["configured"] is False
    assert status["verified"] is False
    assert status["fallback_active"] is True


def test_verify_connection_success():
    """Verifies that successful API response returns 'connected' status."""
    with patch("app.assistant.genai.Client") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_resp = MagicMock()
        mock_resp.text = "pong"
        mock_client.models.generate_content.return_value = mock_resp

        assistant = GeminiAssistant(api_key="valid_test_key_xyz", model_name="gemini-3.5-flash-lite")
        status = assistant.verify_connection(force=True)

        assert status["status_state"] == "connected"
        assert status["configured"] is True
        assert status["verified"] is True
        assert status["fallback_active"] is False
        assert "Connected" in status["status"]


def test_verify_connection_failed_invalid_key():
    """Verifies that 401 or invalid key returns 'verification_failed'."""
    with patch("app.assistant.genai.Client") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.models.generate_content.side_effect = Exception("401 API_KEY_INVALID: User not authorized")

        assistant = GeminiAssistant(api_key="bad_key", model_name="gemini-3.5-flash-lite")
        status = assistant.verify_connection(force=True)

        assert status["status_state"] == "verification_failed"
        assert status["configured"] is True
        assert status["verified"] is False
        assert status["fallback_active"] is True
        assert "bad_key" not in status["status"]


def test_verify_connection_quota_or_network_error():
    """Verifies that 429 quota or network errors return 'quota_or_network_error'."""
    with patch("app.assistant.genai.Client") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.models.generate_content.side_effect = Exception("429 Resource has been exhausted (quota limit reached)")

        assistant = GeminiAssistant(api_key="some_key", model_name="gemini-3.5-flash-lite")
        status = assistant.verify_connection(force=True)

        assert status["status_state"] == "quota_or_network_error"
        assert status["configured"] is True
        assert status["verified"] is False
        assert status["fallback_active"] is True


def test_verify_connection_model_substitution():
    """Verifies that if configured model fails with not found, fallback models are tested."""
    with patch("app.assistant.genai.Client") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client

        def side_effect(model, contents, **kwargs):
            if model == "unsupported-model-v99":
                raise Exception("404 Model unsupported-model-v99 not found")
            mock_ok = MagicMock()
            mock_ok.text = "hello"
            return mock_ok

        mock_client.models.generate_content.side_effect = side_effect

        assistant = GeminiAssistant(api_key="valid_key", model_name="unsupported-model-v99")
        status = assistant.verify_connection(force=True)

        assert status["status_state"] == "connected"
        assert status["verified"] is True
        assert status["model"] != "unsupported-model-v99"
