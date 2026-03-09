---
name: veo-prompt-director
description: Generates structured Google Veo 3.1 video prompts by collecting user input for subject, action, style, cinematography, and audio. Guides users through the Universal Prompt Formula to produce camera-ready prompts. Use when creating Veo video prompts or when the user mentions Veo, video generation, or cinematic prompts.
---

# Veo Prompt Director

Domain knowledge for generating Google Veo 3.1 video prompts based on the Universal Prompt Formula.

## Prompt Input Elements

### Required Elements

| Element | Description | Example |
|---------|-------------|--------|
| **Subject** | The main subject. Noun + state/appearance combination | "a man standing in a dark alley" |
| **Action** | An observable, physical action performed by the subject. Emotions are not actions | "lowers his head and slowly steps backward" |
| **Style** | The overall tone/genre. 1–2 clear, non-conflicting choices | "film noir", "retro aesthetic" |

### Optional Elements (Quality Enhancers)

| Element | Description | Example |
|---------|-------------|--------|
| **Cinematography** | Camera movement + composition + lens/focus | "dolly shot, close-up, shallow focus" |
| **Context** | Location, time of day, background elements | "a rainy city alley at night" |
| **Mood** | Color tone, lighting, atmosphere | "blue-toned night lighting" |
| **Audio** | Dialogue, sound effects, ambient noise | See [audio_directing.md](references/audio_directing.md) |
| **Duration** | Clip length | 4s, 6s, 8s |
| **Aspect Ratio** | Frame orientation | 16:9 (landscape), 9:16 (portrait) |
| **Negative Prompt** | Elements to exclude (use affirmative descriptions of the desired opposite) | "clear sky, dry pavement" |

### Input Characteristics

- A valid prompt requires all three required elements (Subject, Action, Style)
- Emotional descriptions ("looks sad") are not understood by Veo — the equivalent observable action is needed ("lowers his head and slowly steps backward"). See emotion-to-action table in [prompt_formula.md](references/prompt_formula.md)
- Conflicting style combinations (e.g., "film noir" + "bright cartoon") degrade output quality
- Optional elements default to model inference when omitted

## Prompt Assembly

**Formula**: `[Cinematography] + [Subject] + [Action] + [Context] + [Style & Ambiance]`

Full spec, composition rules, and examples → [prompt_formula.md](references/prompt_formula.md)

## Output Format

A generated prompt consists of:

```yaml
components:
  - settings: "{duration} | {aspect_ratio} | {resolution}"
  - prompt: "assembled prompt string following the Universal Prompt Formula"
  - negative_prompt: "optional — affirmative descriptions of elements to exclude"
  - checklist: "per-element confirmation of which elements are included"
```

## Platform Constraints

```yaml
safety_filter:
  scope: "Applies to both generated video and uploaded images"
  mechanism: "Uses the same safety filters as the Gemini family"
  effect: "Prompts violating policy produce no output — the video is not generated"
  guidance: "Action/state/environment descriptions produce stable results; provocative language triggers blocking"

digital_watermark:
  technology: SynthID
  scope: "All Veo-generated videos are automatically watermarked"
  purpose: "Indicates the content is AI-generated"
```

## Technical References

- **[prompt_formula.md](references/prompt_formula.md)**: Universal Prompt Formula structure, composition rules, emotion-to-action table, negative prompt patterns, and model settings
- **[cinematography.md](references/cinematography.md)**: Camera movements, composition types, lens/focus effects, and Veo-specific notes
- **[audio_directing.md](references/audio_directing.md)**: Dialogue, sound effects, and ambient noise — formats and combination patterns
- **[advanced_workflows.md](references/advanced_workflows.md)**: Timestamp prompting, First/Last Frame, Ingredients to Video, Image to Video, and Prompt Enhancement with Gemini
