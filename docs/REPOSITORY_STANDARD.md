# Intellectual Estate Repository Standard

This document defines what "finished enough to preserve and hand to another person" means for a major repository in the Rando Young Intellectual Estate.

## Required front-door files

Every major project repository should have:

- `README.md` — purpose, significance, shortest useful path, requirements, status, and navigation.
- `ESTATE_STATUS.md` — one of `READY`, `USABLE BUT INCOMPLETE`, or `ARCHIVAL`, with an explicit explanation.
- `PROJECT_HISTORY.md` — lineage, renamed concepts, superseded designs, and canonical decisions.
- `LICENSE` — when a deliberate license has been selected.
- `CHANGELOG.md` — for repositories that have numbered or public releases.

Do not add a license merely to fill the slot. The license must reflect the owner's actual publication intent.

## Recommended structure

```text
README.md
ESTATE_STATUS.md
PROJECT_HISTORY.md
docs/
src/ or bridge/
firmware/ or endpoints/
hardware/          # when applicable
examples/
validation/
assets/
archive/
```

Projects do not need empty directories. Add a directory when it contains real material.

## Golden-path rule

Each `READY` technical repository must present one shortest reproducible path. The path should answer:

1. What do I need?
2. What do I connect or install?
3. What command or program do I run?
4. What should I observe?
5. How do I know it worked?

Advanced alternatives come after this path, not before it.

## Validation rule

A claim of reproducibility requires evidence. Record:

- date tested;
- hardware and relevant versions;
- operating system/toolchain where relevant;
- exact source revision;
- expected result;
- observed result;
- known deviations or failures.

A historical checksum, screenshot, or old package is useful evidence but does not by itself prove that the current repository is reproducible.

## Source rule

The canonical source required for the golden path should live in the repository itself. Submodules and external repositories may preserve lineage or optional components, but the first reproducible path should not depend on reconstructing undocumented external state.

## Archive rule

Never delete valuable history merely because it is obsolete. Move or identify it as historical. A future reader must be able to distinguish:

- current and recommended;
- tested but superseded;
- experimental;
- archival.

## Naming rule

Prefer descriptive names over unexplained version dumps. When a historical filename must be retained, add an index or explanation that states what it is and whether it is current.

## Documentation rule

Documentation must distinguish facts from plans. Use explicit terms such as:

- **tested** — actually reproduced;
- **implemented** — source exists, but current reproduction may not have been performed;
- **planned** — intended but not implemented;
- **historical** — preserved from an earlier stage.

## Definition of Done

A major repository is estate-ready when:

- [ ] README explains what the project is and why it matters.
- [ ] A new reader can identify the shortest useful path in under a minute.
- [ ] Requirements are explicit.
- [ ] At least one meaningful path has been reproduced from the repository.
- [ ] Current source is editable and present.
- [ ] Installation/build/run instructions are complete enough for another person.
- [ ] Expected successful output is shown or described.
- [ ] Current, experimental, and historical material are distinguishable.
- [ ] Major design decisions and project lineage are documented.
- [ ] Related estate repositories are linked where useful.
- [ ] Readiness status is truthful and current.

## Why this exists

The estate is larger than any one repository. Consistency reduces the amount of interpretation future readers must perform. One well-constructed reference repository establishes the pattern; subsequent repositories should conform to the pattern where it fits rather than invent a new organization each time.