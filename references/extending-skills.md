# Extending the Framework with External Skills

The bundle ships a fixed set of built-in specialists under [skills/](../skills/). This document explains how to add external (third-party or project-local) specialists without forking the framework, and how the loader keeps the bundle stable when an extension misbehaves.

## Where Extensions Live

External specialists are installed as directories under [extensions/](../extensions/):

```text
extensions/
└── <skill-name>/
    ├── SKILL.md          # required; same contract as a built-in entry
    └── references/       # optional local method documents
```

Install by cloning, copying, or symlinking a skill directory there:

```bash
git clone <skill-repo> extensions/<skill-name>
python3 scripts/research.py validate
python3 scripts/research.py skills
```

`git pull` inside the directory updates it. The directory name must match the `name` field in `SKILL.md`.

## The Extension Contract

An extension is held to the same standard as a built-in entry. Its `SKILL.md` must provide:

- frontmatter with single-line `name` (matching the directory) and `description`;
- the five specialist sections: `## Inputs`, `## Method`, `## Outputs`, `## Checks`, `## Boundary`;
- the boundary phrases `Return to the core` and `Do not dispatch`;
- links that stay inside the extension's own directory.

An extension must not read or write outside its assignment, select models, dispatch other skills, or modify global research state. If it needs a capability the assignment does not grant, it returns a blocker to the core like any built-in specialist.

## How the Loader Keeps the Bundle Stable

- **Built-ins win.** A name collision between `skills/<name>` and `extensions/<name>` is resolved in favor of the built-in entry; the extension stays unused and `validate` reports a shadowing note.
- **Broken extensions degrade to warnings.** Missing frontmatter, wrong sections, broken links, or oversized entries produce `NOTE:`-prefixed advisory lines from `validate` and `skills`. They never crash the framework and never invalidate the built-in bundle.
- **Absence is normal.** `extensions/` may be empty or missing entirely; every command works without it.
- **No registry.** Extensions are discovered from disk on every run; there is no registration file to edit and no cache to invalidate.

## Using an Extension in Research

Select it by name as the task skill, exactly like a built-in entry:

```bash
python3 scripts/research.py task --project ./projects/study --task t9 \
  --objective "..." --activity analysis --skill <skill-name> --role analyst --acceptance "..."
```

If the extension is missing or invalid, task creation fails with `Missing direct skill: <name>` - a blocker to fix by installing or repairing the extension, never a reason to let another skill impersonate it.

## Removing an Extension

Delete or move the directory; nothing else references it. `validate` stops listing it on the next run.
