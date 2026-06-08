-- Personality Yoda: Reactions table
-- Trigger → response pattern mappings for contextual behavior.

CREATE TABLE IF NOT EXISTS personality_yoda_reactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_slug VARCHAR(255) NOT NULL,
    trigger_type VARCHAR(50) NOT NULL CHECK (trigger_type IN (
        'criticism',       -- when someone criticizes or attacks
        'praise',          -- when someone compliments or agrees
        'challenge',       -- when expertise or authority is questioned
        'confusion',       -- when asked something they don't know
        'agreement',       -- when someone aligns with their position
        'betrayal',        -- when an ally turns or is disloyal
        'victory',         -- when they win or are proven right
        'defeat',          -- when they lose or are proven wrong
        'media',           -- when interacting with press/media
        'negotiation',     -- when making deals or bargaining
        'emotional',       -- when the other party is emotional
        'technical'        -- when asked about detailed/technical topics
    )),
    trigger_pattern TEXT NOT NULL,
    response_pattern TEXT NOT NULL,
    intensity VARCHAR(10) DEFAULT 'moderate' CHECK (intensity IN (
        'mild', 'moderate', 'strong', 'extreme'
    )),
    example TEXT,
    tags TEXT[] DEFAULT '{}',
    weight FLOAT DEFAULT 1.0 CHECK (weight >= 0.0 AND weight <= 1.0),
    content_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(profile_slug, content_hash)
);

CREATE INDEX IF NOT EXISTS idx_py_reactions_profile
    ON personality_yoda_reactions(profile_slug);
CREATE INDEX IF NOT EXISTS idx_py_reactions_trigger
    ON personality_yoda_reactions(profile_slug, trigger_type);
CREATE INDEX IF NOT EXISTS idx_py_reactions_intensity
    ON personality_yoda_reactions(profile_slug, intensity);
CREATE INDEX IF NOT EXISTS idx_py_reactions_tags
    ON personality_yoda_reactions USING GIN(tags);
