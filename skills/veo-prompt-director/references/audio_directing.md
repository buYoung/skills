# Audio Directing Guide

Defines how to write audio prompts — one of Veo 3.1's key differentiators. Veo 3.1 generates video and audio simultaneously.

## Three Audio Element Types

```yaml
- type: Dialogue
  description: Lines spoken by characters
  format: "Wrap dialogue in quotes + describe tone/delivery"
  examples:
    - 'A woman says, "We have to leave now."'
    - 'He mutters, "This must be the key."'
    - 'He says in a weary voice, "Of all the offices in this town, you had to walk into mine."'
    - 'A slight, mysterious smile plays on her lips as she replies, "You were highly recommended."'
    - 'The singer sings "when you look me in the eyes, I can see a million stars."'

- type: Sound Effects (SFX)
  description: Sounds tied to specific events
  format: "'SFX:' prefix + specific sound description"
  examples:
    - "SFX: thunder cracks in the distance"
    - "SFX: tires screeching loudly"
    - "SFX: glass shattering"
    - "SFX: The rustle of dense leaves, distant exotic bird calls"
    - "SFX: A swelling, gentle orchestral score begins to play"

- type: Ambient Noise
  description: Continuous background sounds that fill the scene
  format: "'Ambient noise:' prefix + environmental sound description"
  examples:
    - "Ambient noise: the quiet hum of a starship bridge"
    - "Ambient noise: distant city traffic"
    - "Ambient noise: traffic noise heard from afar"
    - "Ambient noise: rain pattering on windows, occasional thunder"
```

## Format Conventions

1. **Dialogue** uses quotation marks (`""`) to delineate spoken lines
2. **SFX** uses the `SFX:` prefix for model recognition as a sound effect
3. **Ambient** uses the `Ambient noise:` prefix to distinguish background sound
4. Audio elements are typically placed at the **end of the prompt**
5. Multiple audio elements are combinable (Dialogue + SFX + Ambient in a single prompt)

## Prompt Examples with Audio

### Dialogue + Ambience

```
Medium shot of the detective behind his desk. He looks up at the woman
and says in a weary voice, "Of all the offices in this town, you had to
walk into mine." Ambient noise: rain against the window, a distant siren.
```

### SFX + Ambience

```
Wide shot, a nighttime cityscape, vehicles slowly moving along the road,
film noir style, blue-toned night lighting.
SFX: car horns honking intermittently.
Ambient noise: distant traffic sounds, a low urban hum.
```

### Dialogue + SFX

```
Close-up of a woman holding a phone, her eyes widening.
She whispers, "They found us."
SFX: a door creaking open slowly in the background.
```

## When No Audio Is Needed

If the user does not want audio, simply omit all audio-related phrases from the prompt. Veo 3.1 can automatically generate basic background sounds even without explicit audio instructions.
