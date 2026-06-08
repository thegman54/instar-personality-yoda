-- Personality Yoda: Core traits table
-- 18 categories across 6 layers for comprehensive voice reproduction.
--
-- Categories:
--   Layer 1 (Foundation):  identity, values, worldview
--   Layer 2 (Expression):  voice, lexicon, tone, emphasis, humor
--   Layer 3 (Strategy):    rhetoric, social, narrative, authority, deflection
--   Layer 4 (Reactive):    reaction, situational
--   Layer 5 (Reference):   signature, quote
--   Layer 6 (Constraints): boundary

CREATE TABLE IF NOT EXISTS personality_yoda_traits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_slug VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN (
        'identity', 'values', 'worldview',
        'voice', 'lexicon', 'tone', 'emphasis', 'humor',
        'rhetoric', 'social', 'narrative', 'authority', 'deflection',
        'reaction', 'situational',
        'signature', 'quote',
        'boundary'
    )),
    subcategory VARCHAR(100),
    layer INT NOT NULL CHECK (layer BETWEEN 1 AND 6),
    content TEXT NOT NULL,
    examples TEXT[] DEFAULT '{}',
    anti_examples TEXT[] DEFAULT '{}',
    content_hash VARCHAR(64) NOT NULL,
    tags TEXT[] DEFAULT '{}',
    weight FLOAT DEFAULT 1.0 CHECK (weight >= 0.0 AND weight <= 1.0),
    stable BOOLEAN DEFAULT FALSE,
    source VARCHAR(255) DEFAULT 'manual',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(profile_slug, content_hash)
);

CREATE INDEX IF NOT EXISTS idx_py_traits_profile_cat
    ON personality_yoda_traits(profile_slug, category);
CREATE INDEX IF NOT EXISTS idx_py_traits_profile_layer
    ON personality_yoda_traits(profile_slug, layer);
CREATE INDEX IF NOT EXISTS idx_py_traits_profile_weight
    ON personality_yoda_traits(profile_slug, weight DESC);
CREATE INDEX IF NOT EXISTS idx_py_traits_tags
    ON personality_yoda_traits USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_py_traits_examples
    ON personality_yoda_traits USING GIN(examples);
