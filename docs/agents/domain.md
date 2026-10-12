# Domain documentation

How engineering agents consume this repository's domain glossary and architecture decisions.

## Before exploring

Read:

- `GLOSSARY.md` at the repository root, if it exists.
- Relevant ADRs under `docs/adr/`, if they exist.

If these files do not exist, proceed without creating placeholders or suggesting them upfront. The `domain-modeling` skill creates them when a domain term or architectural decision is actually established.

## File structure

This repository has one context:

```text
/
├── GLOSSARY.md
├── docs/
│   ├── agents/
│   └── adr/
└── plugins/
```

## Vocabulary rules

When naming a domain concept in an issue, proposal, refactor, hypothesis, or test, use the term defined in `GLOSSARY.md`, including its avoided synonyms. If a concept is not defined, reconsider inventing a synonym and record any real gap through the domain-modeling process.

## ADR conflicts

If proposed work contradicts an existing ADR, identify the decision and explain why it should be reopened instead of silently overriding it.
