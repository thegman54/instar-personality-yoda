# instar-personality-yoda

A comprehensive personality profile for [Project Instar](https://github.com/thegman54/project-instar) that enables a bot to communicate in the voice and style of Yoda, Grand Master of the Jedi Order.

## Architecture

This personality engine uses **18 trait categories** across **6 layers**, backed by **4 database tables** for different types of personality data:

### Layers

| Layer | Name | Categories | Purpose |
|-------|------|------------|---------|
| 1 | **Foundation** | identity, values, worldview | Core beliefs — always active |
| 2 | **Expression** | voice, lexicon, tone, emphasis, humor | Shapes every response |
| 3 | **Strategy** | rhetoric, social, narrative, authority, deflection | How interactions are conducted |
| 4 | **Reactive** | reaction, situational | Triggered by conversational context |
| 5 | **Reference** | signature, quote | Catchphrases and actual quotes |
| 6 | **Constraints** | boundary | Guardrails and limits |

### Data Stores

| Table | Purpose |
|-------|---------|
| `personality_yoda_traits` | 18-category behavioral traits with examples and anti-examples |
| `personality_yoda_quotes` | Actual quotes with source attribution and usage context |
| `personality_yoda_lexicon` | Vocabulary fingerprint — words to favor, avoid, and use situationally |
| `personality_yoda_reactions` | Trigger-to-response pattern mappings by context |

### Inverted Syntax (OSV)

Yoda's most distinctive feature is **Object-Subject-Verb** sentence structure. The voice traits include detailed inversion rules with three patterns:

1. **Adjective Fronting** — "Dangerous, this path is"
2. **Object Fronting** — "Fear in you, I sense"
3. **Verb Phrase to End** — "Teach him, I cannot"

Target: 60-70% inverted sentences, 30-40% standard for readability.

## Installation

This is a skill package for Project Instar. Upload it via the Admin UI or place it in the skills directory.

```bash
# Clone
git clone https://github.com/thegman54/instar-personality-yoda.git

# Import seed data via admin panel YAML import
# or load directly into the database
```

## Tools

| Tool | Purpose |
|------|---------|
| `personality_yoda_read` | Load traits, quotes, lexicon, and reactions by category and situation |
| `personality_yoda_list` | List available categories, counts, and data store stats |

## Seed Data

`data/yoda_profile.yaml` contains a comprehensive starter profile with:
- 60+ traits across all 18 categories with detailed OSV syntax inversion rules
- 16 actual quotes with source attribution and usage context
- 40+ lexicon entries (favored words, avoided words, signatures, dismissals)
- 14 reaction patterns covering criticism, praise, challenges, teaching, and more

## License

MIT
