# Domain documentation

This directory explains how engineering agents consume the domain glossary and architecture decisions.

## Before exploring

Read:

- `CONTEXT.md` at the repository root, if it exists.
- Relevant ADRs under `docs/adr/`, if they exist.

If these files do not exist, proceed without creating placeholders. Create them only when a domain term or architectural decision is actually established.

## File structure

This repository has one context:

```text
/
├── CONTEXT.md
├── docs/
│   ├── agents/
│   └── adr/
└── plugins/
```

## Vocabulary rules

When naming a domain concept in an issue, proposal, refactor, or test, use the term defined in `CONTEXT.md`. If a concept is not defined, reconsider inventing a synonym and record the gap through the domain-modeling process.

## ADR conflicts

If proposed work contradicts an existing ADR, surface the conflict explicitly instead of silently overriding the decision.
