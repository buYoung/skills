# Foundations

## Visual direction

The system communicates calm precision: hierarchy is explicit, surfaces are quiet, and emphasis is concentrated where a user must decide or act. Complexity is organized rather than hidden; density may increase when the task requires it, but it must not create competing focal points.

## Core principles

- **Primary action first (invariant):** each task context has one visually and semantically dominant next action when a primary action exists.
- **Quiet support (invariant):** secondary information and controls support the task without competing with the primary action.
- **Structured density (variable):** information density may vary with content complexity; grouping, alignment, and scan paths must remain clear.
- **Accessible clarity (invariant):** perception, focus, semantics, and alternative input are part of the visual system, not after-the-fact decoration.

## Foundations by dimension

| Dimension | Common contract | Allowed variation | Prohibited expression | Verification |
| --- | --- | --- | --- | --- |
| Color | Use color to establish hierarchy, state, and meaning with sufficient perceptual distinction. | Emphasis can increase for the primary action or urgent state. | Color-only meaning or decorative contrast that competes with the task. | Check the primary action, text, state, and focus in both representative situations. |
| Typography | Establish a clear reading hierarchy and predictable alignment. | Density may tighten in data-heavy contexts while preserving legibility. | Tiny or low-contrast text used to fit more content. | Scan headings, labels, values, and action labels without rereading. |
| Spacing | Use spacing to group related content and separate task stages. | Settings may use more breathing room; tables may use tighter rows. | Arbitrary spacing that breaks grouping or creates false priority. | Confirm grouping and primary-action prominence in simple and dense views. |
| Sizing and layout | Make important actions and content discoverable at the point of use. | Layout can adapt to viewport and content. | Forced sameness that makes a dense table unusable or a settings screen feel ambiguous. | Test intended viewport sizes and keyboard/pointer operation on web. |
| Shape | Prefer restrained, functional shapes whose affordance is apparent. | Shape may distinguish control roles or status when it remains legible. | Novel shapes that require learning before action. | Identify control roles and states without relying on decoration. |
| Depth | Use depth sparingly to separate layers and interactive surfaces. | Stronger separation is allowed for transient overlays. | Effects that add visual noise or imply interaction where none exists. | Check hierarchy and focus in both representative situations. |
| Icons and imagery | Icons clarify actions or status and support text. | Imagery may appear where it carries task-relevant meaning. | Icon-only critical actions without an accessible name; ornamental imagery competing with action. | Verify accessible names and comprehension without color or decoration. |
| Motion | Motion communicates change and preserves orientation. | Web-specific reduced-motion behavior is defined in [platforms/web.md](platforms/web.md). | Motion that delays, distracts from, or obscures the primary action. | Check transitions with motion enabled and reduced motion requested. |

## Missing exact values

The supplied direction does not establish numeric color, typography, spacing, sizing, or motion values. Those values remain an unresolved token decision owned by [tokens.md](tokens.md); do not infer them from convention.

