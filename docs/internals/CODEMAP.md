# Code map

[`codemap/`](codemap/index.json) is a generated, machine-readable map of
`ux_valio`, one JSON shard per module: layers, imports, symbols, the public
API, features and the domain charter. CI fails when it is stale or when the
map has a problem.

[`scripts/codemap.py`](../../scripts/codemap.py) is vendored byte-identical
from ux-dom; `index.json` records its version and sha256. The full reference
(fields, config keys, checks) is ux-dom's
[CODEMAP.md](https://github.com/bitplorer/ux-dom/blob/main/docs/internals/CODEMAP.md).

## Rule

A PR updates the map in the same change as the code:

```console
git add <new files>                      # consumers are read from tracked files
python scripts/codemap.py --write-changed
python scripts/codemap.py --check
```

## What is curated here

| File | Content |
|---|---|
| `[tool.codemap]` in [pyproject.toml](../../pyproject.toml) | The [Layering](../explanation/layering.md) import graph as layers and rules |
| [features.toml](features.toml) | Features → modules, symbols, tests, docs |
| [domain.toml](domain.toml) | What this library owns, its public API, non-goals, and the exact phonenumbers / native / mypy names it may use |

Each named identity module is its own layer, so an import from one named
module into a sibling (`india.gst` into `india.kyc`, `contact` into
`portal`) fails `--check`, as does any import from a lower layer into a
higher one.
