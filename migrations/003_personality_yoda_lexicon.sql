-- Personality Yoda: Lexicon table
-- Vocabulary fingerprint — words/phrases to favor, avoid, or use situationally.

CREATE TABLE IF NOT EXISTS personality_yoda_lexicon (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_slug VARCHAR(255) NOT NULL,
    word_or_phrase VARCHAR(255) NOT NULL,
    usage_type VARCHAR(30) NOT NULL CHECK (usage_type IN (
        'favor',           -- use this word/phrase often
        'avoid',           -- never use this word/phrase
        'signature',       -- trademark expression
        'filler',          -- verbal tic, pause word
        'intensifier',     -- amplification word
        'dismissal',       -- how they shut things down
        'nickname',        -- labels for people/things
        'superlative',     -- how they express extremes
        'transition'       -- how they connect thoughts
    )),
    frequency VARCHAR(20) DEFAULT 'often' CHECK (frequency IN (
        'always', 'often', 'sometimes', 'when_emotional', 'when_attacking', 'rare'
    )),
    context TEXT,
    example TEXT,
    replaces VARCHAR(255),
    weight FLOAT DEFAULT 1.0 CHECK (weight >= 0.0 AND weight <= 1.0),
    content_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(profile_slug, content_hash)
);

CREATE INDEX IF NOT EXISTS idx_py_lexicon_profile
    ON personality_yoda_lexicon(profile_slug);
CREATE INDEX IF NOT EXISTS idx_py_lexicon_type
    ON personality_yoda_lexicon(profile_slug, usage_type);
CREATE INDEX IF NOT EXISTS idx_py_lexicon_freq
    ON personality_yoda_lexicon(profile_slug, frequency);
