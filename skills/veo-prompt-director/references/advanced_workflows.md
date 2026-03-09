# Advanced Workflows

Defines advanced creative workflows for Veo 3.1. Goes beyond single-prompt generation to support multi-step production pipelines.

## Table of Contents

- [Timestamp Prompting](#timestamp-prompting)
- [First and Last Frame](#first-and-last-frame)
- [Ingredients to Video](#ingredients-to-video)
- [Image to Video](#image-to-video)
- [Prompt Enhancement with Gemini](#prompt-enhancement-with-gemini)

## Timestamp Prompting

Specify different shots at distinct timecodes within a single generation to create a multi-shot sequence.

### Format

```
[HH:MM-HH:MM] {shot_description}
```

### Format Constraints

1. Segments fall within the video duration (4 / 6 / 8 seconds)
2. Each segment has its own independent Cinematography + Subject + Action
3. Time segments do not overlap
4. Audio/SFX can be specified per segment

### Example

```
[00:00-00:02] Medium shot from behind a young female explorer with a leather
satchel and messy brown hair in a ponytail, as she pushes aside a large
jungle vine to reveal a hidden path.

[00:02-00:04] Reverse shot of the explorer's freckled face, her expression
filled with awe as she gazes upon ancient, moss-covered ruins in the
background. SFX: The rustle of dense leaves, distant exotic bird calls.

[00:04-00:06] Tracking shot following the explorer as she steps into the
clearing and runs her hand over the intricate carvings on a crumbling
stone wall. Emotion: Wonder and reverence.

[00:06-00:08] Wide, high-angle crane shot, revealing the lone explorer
standing small in the center of the vast, forgotten temple complex,
half-swallowed by the jungle. SFX: A swelling, gentle orchestral score
begins to play.
```

## First and Last Frame

Generates a smooth video transition between a starting image and an ending image.

### Workflow

```yaml
step_1:
  tool: Gemini 2.5 Flash Image
  action: Generate the first frame image
  example_prompt: >
    Medium shot of a female pop star singing passionately into a vintage
    microphone. She is on a dark stage, lit by a single, dramatic spotlight
    from the front. Photorealistic, cinematic.

step_2:
  tool: Gemini 2.5 Flash Image
  action: Generate the last frame image
  example_prompt: >
    POV shot from behind the singer on stage, looking out at a large,
    cheering crowd. The stage lights are bright, creating lens flare.
    Energetic atmosphere.

step_3:
  tool: Veo 3.1 (First and Last Frame feature)
  action: Provide both images + write a transition prompt
  example_prompt: >
    The camera performs a smooth 180-degree arc shot, starting with the
    front-facing view of the singer and circling around her to seamlessly
    end on the POV shot from behind her on stage. The singer sings
    "when you look me in the eyes, I can see a million stars."
```

### Key Writing Points

- Describe the transition movement in detail (arc shot, dolly, pan, etc.)
- Clearly define the camera path from start to end
- Audio can be specified alongside the transition

## Ingredients to Video

Supply reference images (characters, objects, backgrounds) to generate multi-shot scenes with a consistent aesthetic.

### Workflow

```yaml
step_1:
  tool: Gemini 2.5 Flash Image
  action: Generate reference images for characters / backgrounds / objects
  outputs:
    - "Character A reference image"
    - "Character B reference image"
    - "Background / set reference image"

step_2:
  tool: Veo 3.1 (Ingredients to Video feature)
  action: Generate scenes using reference images + prompt
  prompt_format: >
    Using the provided images for {character_A}, {character_B}, and
    {setting}, create a {shot_type} of {action_description}.
    {dialogue_or_audio}
```

### Prompt Examples

**Shot 1:**
```
Using the provided images for the detective, the woman, and the office
setting, create a medium shot of the detective behind his desk. He looks
up at the woman and says in a weary voice, "Of all the offices in this
town, you had to walk into mine."
```

**Shot 2:**
```
Using the provided images for the detective, the woman, and the office
setting, create a shot focusing on the woman. A slight, mysterious smile
plays on her lips as she replies, "You were highly recommended."
```

### Use Cases

- Multi-shot dialogue scenes (maintaining character consistency)
- Ad series (consistent product/brand visuals)
- Storyboard-based sequence production

## Image to Video

Animates a single source image into video.

### Characteristics

- Input: 1 source image + a prompt describing the desired motion/transition
- Veo 3.1 has improved prompt adherence and audio-visual quality over previous versions
- Motion is added while preserving the original image's composition and style

## Prompt Enhancement with Gemini

Gemini analyzes and enriches a simple prompt, expanding it into a more descriptive, cinematic version.

### Pipeline

1. Simple idea as input
2. Gemini enhances with cinematic language
3. Enhanced prompt feeds into Veo 3.1

### Example

**User input**: "A person walking alone on a rainy night"

**Gemini-enhanced result**:
```
Dolly shot slowly following a lone figure in a dark overcoat, walking
down a rain-slicked city street at night. Shallow depth of field keeps
the figure sharp against the bokeh of neon reflections on wet asphalt.
Neo-noir style, moody blue and orange tones.
Ambient noise: steady rain, distant car tires on wet road.
```
