"""
personality_yoda_read — retrieve personality data across all four stores.

Queries traits (18 categories, 6 layers), quotes, lexicon, and reactions.
Returns a unified personality payload for the bot to adopt. Non-stable traits
decay at ~5% per day based on updated_at.
"""

import structlog

from ..base import BaseTool, ToolResult
from ..registry import register_tool

log = structlog.get_logger()

# Category → layer mapping
CATEGORY_LAYERS = {
    'identity': 1, 'values': 1, 'worldview': 1,
    'voice': 2, 'lexicon': 2, 'tone': 2, 'emphasis': 2, 'humor': 2,
    'rhetoric': 3, 'social': 3, 'narrative': 3, 'authority': 3, 'deflection': 3,
    'reaction': 4, 'situational': 4,
    'signature': 5, 'quote': 5,
    'boundary': 6,
}

LAYER_NAMES = {
    1: 'Foundation', 2: 'Expression', 3: 'Strategy',
    4: 'Reactive', 5: 'Reference', 6: 'Constraints',
}


@register_tool
class PersonalityYodaReadTool(BaseTool):
    """Load Yoda personality traits, quotes, lexicon, and reactions."""

    @property
    def name(self) -> str:
        return "personality_yoda_read"

    @property
    def description(self) -> str:
        return (
            "Load Yoda personality data for the given categories. "
            "18 categories across 6 layers: "
            "Foundation (identity, values, worldview), "
            "Expression (voice, lexicon, tone, emphasis, humor), "
            "Strategy (rhetoric, social, narrative, authority, deflection), "
            "Reactive (reaction, situational), "
            "Reference (signature, quote), "
            "Constraints (boundary). "
            "Always load identity,values,worldview,voice,tone,emphasis at minimum. "
            "Add other categories based on conversational context. "
            "Optionally include quotes, lexicon, and reaction data."
        )

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "categories": {
                    "type": "string",
                    "description": (
                        "Comma-separated category names. "
                        "Options: identity, values, worldview, voice, lexicon, tone, "
                        "emphasis, humor, rhetoric, social, narrative, authority, "
                        "deflection, reaction, situational, signature, quote, boundary"
                    ),
                },
                "situation": {
                    "type": "string",
                    "description": (
                        "Optional comma-separated context tags for filtering. "
                        "Examples: 'negotiation,business' or 'attack,defense' or 'rally,crowd'"
                    ),
                },
                "include_quotes": {
                    "type": "boolean",
                    "description": "Include relevant quotes from the quote library. Default false.",
                    "default": False,
                },
                "include_lexicon": {
                    "type": "boolean",
                    "description": "Include vocabulary guidance (words to favor/avoid). Default false.",
                    "default": False,
                },
                "include_reactions": {
                    "type": "boolean",
                    "description": "Include trigger→response reaction patterns. Default false.",
                    "default": False,
                },
                "limit": {
                    "type": "integer",
                    "description": "Max non-stable traits per category. Default 10.",
                    "default": 10,
                },
            },
            "required": ["categories"],
        }

    def credential_keys(self) -> list[str]:
        return []

    async def execute(
        self,
        categories: str = "",
        situation: str = "",
        include_quotes: bool = False,
        include_lexicon: bool = False,
        include_reactions: bool = False,
        limit: int = 10,
        **kwargs,
    ) -> ToolResult:
        from ...db import get_pool

        pool = get_pool()
        if not pool:
            return ToolResult.fail("Database not available")

        profile_slug = "default"
        cat_list = [c.strip() for c in categories.split(",") if c.strip()]
        tags = [t.strip() for t in situation.split(",") if t.strip()] if situation else []

        if not cat_list:
            return ToolResult.fail("No categories specified.")

        # Validate categories
        invalid = [c for c in cat_list if c not in CATEGORY_LAYERS]
        if invalid:
            return ToolResult.fail(
                f"Unknown categories: {', '.join(invalid)}. "
                f"Valid: {', '.join(sorted(CATEGORY_LAYERS.keys()))}"
            )

        log.info("personality_yoda_read",
                 profile=profile_slug, categories=cat_list, tags=tags)

        try:
            async with pool.acquire() as conn:
                # --- Traits ---
                if tags:
                    trait_rows = await conn.fetch(
                        """
                        SELECT category, layer, content, examples, anti_examples, stable,
                            weight * POWER(0.95, EXTRACT(EPOCH FROM (NOW() - updated_at)) / 86400.0)
                            AS effective_weight
                        FROM personality_yoda_traits
                        WHERE profile_slug = $1
                          AND category = ANY($2::text[])
                          AND (stable = TRUE OR tags && $3::text[])
                        ORDER BY layer, category, effective_weight DESC
                        """,
                        profile_slug, cat_list, tags,
                    )
                else:
                    trait_rows = await conn.fetch(
                        """
                        SELECT category, layer, content, examples, anti_examples, stable,
                            weight * POWER(0.95, EXTRACT(EPOCH FROM (NOW() - updated_at)) / 86400.0)
                            AS effective_weight
                        FROM personality_yoda_traits
                        WHERE profile_slug = $1
                          AND category = ANY($2::text[])
                        ORDER BY layer, category, effective_weight DESC
                        """,
                        profile_slug, cat_list,
                    )

                # Group by category, limit non-stable
                traits = {}
                counts = {}
                for row in trait_rows:
                    cat = row['category']
                    entry = {"content": row['content']}
                    if row['examples']:
                        entry["examples"] = list(row['examples'])
                    if row['anti_examples']:
                        entry["anti_examples"] = list(row['anti_examples'])

                    if row['stable']:
                        traits.setdefault(cat, []).append(entry)
                    else:
                        counts.setdefault(cat, 0)
                        if counts[cat] < limit:
                            traits.setdefault(cat, []).append(entry)
                            counts[cat] += 1

                result = {
                    "profile": profile_slug,
                    "categories_requested": cat_list,
                    "trait_count": sum(len(v) for v in traits.values()),
                    "traits": traits,
                }

                # --- Quotes ---
                if include_quotes:
                    if tags:
                        quote_rows = await conn.fetch(
                            """
                            SELECT quote, source, context, paraphrase_ok, tone_tags
                            FROM personality_yoda_quotes
                            WHERE profile_slug = $1
                              AND use_when && $2::text[]
                            ORDER BY weight DESC
                            LIMIT 10
                            """,
                            profile_slug, tags,
                        )
                    else:
                        quote_rows = await conn.fetch(
                            """
                            SELECT quote, source, context, paraphrase_ok, tone_tags
                            FROM personality_yoda_quotes
                            WHERE profile_slug = $1
                            ORDER BY weight DESC
                            LIMIT 10
                            """,
                            profile_slug,
                        )

                    result["quotes"] = [
                        {
                            "quote": r['quote'],
                            "source": r['source'],
                            "context": r['context'],
                            "paraphrase_ok": r['paraphrase_ok'],
                        }
                        for r in quote_rows
                    ]

                # --- Lexicon ---
                if include_lexicon:
                    lex_rows = await conn.fetch(
                        """
                        SELECT word_or_phrase, usage_type, frequency, context, example, replaces
                        FROM personality_yoda_lexicon
                        WHERE profile_slug = $1
                        ORDER BY usage_type, weight DESC
                        """,
                        profile_slug,
                    )

                    lexicon = {}
                    for r in lex_rows:
                        utype = r['usage_type']
                        entry = {"word": r['word_or_phrase'], "frequency": r['frequency']}
                        if r['context']:
                            entry["context"] = r['context']
                        if r['example']:
                            entry["example"] = r['example']
                        if r['replaces']:
                            entry["replaces"] = r['replaces']
                        lexicon.setdefault(utype, []).append(entry)

                    result["lexicon"] = lexicon

                # --- Reactions ---
                if include_reactions:
                    if tags:
                        react_rows = await conn.fetch(
                            """
                            SELECT trigger_type, trigger_pattern, response_pattern,
                                   intensity, example
                            FROM personality_yoda_reactions
                            WHERE profile_slug = $1
                              AND tags && $2::text[]
                            ORDER BY weight DESC
                            """,
                            profile_slug, tags,
                        )
                    else:
                        react_rows = await conn.fetch(
                            """
                            SELECT trigger_type, trigger_pattern, response_pattern,
                                   intensity, example
                            FROM personality_yoda_reactions
                            WHERE profile_slug = $1
                            ORDER BY trigger_type, weight DESC
                            """,
                            profile_slug,
                        )

                    reactions = {}
                    for r in react_rows:
                        ttype = r['trigger_type']
                        reactions.setdefault(ttype, []).append({
                            "trigger": r['trigger_pattern'],
                            "response": r['response_pattern'],
                            "intensity": r['intensity'],
                            "example": r['example'],
                        })

                    result["reactions"] = reactions

            # Log activity — full payload so cockpit can show what was returned
            try:
                from ...db import log_tool_activity

                # Build detail with the full returned data
                detail = {
                    "categories": cat_list,
                    "situation": situation or None,
                    "trait_count": result['trait_count'],
                    "traits": {
                        cat: [t["content"] for t in entries]
                        for cat, entries in traits.items()
                    },
                }
                if "quotes" in result:
                    detail["quotes"] = [
                        {"quote": q["quote"][:120], "source": q.get("source")}
                        for q in result["quotes"]
                    ]
                if "lexicon" in result:
                    detail["lexicon"] = {
                        utype: [e["word"] for e in entries]
                        for utype, entries in result["lexicon"].items()
                    }
                if "reactions" in result:
                    detail["reactions"] = {
                        ttype: [r["trigger"] for r in entries]
                        for ttype, entries in result["reactions"].items()
                    }

                parts = [f"{result['trait_count']} traits"]
                if "quotes" in result:
                    parts.append(f"{len(result['quotes'])} quotes")
                if "lexicon" in result:
                    parts.append(f"{sum(len(v) for v in result['lexicon'].values())} words")
                if "reactions" in result:
                    parts.append(f"{sum(len(v) for v in result['reactions'].values())} reactions")

                await log_tool_activity(
                    tool_name="personality_yoda_read",
                    summary=f"Loaded {', '.join(parts)} for: {', '.join(cat_list)}",
                    detail=detail,
                    profile_slug=profile_slug,
                    session_id=getattr(self, '_session_id', None),
                )
            except Exception:
                pass

            return ToolResult.ok(result)

        except Exception as e:
            log.error("personality_yoda_read_error", error=str(e))
            return ToolResult.fail(f"Failed to read personality: {e}")
