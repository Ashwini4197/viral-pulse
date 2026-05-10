"""
viral_pulse/src/nlp/entities.py

Named Entity Recognition using spaCy.
Extracts: companies (ORG), people (PERSON), products (PRODUCT),
          geopolitical entities (GPE — countries, cities).

Install: python -m spacy download en_core_web_sm
"""

import re
import logging
from collections import Counter
from typing import Dict, List, Tuple

import spacy

logger = logging.getLogger(__name__)

# Load model once at import time (expensive operation)
try:
    _nlp = spacy.load("en_core_web_sm", disable=["parser"])   # parser not needed
except OSError:
    logger.warning("spaCy model not found. Run: python -m spacy download en_core_web_sm")
    _nlp = None

# Entity types we care about
TARGET_TYPES = {"ORG", "PERSON", "PRODUCT", "GPE"}

# Noise filter — skip generic words even if spaCy tags them as entities
STOPWORDS = {
    "reddit", "twitter", "google", "facebook", "amazon",  # Too common to be insightful
    "the", "a", "an", "this", "that",
    "monday", "tuesday", "wednesday", "thursday", "friday",
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
}


def extract_entities(text: str) -> List[Tuple[str, str, int]]:
    """
    Extract named entities from text.

    Returns:
        List of (entity_text, entity_type, mention_count) tuples,
        deduplicated and sorted by frequency.
    """
    if not _nlp or not text:
        return []

    # Truncate very long texts (spaCy limit)
    doc = _nlp(text[:50_000])

    counts: Counter = Counter()
    for ent in doc.ents:
        if ent.label_ not in TARGET_TYPES:
            continue

        clean = ent.text.strip().title()

        # Filter short, numeric, or stopword entities
        if len(clean) < 2 or clean.lower() in STOPWORDS:
            continue
        if re.fullmatch(r"[\d\s\W]+", clean):
            continue

        counts[(clean, ent.label_)] += 1

    return [(text, label, count) for (text, label), count in counts.most_common(20)]


def extract_from_post(post: Dict) -> List[Dict]:
    """
    Extract entities from a post dict.

    Returns list of entity dicts ready to insert into extracted_entities.
    """
    title = post.get("title", "") or ""
    body  = post.get("body",  "") or ""
    combined = f"{title} {body}"

    entities = extract_entities(combined)
    return [
        {
            "post_id":      post["post_id"],
            "entity_text":  entity_text,
            "entity_type":  entity_type,
            "mention_count": count,
        }
        for entity_text, entity_type, count in entities
    ]


if __name__ == "__main__":
    sample = """
    Apple and Microsoft are competing fiercely. Elon Musk announced
    a new Tesla product at CES in Las Vegas. OpenAI released GPT-5
    while Google DeepMind responded with Gemini Pro.
    """
    for entity, label, count in extract_entities(sample):
        print(f"[{label:8s}] {entity} ({count}x)")
