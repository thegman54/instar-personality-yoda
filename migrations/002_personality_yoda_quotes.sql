-- Personality Yoda: Quotes table
-- Actual quotes with rich context for when/how to reference or paraphrase them.

CREATE TABLE IF NOT EXISTS personality_yoda_quotes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_slug VARCHAR(255) NOT NULL,
    quote TEXT NOT NULL,
    source VARCHAR(255),
    source_date DATE,
    context TEXT,
    use_when TEXT[] DEFAULT '{}',
    paraphrase_ok BOOLEAN DEFAULT TRUE,
    tone_tags TEXT[] DEFAULT '{}',
    weight FLOAT DEFAULT 1.0 CHECK (weight >= 0.0 AND weight <= 1.0),
    content_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(profile_slug, content_hash)
);

CREATE INDEX IF NOT EXISTS idx_py_quotes_profile
    ON personality_yoda_quotes(profile_slug);
CREATE INDEX IF NOT EXISTS idx_py_quotes_use_when
    ON personality_yoda_quotes USING GIN(use_when);
CREATE INDEX IF NOT EXISTS idx_py_quotes_tone
    ON personality_yoda_quotes USING GIN(tone_tags);
