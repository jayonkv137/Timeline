# Foundation: Motion

Status: v0.1 baseline (DDR-002). Choreography for live updates in D7.

## Principle

**Stillness first, motion for meaning** (DDR-001, principle 5). Motion says that something changed: a node was born, went dormant, reactivated, a question was answered, focus moved, a control responded. Nothing moves to look alive.

## Tokens

| Token | Value | Use |
|---|---|---|
| `duration.instant` | 0ms | Reduced motion, programmatic jumps |
| `duration.fast` | 150ms | Hover, press, notch change (`motion.feedback`) |
| `duration.base` | 250ms | State changes, panel toggles, fill sweep (`motion.state`) |
| `duration.slow` | 380ms | Arrivals: new node, dialog, toast (`motion.arrive`) |
| `duration.breathe` | 4000ms | Only the focus halo and open-question rings |
| `easing.standard` | cubic-bezier(0.4, 0, 0.2, 1) | Most transitions |
| `easing.enter` | cubic-bezier(0, 0, 0.2, 1) | Things arriving |
| `easing.exit` | cubic-bezier(0.4, 0, 1, 1) | Things leaving |

Composites: `--motion-feedback`, `--motion-state`, `--motion-arrive` (duration + easing).

## Rules

1. Animate `transform` and `opacity`, never width, height, padding or margin. Two width transitions remain (scrubber fill, one in workspace.css), listed in DEBT.
2. Every animation has a reduced-motion path. `tokens.css` sets durations to 0; canvas code checks `prefers-reduced-motion` and freezes pulses.
3. Only two loops are allowed: the focus halo and open-question rings, both at the breathe tempo and low amplitude.
4. Scrubbing and live updates never move existing nodes (layout invariant). Positions persist across pairs and tabs.
5. Nothing yanks the user: no auto-scroll or camera jump while the user is in history (Interaction Spec).

## Graph motion vocabulary

| Event | Motion |
|---|---|
| Node born | Grows in at its remembered position over `slow`; its tether draws from the parent |
| Dormant | Sphere, ring and beads dim to `opacity.dormant` (0.55); tether turns slate |
| Reactivated | Tether brightens back over `base` |
| Question answered | Ring fills to an answered bead |
| Focus moves | The white halo moves to the new focus node |
| Drag | Physics springs settle (damping 0.86) |

## Debt (see DEBT.md)

The prototype has four looping animations outside the two allowed: brain `breathe` 3.2s and 3.4s, `questionPulse` 2.5s and `photonFlow` 4s. Keep, retime to `breathe`, or remove: decided in the UI/UX phase.
