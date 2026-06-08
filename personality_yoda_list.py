"""
personality_yoda_list — list available categories, counts, and data store stats.

Returns a layered overview of all personality data without loading content.
Useful for the bot to understand what dimensions are configured.
"""

import structlog

from ..base import BaseTool, ToolResult
from ..registry import register_tool

log = structlog.get_logger()

LAYER_NAMES = {
    1: 'Foundation', 2: 'Expression', 3: 'Strategy',
    4: 'Reactive', 5: 'Reference', 6: 'Constraints',
}


@register_tool
class PersonalityYodaListTool(BaseTool):
    """List available personality categories and data store counts."""

    @property
    def name(self) -> str:
        return "personality_yoda_list"

    @property
    def description(self) -> str:
        return (
            "List all available personality categories, organized by layer, "
            "with trait counts. Also shows quote library size, lexicon entries, "
            "and reaction pattern counts. Use before personality_yoda_read "
            "to see what's available."
        )

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def credential_keys(self) -> list[str]:
        return []

    async def execute(self, **kwargs) -> ToolResult:
        from ...db import get_pool

        pool = get_pool()
        if not pool:
            return ToolResult.fail("Database not available")

        profile_slug = "default"

        try:
            async with pool.acquire() as conn:
                # Trait counts by layer and category
                trait_rows = await conn.fetch(
                    """
                    SELECT
                        layer, category,
                        COUNT(*) AS total,
                        COUNT(*) FILTER (WHERE stable = TRUE) AS stable_count,
                        COUNT(*) FILTER (WHERE stable = FALSE) AS dynamic_count
                    FROM personality_yoda_traits
                    WHERE profile_slug = $1
                    GROUP BY layer, category
                    ORDER BY layer, category
                    """,
                    profile_slug,
                )

                # Quote count
                quote_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM personality_yoda_quotes WHERE profile_slug = $1",
                    profile_slug,
                )

                # Lexicon counts by usage type
                lex_rows = await conn.fetch(
                    """
                    SELECT usage_type, COUNT(*) AS count
                    FROM personality_yoda_lexicon
                    WHERE profile_slug = $1
                    GROUP BY usage_type
                    ORDER BY usage_type
                    """,
                    profile_slug,
                )

                # Reaction counts by trigger type
                react_rows = await conn.fetch(
                    """
                    SELECT trigger_type, COUNT(*) AS count
                    FROM personality_yoda_reactions
                    WHERE profile_slug = $1
                    GROUP BY trigger_type
                    ORDER BY trigger_type
                    """,
                    profile_slug,
                )

            # Build layered response
            layers = {}
            for row in trait_rows:
                layer_num = row['layer']
                layer_name = LAYER_NAMES.get(layer_num, f"Layer {layer_num}")
                if layer_name not in layers:
                    layers[layer_name] = {"layer": layer_num, "categories": []}
                layers[layer_name]["categories"].append({
                    "category": row['category'],
                    "total": row['total'],
                    "stable": row['stable_count'],
                    "dynamic": row['dynamic_count'],
                })

            total_traits = sum(r['total'] for r in trait_rows)

            return ToolResult.ok({
                "profile": profile_slug,
                "layers": layers,
                "total_traits": total_traits,
                "quotes": quote_count or 0,
                "lexicon": {r['usage_type']: r['count'] for r in lex_rows},
                "lexicon_total": sum(r['count'] for r in lex_rows),
                "reactions": {r['trigger_type']: r['count'] for r in react_rows},
                "reactions_total": sum(r['count'] for r in react_rows),
            })

        except Exception as e:
            log.error("personality_yoda_list_error", error=str(e))
            return ToolResult.fail(f"Failed to list personality data: {e}")
