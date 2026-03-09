# Universal Prompt Formula

Defines the core structure and composition rules for Veo 3.1 prompts.

## Formula Structure

```
[Cinematography] + [Subject] + [Action] + [Context] + [Style & Ambiance]
```

### Element Definitions

```yaml
- element: Cinematography
  role: Defines camera work and shot composition
  required: false
  details: Camera movement, composition, lens/focus
  reference: cinematography.md

- element: Subject
  role: Identifies the protagonist or focal point
  required: true
  format: "noun + state/appearance description"
  bad_example: "a person"
  good_example: "a man standing in a dark alley"

- element: Action
  role: An observable action performed by the subject
  required: true
  constraint: "Emotional descriptions are not understood — only visible, physical actions produce results"
  bad_example: "looks sad"
  good_example: "lowers his head and slowly steps backward"

- element: Context
  role: Environment, background elements, time of day
  required: false
  example: "cluttered office late at night"

- element: Style & Ambiance
  role: Overall aesthetics, mood, lighting
  required: true (at least 1 style)
  constraint: "1–2 clear choices. Conflicting style combinations degrade output quality"
  examples:
    - "Retro aesthetic, shot as if on 1980s color film, slightly grainy"
    - "Film noir style, blue-toned night lighting"
```

## Composition Conventions

1. **Order**: Cinematography → Subject → Action → Context → Style & Ambiance
2. **Separators**: Commas (,) between elements; natural English sentences are also acceptable
3. **Language**: English prompts are optimized for the Veo model
4. **Length**: Specificity and descriptiveness improve results; unnecessary repetition does not

## Required vs Optional Elements

```yaml
required:
  - Subject: "A concrete noun + state/appearance"
  - Action: "An observable, physical action"
  - Style: "At least 1 genre/aesthetic"

optional_quality_boosters:
  - Cinematography: "Camera movement + composition + lens"
  - Context: "Environment, location, time"
  - Mood: "Color tone, lighting atmosphere"
  - Audio: "Dialogue, SFX, ambience"
  - Negative Prompt: "Elements to exclude"
```

## Emotion-to-Action Conversion Rules

Veo understands observable actions, not emotions.

```yaml
- emotion: "looks sad"
  action: "lowers his head and slowly steps backward"
- emotion: "is angry"
  action: "clenches his fist and slams it on the table"
- emotion: "is surprised"
  action: "widens his eyes and takes a step back"
- emotion: "is happy"
  action: "breaks into a wide smile and spreads both arms open"
- emotion: "is nervous"
  action: "taps fingers on the table and glances around"
```

## Writing Negative Prompts

When describing elements to exclude, use **affirmative descriptions of the desired opposite state** rather than negation words.

```yaml
- bad: "no man-made structures"
  good: "a desolate landscape with no buildings or roads"
- bad: "no rain"
  good: "clear sky, dry pavement"
```

## Model Settings

```yaml
resolution:
  - 720p
  - 1080p
aspect_ratio:
  - "16:9"
  - "9:16"
duration:
  - 4s
  - 6s
  - 8s
```

## Complete Prompt Examples

### Example 1: Film Noir

```
Wide shot, a nighttime cityscape, vehicles slowly moving along the road,
film noir style, blue-toned night lighting,
ambient noise: distant traffic sounds.
```

Breakdown:
- Cinematography: Wide shot
- Subject: nighttime cityscape
- Action: vehicles slowly moving along the road
- Context: (embedded in Subject)
- Style & Ambiance: film noir style, blue-toned night lighting
- Audio: ambient noise: distant traffic sounds

### Example 2: Retro Office

```
Medium shot, a tired corporate worker, rubbing his temples in exhaustion,
in front of a bulky 1980s computer in a cluttered office late at night.
The scene is lit by the harsh fluorescent overhead lights and the green glow
of the monochrome monitor. Retro aesthetic, shot as if on 1980s color film,
slightly grainy.
```

Breakdown:
- Cinematography: Medium shot
- Subject: a tired corporate worker
- Action: rubbing his temples in exhaustion
- Context: in front of a bulky 1980s computer in a cluttered office late at night
- Style & Ambiance: Retro aesthetic, shot as if on 1980s color film, slightly grainy
- Mood: harsh fluorescent overhead lights, green glow of the monochrome monitor

### Example 3: Crane Shot + Fantasy

```
Crane shot starting low on a lone hiker and ascending high above,
revealing they are standing on the edge of a colossal, mist-filled canyon at sunrise,
epic fantasy style, awe-inspiring, soft morning light.
```

Breakdown:
- Cinematography: Crane shot starting low ... ascending high above
- Subject: a lone hiker
- Action: standing on the edge of a colossal, mist-filled canyon
- Context: at sunrise
- Style & Ambiance: epic fantasy style, awe-inspiring, soft morning light
