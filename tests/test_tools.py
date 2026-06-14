"""
Tests for the three FitFindr tools in tools.py.

The two LLM-backed tools (suggest_outfit, create_fit_card) call Groq over the
network. We mock the Groq client so the tests are deterministic and don't make
paid API calls. search_listings reads the local dataset, so it runs for real.

Each tool has at least one test for its documented failure mode:
    search_listings  → no results match            (returns [])
    suggest_outfit   → wardrobe is empty            (returns general advice)
    create_fit_card  → outfit is empty/whitespace   (returns error message)
"""

from unittest.mock import MagicMock, patch

import pytest

import tools


# ── Helpers ─────────────────────────────────────────────────────────────────

def _mock_groq_returning(text):
    """Build a fake Groq client whose chat completion returns `text`."""
    client = MagicMock()
    message = MagicMock()
    message.content = text
    choice = MagicMock()
    choice.message = message
    client.chat.completions.create.return_value = MagicMock(choices=[choice])
    return client


@pytest.fixture
def sample_item():
    return {
        "id": "lst_test",
        "title": "Y2K Baby Tee — Butterfly Print",
        "category": "tops",
        "style_tags": ["y2k", "vintage", "graphic tee"],
        "colors": ["white", "pink"],
        "condition": "excellent",
        "price": 18.0,
        "platform": "depop",
    }


# ── Tool 1: search_listings ──────────────────────────────────────────────────

def test_search_returns_relevant_matches():
    """A common query returns a non-empty list of dicts with the right shape."""
    results = tools.search_listings("vintage graphic tee")
    assert isinstance(results, list)
    assert len(results) > 0
    assert all(isinstance(r, dict) and "title" in r for r in results)


def test_search_no_match_returns_empty_list():
    """Failure mode: no listing matches -> returns [] without raising."""
    results = tools.search_listings("nonexistent spaceship rocketship gizmo")
    assert results == []


def test_search_respects_max_price():
    """Every result must be at or under the price ceiling."""
    results = tools.search_listings("tee", max_price=20.0)
    assert results, "expected at least one cheap tee in the dataset"
    assert all(r["price"] <= 20.0 for r in results)


def test_search_size_filter_is_case_insensitive_and_partial():
    """Size 'm' should match listings whose size contains it (e.g. 'S/M')."""
    results = tools.search_listings("tee", size="m")
    for r in results:
        assert "m" in r["size"].lower()


# ── Tool 2: suggest_outfit ───────────────────────────────────────────────────

def test_suggest_outfit_with_wardrobe(sample_item):
    """Populated wardrobe -> returns the LLM's outfit suggestion string."""
    wardrobe = {"items": [
        {"name": "Baggy jeans", "category": "bottoms",
         "colors": ["blue"], "style_tags": ["denim"]},
    ]}
    fake = _mock_groq_returning("Outfit: tee + baggy jeans.")
    with patch.object(tools, "_get_groq_client", return_value=fake):
        result = tools.suggest_outfit(sample_item, wardrobe)
    assert result == "Outfit: tee + baggy jeans."
    fake.chat.completions.create.assert_called_once()


def test_suggest_outfit_empty_wardrobe_returns_advice(sample_item):
    """Failure mode: empty wardrobe -> general advice, non-empty, no crash."""
    fake = _mock_groq_returning("General styling advice for the tee.")
    with patch.object(tools, "_get_groq_client", return_value=fake):
        result = tools.suggest_outfit(sample_item, {"items": []})
    assert isinstance(result, str) and result.strip()
    fake.chat.completions.create.assert_called_once()


def test_suggest_outfit_missing_items_key_does_not_crash(sample_item):
    """A wardrobe dict without an 'items' key is handled gracefully."""
    fake = _mock_groq_returning("Advice.")
    with patch.object(tools, "_get_groq_client", return_value=fake):
        result = tools.suggest_outfit(sample_item, {})
    assert isinstance(result, str) and result.strip()


# ── Tool 3: create_fit_card ──────────────────────────────────────────────────

def test_create_fit_card_with_outfit(sample_item):
    """A valid outfit -> returns the LLM caption string."""
    fake = _mock_groq_returning("Scored this tee for $18 on depop! 😎")
    with patch.object(tools, "_get_groq_client", return_value=fake):
        result = tools.create_fit_card("tee + baggy jeans + sneakers", sample_item)
    assert result == "Scored this tee for $18 on depop! 😎"
    fake.chat.completions.create.assert_called_once()


def test_create_fit_card_empty_outfit_returns_error(sample_item):
    """Failure mode: empty outfit -> error message string, no LLM call, no crash."""
    with patch.object(tools, "_get_groq_client") as mock_client:
        result = tools.create_fit_card("", sample_item)
    assert isinstance(result, str) and result.strip()
    mock_client.assert_not_called()  # guard returns before calling the LLM


def test_create_fit_card_whitespace_outfit_returns_error(sample_item):
    """Whitespace-only outfit is treated the same as empty."""
    with patch.object(tools, "_get_groq_client") as mock_client:
        result = tools.create_fit_card("   \n  ", sample_item)
    assert isinstance(result, str) and result.strip()
    mock_client.assert_not_called()
