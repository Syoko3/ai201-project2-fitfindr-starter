"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os
import re

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    listings = load_listings()

    # Keywords from the description, lowercased and deduped.
    keywords = {word for word in re.findall(r"[a-z0-9]+", description.lower())}

    results = []
    for listing in listings:
        # Filter by price ceiling (inclusive).
        if max_price is not None and listing.get("price", 0) > max_price:
            continue

        # Filter by size — case-insensitive, allows partial matches like
        # "M" matching "S/M".
        if size is not None:
            listing_size = (listing.get("size") or "").lower()
            if size.lower() not in listing_size:
                continue

        # Score by keyword overlap across the listing's text fields.
        searchable = " ".join([
            listing.get("title", ""),
            listing.get("description", ""),
            listing.get("category", ""),
            listing.get("brand") or "",
            " ".join(listing.get("style_tags", [])),
            " ".join(listing.get("colors", [])),
        ]).lower()
        listing_words = set(re.findall(r"[a-z0-9]+", searchable))
        score = len(keywords & listing_words)

        # Drop listings with no relevant keyword matches.
        if score == 0:
            continue

        results.append((score, listing))

    # Sort by score, highest first; preserve dataset order for ties.
    results.sort(key=lambda pair: pair[0], reverse=True)
    return [listing for _, listing in results]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    client = _get_groq_client()

    # Describe the thrifted item for the prompt.
    item_desc = (
        f"- Title: {new_item.get('title', 'Unknown item')}\n"
        f"- Category: {new_item.get('category', 'unknown')}\n"
        f"- Colors: {', '.join(new_item.get('colors', [])) or 'unspecified'}\n"
        f"- Style: {', '.join(new_item.get('style_tags', [])) or 'unspecified'}\n"
        f"- Condition: {new_item.get('condition', 'unknown')}"
    )

    items = wardrobe.get("items", []) if wardrobe else []

    if not items:
        # Empty wardrobe: ask for general styling advice instead of crashing.
        system_prompt = (
            "You are FitFindr, a friendly thrift-stylist assistant. The user is "
            "considering buying a secondhand item but hasn't shared their wardrobe. "
            "Give general styling advice: what kinds of pieces pair well with it, "
            "what vibe it suits, and one or two example outfit ideas. Keep it warm, "
            "specific, and concise."
        )
        user_prompt = f"Here's the item I'm thinking of buying:\n{item_desc}"
    else:
        # Format the wardrobe so the model can name specific pieces.
        wardrobe_lines = "\n".join(
            f"- {w.get('name', 'item')} "
            f"({w.get('category', '?')}; "
            f"{', '.join(w.get('colors', [])) or 'no colors'}; "
            f"{', '.join(w.get('style_tags', [])) or 'no tags'})"
            for w in items
        )
        system_prompt = (
            "You are FitFindr, a friendly thrift-stylist assistant. Suggest 1-2 "
            "complete outfits that combine the new thrifted item with specific "
            "pieces the user already owns. Refer to wardrobe pieces by name. "
            "Explain briefly why each outfit works. Keep it warm and concise."
        )
        user_prompt = (
            f"New thrifted item:\n{item_desc}\n\n"
            f"My current wardrobe:\n{wardrobe_lines}"
        )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,  # a little creativity for styling variety
    )
    return response.choices[0].message.content


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    # Guard against a missing or empty/whitespace-only outfit string.
    if not outfit or not outfit.strip():
        return (
            "Couldn't create a fit card — no outfit suggestion was provided. "
            "Run suggest_outfit() first to get styling ideas, then try again."
        )

    client = _get_groq_client()

    title = new_item.get("title", "this thrifted find")
    price = new_item.get("price")
    price_str = f"${price:.0f}" if isinstance(price, (int, float)) else "a steal"
    platform = new_item.get("platform", "secondhand")

    system_prompt = (
        "You are FitFindr, writing a short, shareable OOTD caption for a thrift "
        "find. Write 2-4 sentences that feel casual and authentic — like a real "
        "outfit-of-the-day post, not a product description. Mention the item "
        "name, its price, and the platform naturally, once each. Capture the "
        "outfit's vibe in specific terms. A couple of emojis are fine; no "
        "hashtag dumps."
    )
    user_prompt = (
        f"Item: {title}\n"
        f"Price: {price_str}\n"
        f"Platform: {platform}\n\n"
        f"Outfit the person is wearing it with:\n{outfit}\n\n"
        "Write the caption."
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=1.0,  # high temperature so captions vary run to run
    )
    return response.choices[0].message.content
