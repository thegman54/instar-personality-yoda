"""
Personality Yoda — Admin API Handlers

Provides CRUD endpoints for traits, quotes, lexicon, and reactions.
Loaded by the tool-executor's skill API discovery system.

Each handler is an async function: (pool, slug, body=None, item_id=None) → dict
The `routes` list maps (METHOD, regex_pattern) → handler.
"""

import hashlib
import json

import structlog
import yaml

log = structlog.get_logger()

TABLE_PREFIX = "personality_yoda"

# =============================================================================
# Layer ↔ Category mapping (shared with read tool)
# =============================================================================

CATEGORY_LAYERS = {
    'identity': 1, 'values': 1, 'worldview': 1,
    'voice': 2, 'lexicon': 2, 'tone': 2, 'emphasis': 2, 'humor': 2,
    'rhetoric': 3, 'social': 3, 'narrative': 3, 'authority': 3, 'deflection': 3,
    'reaction': 4, 'situational': 4,
    'signature': 5, 'quote': 5,
    'boundary': 6,
}


# =============================================================================
# TRAITS
# =============================================================================

async def list_traits(pool, slug, **_):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, category, subcategory, layer, content, examples, anti_examples,
                   tags, weight, stable, source, created_at, updated_at
            FROM personality_yoda_traits
            WHERE profile_slug = $1
            ORDER BY layer, category, stable DESC, weight DESC
            """,
            slug,
        )
    traits = [
        {
            "id": str(r['id']),
            "category": r['category'],
            "subcategory": r['subcategory'],
            "layer": r['layer'],
            "content": r['content'],
            "examples": list(r['examples']) if r['examples'] else [],
            "anti_examples": list(r['anti_examples']) if r['anti_examples'] else [],
            "tags": list(r['tags']) if r['tags'] else [],
            "weight": r['weight'],
            "stable": r['stable'],
            "source": r['source'],
            "created_at": r['created_at'].isoformat(),
            "updated_at": r['updated_at'].isoformat(),
        }
        for r in rows
    ]
    return {"profile_slug": slug, "count": len(traits), "traits": traits}


async def create_trait(pool, slug, body=None, **_):
    if not body:
        return {"__status": 400, "detail": "request body required"}
    content = (body.get('content') or '').strip()
    if not content:
        return {"__status": 400, "detail": "content is required"}

    category = body.get('category', 'identity')
    if category not in CATEGORY_LAYERS:
        return {"__status": 400, "detail": f"invalid category: {category}"}

    layer = CATEGORY_LAYERS[category]
    content_hash = hashlib.sha256(content.encode()).hexdigest()

    tags = body.get('tags', [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(',') if t.strip()]

    examples = body.get('examples', [])
    if isinstance(examples, str):
        examples = [e.strip() for e in examples.split('\n') if e.strip()]

    anti_examples = body.get('anti_examples', [])
    if isinstance(anti_examples, str):
        anti_examples = [e.strip() for e in anti_examples.split('\n') if e.strip()]

    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO personality_yoda_traits
                    (profile_slug, category, subcategory, layer, content, examples,
                     anti_examples, content_hash, tags, weight, stable, source)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                RETURNING id
                """,
                slug, category, body.get('subcategory'), layer, content,
                examples, anti_examples, content_hash, tags,
                float(body.get('weight', 1.0)),
                bool(body.get('stable', False)),
                body.get('source', 'manual'),
            )
            return {"id": str(row['id']), "status": "created"}
        except Exception as e:
            if 'unique' in str(e).lower():
                return {"__status": 409, "detail": "Duplicate trait content"}
            raise


async def delete_trait(pool, slug, item_id=None, **_):
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM personality_yoda_traits WHERE id = $1::uuid AND profile_slug = $2",
            item_id, slug,
        )
    if result == "DELETE 0":
        return {"__status": 404, "detail": "Trait not found"}
    return {"status": "deleted"}


# =============================================================================
# QUOTES
# =============================================================================

async def list_quotes(pool, slug, **_):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, quote, source, source_date, context, use_when,
                   paraphrase_ok, tone_tags, weight, created_at
            FROM personality_yoda_quotes
            WHERE profile_slug = $1
            ORDER BY weight DESC
            """,
            slug,
        )
    quotes = [
        {
            "id": str(r['id']),
            "quote": r['quote'],
            "source": r['source'],
            "source_date": r['source_date'].isoformat() if r['source_date'] else None,
            "context": r['context'],
            "use_when": list(r['use_when']) if r['use_when'] else [],
            "paraphrase_ok": r['paraphrase_ok'],
            "tone_tags": list(r['tone_tags']) if r['tone_tags'] else [],
            "weight": r['weight'],
            "created_at": r['created_at'].isoformat(),
        }
        for r in rows
    ]
    return {"profile_slug": slug, "count": len(quotes), "quotes": quotes}


async def create_quote(pool, slug, body=None, **_):
    if not body:
        return {"__status": 400, "detail": "request body required"}
    quote = (body.get('quote') or '').strip()
    if not quote:
        return {"__status": 400, "detail": "quote is required"}

    content_hash = hashlib.sha256(quote.encode()).hexdigest()

    use_when = body.get('use_when', [])
    if isinstance(use_when, str):
        use_when = [t.strip() for t in use_when.split(',') if t.strip()]

    tone_tags = body.get('tone_tags', [])
    if isinstance(tone_tags, str):
        tone_tags = [t.strip() for t in tone_tags.split(',') if t.strip()]

    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO personality_yoda_quotes
                    (profile_slug, quote, source, context, use_when,
                     paraphrase_ok, tone_tags, weight, content_hash)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id
                """,
                slug, quote, body.get('source'), body.get('context'),
                use_when, bool(body.get('paraphrase_ok', True)),
                tone_tags, float(body.get('weight', 1.0)), content_hash,
            )
            return {"id": str(row['id']), "status": "created"}
        except Exception as e:
            if 'unique' in str(e).lower():
                return {"__status": 409, "detail": "Duplicate quote"}
            raise


async def delete_quote(pool, slug, item_id=None, **_):
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM personality_yoda_quotes WHERE id = $1::uuid AND profile_slug = $2",
            item_id, slug,
        )
    if result == "DELETE 0":
        return {"__status": 404, "detail": "Quote not found"}
    return {"status": "deleted"}


# =============================================================================
# LEXICON
# =============================================================================

async def list_lexicon(pool, slug, **_):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, word_or_phrase, usage_type, frequency, context,
                   example, replaces, weight, created_at
            FROM personality_yoda_lexicon
            WHERE profile_slug = $1
            ORDER BY usage_type, weight DESC
            """,
            slug,
        )
    lexicon = [
        {
            "id": str(r['id']),
            "word_or_phrase": r['word_or_phrase'],
            "usage_type": r['usage_type'],
            "frequency": r['frequency'],
            "context": r['context'],
            "example": r['example'],
            "replaces": r['replaces'],
            "weight": r['weight'],
            "created_at": r['created_at'].isoformat(),
        }
        for r in rows
    ]
    return {"profile_slug": slug, "count": len(lexicon), "lexicon": lexicon}


async def create_lexicon(pool, slug, body=None, **_):
    if not body:
        return {"__status": 400, "detail": "request body required"}
    word = (body.get('word_or_phrase') or '').strip()
    if not word:
        return {"__status": 400, "detail": "word_or_phrase is required"}

    content_hash = hashlib.sha256(word.encode()).hexdigest()

    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO personality_yoda_lexicon
                    (profile_slug, word_or_phrase, usage_type, frequency,
                     context, example, replaces, weight, content_hash)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id
                """,
                slug, word,
                body.get('usage_type', 'favor'),
                body.get('frequency', 'often'),
                body.get('context'),
                body.get('example'),
                body.get('replaces'),
                float(body.get('weight', 1.0)),
                content_hash,
            )
            return {"id": str(row['id']), "status": "created"}
        except Exception as e:
            if 'unique' in str(e).lower():
                return {"__status": 409, "detail": "Duplicate lexicon entry"}
            raise


async def delete_lexicon(pool, slug, item_id=None, **_):
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM personality_yoda_lexicon WHERE id = $1::uuid AND profile_slug = $2",
            item_id, slug,
        )
    if result == "DELETE 0":
        return {"__status": 404, "detail": "Lexicon entry not found"}
    return {"status": "deleted"}


# =============================================================================
# REACTIONS
# =============================================================================

async def list_reactions(pool, slug, **_):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, trigger_type, trigger_pattern, response_pattern,
                   intensity, example, tags, weight, created_at
            FROM personality_yoda_reactions
            WHERE profile_slug = $1
            ORDER BY trigger_type, weight DESC
            """,
            slug,
        )
    reactions = [
        {
            "id": str(r['id']),
            "trigger_type": r['trigger_type'],
            "trigger_pattern": r['trigger_pattern'],
            "response_pattern": r['response_pattern'],
            "intensity": r['intensity'],
            "example": r['example'],
            "tags": list(r['tags']) if r['tags'] else [],
            "weight": r['weight'],
            "created_at": r['created_at'].isoformat(),
        }
        for r in rows
    ]
    return {"profile_slug": slug, "count": len(reactions), "reactions": reactions}


async def create_reaction(pool, slug, body=None, **_):
    if not body:
        return {"__status": 400, "detail": "request body required"}
    trigger = (body.get('trigger_pattern') or '').strip()
    response = (body.get('response_pattern') or '').strip()
    if not trigger or not response:
        return {"__status": 400, "detail": "trigger_pattern and response_pattern required"}

    content_hash = hashlib.sha256(f"{trigger}:{response}".encode()).hexdigest()

    tags = body.get('tags', [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(',') if t.strip()]

    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO personality_yoda_reactions
                    (profile_slug, trigger_type, trigger_pattern, response_pattern,
                     intensity, example, tags, weight, content_hash)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id
                """,
                slug,
                body.get('trigger_type', 'criticism'),
                trigger, response,
                body.get('intensity', 'moderate'),
                body.get('example'),
                tags,
                float(body.get('weight', 1.0)),
                content_hash,
            )
            return {"id": str(row['id']), "status": "created"}
        except Exception as e:
            if 'unique' in str(e).lower():
                return {"__status": 409, "detail": "Duplicate reaction"}
            raise


async def delete_reaction(pool, slug, item_id=None, **_):
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM personality_yoda_reactions WHERE id = $1::uuid AND profile_slug = $2",
            item_id, slug,
        )
    if result == "DELETE 0":
        return {"__status": 404, "detail": "Reaction not found"}
    return {"status": "deleted"}


# =============================================================================
# IMPORT (YAML → all 4 tables)
# =============================================================================

async def import_data(pool, slug, body=None, **_):
    if not body:
        return {"__status": 400, "detail": "request body required"}

    yaml_content = body.get('yaml', '')
    if not yaml_content:
        return {"__status": 400, "detail": "yaml field is required"}

    try:
        parsed = yaml.safe_load(yaml_content)
    except Exception as e:
        return {"__status": 400, "detail": f"Invalid YAML: {e}"}

    if not isinstance(parsed, dict):
        return {"__status": 400, "detail": "YAML must be a mapping"}

    stats = {
        "traits_created": 0, "traits_skipped": 0,
        "quotes_created": 0, "quotes_skipped": 0,
        "lexicon_created": 0, "lexicon_skipped": 0,
        "reactions_created": 0, "reactions_skipped": 0,
    }

    async with pool.acquire() as conn:
        # --- Traits ---
        for t in parsed.get('traits', []):
            content = (t.get('content') or '').strip()
            if not content:
                continue
            category = t.get('category', 'identity')
            layer = CATEGORY_LAYERS.get(category, 1)
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            tags = t.get('tags', [])
            examples = t.get('examples', [])
            anti_examples = t.get('anti_examples', [])
            try:
                result = await conn.execute(
                    """
                    INSERT INTO personality_yoda_traits
                        (profile_slug, category, subcategory, layer, content, examples,
                         anti_examples, content_hash, tags, weight, stable, source)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, 'import')
                    ON CONFLICT (profile_slug, content_hash) DO NOTHING
                    """,
                    slug, category, t.get('subcategory'), layer, content,
                    examples, anti_examples, content_hash, tags,
                    float(t.get('weight', 1.0)), bool(t.get('stable', False)),
                )
                if result == "INSERT 0 1":
                    stats["traits_created"] += 1
                else:
                    stats["traits_skipped"] += 1
            except Exception:
                stats["traits_skipped"] += 1

        # --- Quotes ---
        for q in parsed.get('quotes', []):
            quote_text = (q.get('quote') or '').strip()
            if not quote_text:
                continue
            content_hash = hashlib.sha256(quote_text.encode()).hexdigest()
            use_when = q.get('use_when', [])
            tone_tags = q.get('tone_tags', [])
            try:
                result = await conn.execute(
                    """
                    INSERT INTO personality_yoda_quotes
                        (profile_slug, quote, source, context, use_when,
                         paraphrase_ok, tone_tags, weight, content_hash)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (profile_slug, content_hash) DO NOTHING
                    """,
                    slug, quote_text, q.get('source'), q.get('context'),
                    use_when, bool(q.get('paraphrase_ok', True)),
                    tone_tags, float(q.get('weight', 1.0)), content_hash,
                )
                if result == "INSERT 0 1":
                    stats["quotes_created"] += 1
                else:
                    stats["quotes_skipped"] += 1
            except Exception:
                stats["quotes_skipped"] += 1

        # --- Lexicon ---
        for l in parsed.get('lexicon', []):
            word = (l.get('word_or_phrase') or '').strip()
            if not word:
                continue
            content_hash = hashlib.sha256(word.encode()).hexdigest()
            try:
                result = await conn.execute(
                    """
                    INSERT INTO personality_yoda_lexicon
                        (profile_slug, word_or_phrase, usage_type, frequency,
                         context, example, replaces, weight, content_hash)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (profile_slug, content_hash) DO NOTHING
                    """,
                    slug, word,
                    l.get('usage_type', 'favor'),
                    l.get('frequency', 'often'),
                    l.get('context'),
                    l.get('example'),
                    l.get('replaces'),
                    float(l.get('weight', 1.0)),
                    content_hash,
                )
                if result == "INSERT 0 1":
                    stats["lexicon_created"] += 1
                else:
                    stats["lexicon_skipped"] += 1
            except Exception:
                stats["lexicon_skipped"] += 1

        # --- Reactions ---
        for r in parsed.get('reactions', []):
            trigger = (r.get('trigger_pattern') or '').strip()
            response = (r.get('response_pattern') or '').strip()
            if not trigger or not response:
                continue
            content_hash = hashlib.sha256(f"{trigger}:{response}".encode()).hexdigest()
            tags = r.get('tags', [])
            try:
                result = await conn.execute(
                    """
                    INSERT INTO personality_yoda_reactions
                        (profile_slug, trigger_type, trigger_pattern, response_pattern,
                         intensity, example, tags, weight, content_hash)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (profile_slug, content_hash) DO NOTHING
                    """,
                    slug,
                    r.get('trigger_type', 'criticism'),
                    trigger, response,
                    r.get('intensity', 'moderate'),
                    r.get('example'),
                    tags,
                    float(r.get('weight', 1.0)),
                    content_hash,
                )
                if result == "INSERT 0 1":
                    stats["reactions_created"] += 1
                else:
                    stats["reactions_skipped"] += 1
            except Exception:
                stats["reactions_skipped"] += 1

    return stats


# =============================================================================
# ROUTE TABLE
#
# Each entry: (HTTP_METHOD, regex_pattern, handler_function)
# The pattern is matched against the path AFTER stripping the skill prefix.
# Named groups become keyword arguments to the handler.
#
# Example: GET /skill_api/personality_yoda/hal_test/traits
#   → path after strip = "/hal_test/traits"
#   → matches: r"/(?P<slug>[\w-]+)/traits$"
#   → calls: list_traits(pool, slug="hal_test")
# =============================================================================

routes = [
    # Traits
    ("GET",    r"/(?P<slug>[\w-]+)/traits$",                     list_traits),
    ("POST",   r"/(?P<slug>[\w-]+)/traits$",                     create_trait),
    ("DELETE", r"/(?P<slug>[\w-]+)/traits/(?P<item_id>[\w-]+)$", delete_trait),

    # Quotes
    ("GET",    r"/(?P<slug>[\w-]+)/quotes$",                     list_quotes),
    ("POST",   r"/(?P<slug>[\w-]+)/quotes$",                     create_quote),
    ("DELETE", r"/(?P<slug>[\w-]+)/quotes/(?P<item_id>[\w-]+)$", delete_quote),

    # Lexicon
    ("GET",    r"/(?P<slug>[\w-]+)/lexicon$",                     list_lexicon),
    ("POST",   r"/(?P<slug>[\w-]+)/lexicon$",                     create_lexicon),
    ("DELETE", r"/(?P<slug>[\w-]+)/lexicon/(?P<item_id>[\w-]+)$", delete_lexicon),

    # Reactions
    ("GET",    r"/(?P<slug>[\w-]+)/reactions$",                     list_reactions),
    ("POST",   r"/(?P<slug>[\w-]+)/reactions$",                     create_reaction),
    ("DELETE", r"/(?P<slug>[\w-]+)/reactions/(?P<item_id>[\w-]+)$", delete_reaction),

    # Import
    ("POST",   r"/(?P<slug>[\w-]+)/import$",                       import_data),
]
