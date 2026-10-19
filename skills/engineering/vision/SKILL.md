---
name: vision
description: >
  Bridge images to GPT 5.6 Luna via opencode-go when DeepSeek V4 Flash (or any
  text-only model) needs to see a screenshot, photo, diagram, chart, document,
  or UI. Use whenever the user shares an image, asks you to analyze a visual,
  or you need to inspect a screenshot, wireframe, mockup, chart, or image file.
  The bundled CLI is `scripts/vision <image-path> "<question>"`; it routes through
  opencode-go/gpt-5.6-luna by default (override with VISION_MODEL).
allowed-tools:
  - Bash
---

# Vision bridge: DeepSeek V4 Flash (no vision) to GPT 5.6 Luna

You are a text-only agent. When you need to understand an image, you do NOT
guess. You call the vision bridge CLI which sends the image together with your
exact question to a vision-capable model (default `opencode-go/gpt-5.6-luna`, see
Configuration below).

## When to use

- The user attaches or references an image, screenshot, diagram, mockup, chart,
  photo, or document scan.
- You need to inspect UI layout, visual design, colors, spacing, or a rendered
  page.
- You need to read text from a screenshot, extract data from a chart, or check
  an image's visual content.

Do NOT use it for:

- File system operations that don't need vision (use shell tools instead).
- Generating images (use the proper image generation tool).

## How to use

Run:

```bash
${CLAUDE_SKILL_DIR}/scripts/vision <absolute-or-relative-image-path> "<your precise question>"
```

The CLI:

- Resolves the image to an absolute path.
- Converts non-PNG/JPEG inputs (HEIC/HEIF scans d'iPhone, BMP, TIFF) en PNG
  avant l'appel (sips) : un HEIC brut fait halluciner l'analyse sans l'image.
- Calls GPT 5.6 Luna DIRECT via HTTP a un proxy OpenAI-compatible
  (`VISION_BASE_URL`, defaut http://127.0.0.1:10100, base64 data URL), pas
  opencode CLI (single-flight, hang en parallele). Le pool de
  VISION_MAX_PARALLEL slots sert donc vraiment pour plusieurs appels.
- Passes a strong system prompt that makes Luna return an exhaustive,
  structured analysis (text verbatim when relevant, coordinates, colors, CSS
  values, data points, actionable insights).

## Garde-fous (ne pas contourner)

- **Timeout 120s** (variable `VISION_TIMEOUT`). Si le modele bloque, l'appel
  est tue. Ne relance pas en boucle un appel qui traine.
- **Concurrence : pool de `VISION_MAX_PARALLEL` slots** (defaut 1). Les appels
  attendent un slot libre via `shlock` + reclamation des locks stales (PID
  mort). Pool partage avec tout appel vision du systeme (meme
  /tmp/vision.locks/), les appels se limitent mutuellement. Defaut 1 = le
  comportement historique (fan-out = ram sur le Mac le 2026-08-08) ; monter a
  2-3 uniquement quand on sait ce qu'on fait.
- **Exit codes** : `75` = pool sature (tous les slots pris > VISION_LOCK_WAIT,
  reessaie plus tard), `124` = timeout, `1` = image non attachable / fichier
  introuvable. Si tu obtiens une de ces erreurs, corrige la cause (convertis
  l'image, attends, reformule) au lieu de relancer la meme commande.
- **Zero tools** : l'appel HTTP direct donne a Luna aucun acces fichiersysteme,
  c'est un juge visuel pur. Si le prompt pointe vers un fichier ("lis
  bar.md"), Luna ne pourra pas le lire : la barre/criteres DOIVENT etre
  inline dans le prompt.

## Configuration

Defaults keep the original setup (model `opencode-go/gpt-5.6-luna` behind a local
OpenAI-compatible proxy on port 10100). Every default can be overridden with an
environment variable:

| Variable | Default | Meaning |
|---|---|---|
| `VISION_MODEL` | `opencode-go/gpt-5.6-luna` | Model id sent in the `model` field. Must accept images. |
| `VISION_BASE_URL` | `http://127.0.0.1:10100` | Base URL of an OpenAI-compatible server (`/v1/chat/completions`). |
| `VISION_AUTH` | `local` | Bearer token sent to that server (set it if your endpoint checks keys). |
| `VISION_TIMEOUT` | `120` | Seconds before the call is killed (exit 124). |
| `VISION_MAX_PARALLEL` | `1` | Number of concurrent calls allowed. |
| `VISION_LOCK_WAIT` | `60` | Seconds to wait for a free slot before exiting 75. |
| `VISION_USAGE_FILE` | unset | If set, the API `usage` JSON is written to this path. |

Example with another provider: `VISION_BASE_URL=https://api.example.com VISION_AUTH=$KEY VISION_MODEL=my-vision-model ${CLAUDE_SKILL_DIR}/scripts/vision shot.png "..."`.

Requirements: macOS (the script uses `zsh`, `shlock` and `sips`), `python3`, and a reachable
OpenAI-compatible endpoint serving a vision model.

## How to write a good question

Be as specific as if you were asking a human visual expert:

- UI: "Describe the layout, spacing, alignment, colors (hex), typography, and
  interaction states. Propose 3 concrete fixes with exact CSS values."
- Code: "Transcribe every visible line. Quote variable names, function
  signatures, and error messages exactly."
- Chart: "Extract all data points, labels, axes, trends, and outliers.
  Be quantitative."
- Document: "Transcribe every word you can read, preserving formatting."
- Photo: "Describe subjects, composition, lighting, colors, mood, and any
  technical details."
- General: "What is the most important thing I need to know to continue my
  task, and what should I do next?"

## Output handling

- Read the returned analysis carefully.
- Use it to continue your task exactly as if you had seen the image.
- If the analysis is ambiguous, call the CLI again with a narrower or more
  specific question instead of guessing.

