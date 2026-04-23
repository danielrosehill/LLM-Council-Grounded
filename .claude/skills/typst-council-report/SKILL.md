---
name: typst-council-report
description: Render an LLM council result (JSON produced by any LLM-Council-* backend) into a typeset PDF via Typst. Use when the user wants to regenerate a PDF from an existing council run, style the report differently, or produce a PDF from a council result that was captured as JSON. Handles Typst installation checks, template resolution, and compilation.
---

# Typst Council Report

Render a council run to a typeset PDF. This skill is reused across every `LLM-Council-*` repo in the family — each repo ships its own `templates/report.typ`, and the council backend writes a `data.json` alongside it. This skill compiles the pair.

## Preconditions

1. **Typst must be installed.** Check with `typst --version`. If missing:
   - Linux/macOS: install via `cargo install --locked typst-cli` or a package manager (`apt`, `brew`, `nix`).
   - Do **not** attempt to install for the user without asking.
2. **A council result must exist.** Either:
   - A directory `out/<timestamp>/` containing `data.json` and `report.typ` (produced by the backend).
   - Or a raw council-result JSON file the user provides, which you will pair with the repo's `templates/report.typ`.

## Inputs

Accept any of:

- A path to an `out/<timestamp>/` directory → compile `report.typ` inside it.
- A path to a `data.json` file + (optional) path to a `.typ` template → assemble into a fresh output dir and compile.
- Nothing → pick the **most recent** `out/*/` in the current repo.

## Pipeline

1. Resolve inputs to a working directory containing `data.json` and `report.typ`.
2. Validate `data.json` parses and has the keys the template expects. The common council schema is:
   ```json
   {
     "brief": "...",
     "context": { ... },
     "dossier": "..."       /* or "search_spec", "synthesis" — repo-specific */,
     "analyses" | "opinions": [ { ... } ],
     "reviews": [ { ... } ]
   }
   ```
   If the template references a key that the JSON does not provide, surface the specific mismatch to the user before compiling (Typst errors are less readable).
3. Run: `typst compile <path>/report.typ <path>/report.pdf`.
4. On success: print the absolute PDF path and offer to open it (`xdg-open` / `open` / VS Code) **only if the user asks**.
5. On failure: pipe the Typst error back to the user. Common causes:
   - Missing font (`New Computer Modern`) → the template in these repos falls back gracefully on most systems; if not, suggest `set text(font: "Latin Modern Roman")`.
   - Stale `data.json` (e.g., old schema) → re-run the council.

## Styling changes

If the user wants a different look (fonts, colours, paper size, logo), edit `templates/report.typ` in the repo — it is a straightforward Typst document. Do not special-case styling inside this skill; keep the skill purely mechanical.

## Schema hints per repo

Different repos put the Chairman's output under different keys. Quick reference:

| Repo | Chairman key |
|---|---|
| `LLM-Council-Decide` | `dossier` |
| `LLM-Council-Homehunter` | `search_spec` |
| `LLM-Council-V3` | `report` |
| `LLM-Council-Grounded` | `synthesis` |
| `Hypothesis-Council` | `verdict` |
| `LLM-Council-Template` | `synthesis` |

If the active repo uses a different key, read its `templates/report.typ` to see which top-level JSON key it references and adapt.

## Out of scope

- Do not run the council itself — that is the `start-*-council` skill's job. This skill only renders.
- Do not modify the Typst template unless the user explicitly asks for a styling change.
