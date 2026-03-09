# Cinematography Guide

Defines the camera movements, composition, and lens/focus effects available in Veo 3.1.

## Table of Contents

- [Camera Movement](#camera-movement)
- [Composition](#composition)
- [Lens & Focus](#lens--focus)
- [Combination Rules](#combination-rules)
- [Veo-Specific Notes](#veo-specific-notes)

## Camera Movement

Camera movement is the most powerful tool for conveying tone and emotion.

```yaml
- movement: Dolly Shot
  description: The camera physically moves forward or backward
  variants:
    - "Dolly In: Emphasizes emotion or importance (approaches the subject)"
    - "Dolly Out: Creates a sense of isolation or lingering (retreats from the subject)"
  veo_note: "Dolly is far more stable than zoom in Veo"
  prompt_example: "Dolly shot slowly pushing in on the detective's face"

- movement: Tracking Shot
  description: Follows the subject's movement
  prompt_example: "Tracking shot following the explorer as she steps into the clearing"

- movement: Crane Shot
  description: The camera rises or descends vertically
  prompt_example: "Crane shot starting low on a lone hiker and ascending high above"

- movement: Aerial View
  description: An overhead (drone) perspective
  prompt_example: "Aerial view of a vast desert highway stretching to the horizon"

- movement: Slow Pan
  description: The camera rotates horizontally at a slow pace
  prompt_example: "Slow pan across a crowded marketplace at golden hour"

- movement: POV Shot
  description: First-person perspective from the character's point of view
  prompt_example: "POV shot from behind the singer on stage, looking out at a large, cheering crowd"

- movement: Arc Shot
  description: The camera orbits around the subject in a circular path
  prompt_example: "The camera performs a smooth 180-degree arc shot, starting with the front-facing view"

- movement: Static
  description: The camera remains fixed (no movement)
  prompt_example: "Static camera, locked off wide shot"
```

## Composition

Determines how the frame is structured.

```yaml
- shot: Wide Shot
  purpose: Establishes the space and introduces the environment
  prompt_example: "Wide shot of the abandoned factory floor"

- shot: Medium Shot
  purpose: Balances the upper body of the subject with the background
  prompt_example: "Medium shot, a tired corporate worker"

- shot: Close-up
  purpose: Emphasizes emotion and detail
  prompt_example: "Close-up of her trembling hands gripping the letter"

- shot: Extreme Close-up
  purpose: Highlights minute details (eyes, fingers, etc.)
  prompt_example: "Extreme close-up of a single tear rolling down his cheek"

- shot: Low Angle
  purpose: Conveys dominance, authority, or power
  prompt_example: "Low angle shot looking up at the towering skyscraper"

- shot: High Angle
  purpose: Conveys vulnerability or provides an overview
  prompt_example: "Wide, high-angle crane shot, revealing the lone explorer"

- shot: Two-shot
  purpose: Shows the relationship between two characters
  prompt_example: "Two-shot of the detective and the woman across the desk"

- shot: Over-the-shoulder
  purpose: Establishes point of view in dialogue scenes
  prompt_example: "Over-the-shoulder shot from behind the detective"
```

## Lens & Focus

Using only 1–2 per scene produces the most stable results.

```yaml
- effect: Shallow Depth of Field
  description: Subject is sharp while the background is blurred
  use_case: Highlighting characters or products
  prompt_example: "Close-up with very shallow depth of field, a young woman's face"

- effect: Deep Focus
  description: Everything from foreground to background is in sharp focus
  use_case: Landscapes and spatial context
  prompt_example: "Deep focus wide shot of the entire valley"

- effect: Soft Focus
  description: Overall soft, dreamy look
  use_case: Emotional or dream sequences
  prompt_example: "Soft focus, dreamlike quality"

- effect: Macro Lens
  description: Magnifies extremely small details
  use_case: Insects, water droplets, textures
  prompt_example: "Macro lens capturing dew drops on a spider web"

- effect: Wide-angle Lens
  description: Wide field of view with strong perspective distortion
  use_case: Architecture, landscapes, distortion effects
  prompt_example: "Wide-angle lens, exaggerated perspective of the narrow alley"
```

## Combination Constraints

1. Stable results come from selecting **camera movement + composition** first, then adding lens/focus
2. **1 movement per scene** produces the most stable output
3. **1–2 lens/focus effects** per scene is the practical limit
4. Conflicting combinations that degrade quality:
   - Shallow depth of field + Deep focus (contradictory)
   - Extreme close-up + Wide-angle lens (illogical)
   - Multiple simultaneous camera movements (e.g., Dolly + Crane + Pan)

## Veo-Specific Notes

```yaml
- note: "Dolly produces far more stable results than zoom in Veo"
  implication: "Dolly is the preferred movement over zoom"
- note: "Without explicit camera direction, Veo places the camera arbitrarily"
  implication: "Specifying camera direction reduces unintended framing"
- note: "Multiple shots in a single prompt benefit from timestamp segmentation"
  implication: "Timestamp prompting defines each segment independently"
```
