# Premium pack sources — authoring notes (NOT shipped in the pack)

`tools/keygen.py build-pack` packs `modules/*.md` (sorted by filename) into the
encrypted premium pack as `{"modules":[{"file","body"}, ...]}`. The course app
indexes premium bodies by manifest order: `course-04` = pack index 0 …
`course-46` = pack index 42. Filenames must stay zero-padded and sequential —
renumbering breaks the index mapping.

## Module body format (plain text, one template for every module)

```
<Module title>                      (line 1 — the app strips it; the h2 shows it)
MODULE OVERVIEW                     (must be line 2 — the app detects it)
Level: … | Time: …
Prerequisites: …
LEARNING OBJECTIVES
After this module you can:
- …
LESSON 1 — <TITLE>                  (instruction + CASE BREAKDOWN + checklist + COMMON MISTAKE)
LESSON 2 — <TITLE>                  (same)
HANDS-ON EXERCISE                   (scenario, 3 decision points, correct path)
KNOWLEDGE CHECK
[CHECK] blocks ×3                   (format below)
KEY TAKEAWAYS
GLOSSARY
FURTHER READING                     (stable official sources only)
CERTIFICATION ALIGNMENT             (certs + objective domains + honesty sentence)
```

`[CHECK]` block (parsed by the course app into an interactive check;
without JS the raw block still reads fine):

```
[CHECK]
Q: …
A: …
B: …
C: …
ANSWER: <letter>
FEEDBACK: …
[/CHECK]
```

## Rules

- Plain language, procedures and decision points — no filler, no invented
  statistics, no absolute claims.
- Certification alignment is honest: the course teaches knowledge domains;
  it confers no certification or license. Hands-on / state-issued
  credentials are pathways content only.
- The owner's older local premium sources (game scenarios + 16 short
  modules) are superseded by this directory. The removed game remains
  recoverable in git history.
