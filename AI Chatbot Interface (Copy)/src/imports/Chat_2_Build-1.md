# FIGMA MAKE BUILD DOC — CHAT 2 ("AI DROVE")
Build the same interface as Chat 1: a chat panel (center), and a right rail with
THREE stacked sections — TOP (goal + direction), MIDDLE (pair timeline), BOTTOM (the
HOW analogy). Same components, same interactions. Only the data changes.

════════════════════════════════════════════════════════════════════
PART A — LAYOUT (same as Chat 1)
════════════════════════════════════════════════════════════════════
- Left sidebar (~190px): "CHATS" list, one item active: "Cover Letter — Lumen".
- Center: the chat (message bubbles, you = dark bubble right, assistant = light bubble
  left, timestamps above each). Message input pinned to bottom.
- Right rail (~260px): three sections, top→bottom: TOP PANEL, MIDDLE TIMELINE, BOTTOM
  PANEL. Sections size to content; thin divider between them.
- Font: monospace for labels/headers (e.g. Geist Mono / IBM Plex Mono); regular sans
  for body. Light theme, paper-cream background, near-black bubbles for "you".

════════════════════════════════════════════════════════════════════
PART B — THE CHAT (render these messages in order)
════════════════════════════════════════════════════════════════════
you · 09:02
can you write me a cover letter for a marketing manager role at a startup called Lumen? i'm applying tomorrow

assistant · 09:02
Happy to. To make it land, anything specific about your background or why Lumen — or should I write a strong general version you can lightly tweak?

you · 09:03
uh i've got about 5 years in marketing, mostly social media and some email campaigns. that's really it. just make it sound good

assistant · 09:03
Here's a strong draft:

Dear Hiring Team,
I'm excited to apply for the Marketing Manager position at Lumen. With over five years of experience driving marketing initiatives, I've developed expertise in social media strategy and email campaign management that aligns closely with what a fast-moving startup like Lumen needs.
In previous roles, I led social media efforts that grew engaged audiences and designed email campaigns that nurtured leads through the funnel. I thrive where I can wear multiple hats, move quickly, and see the direct impact of my work on growth.
What draws me to Lumen is the chance to help shape a brand at an early stage — to build rather than maintain. I'd love to bring my energy and experience to your team.
Sincerely, [Your Name]

you · 09:05
oh nice. can you make it a bit longer though? feels a little short for a cover letter

assistant · 09:06
Sure — here's an expanded version with an extra paragraph on your impact and approach:
[...same opening...]
Beyond execution, I take a data-informed approach — I pay attention to what's actually moving the needle and double down there rather than spreading effort thin. Whether testing subject lines, refining targeting, or finding formats that resonate, I'm comfortable owning a channel end to end and reporting on what works.
I'm especially comfortable in the ambiguity of an early-stage company, where priorities shift and the playbook is still being written...
[...same closing...]

you · 09:07
perfect. actually can the opening be more catchy? the "I'm excited to apply" thing is so generic

assistant · 09:08
Agreed — a sharper hook:
"The hardest part of early-stage marketing isn't doing the work — it's knowing which work matters. That's the instinct I've spent five years sharpening, and exactly what I'd bring to Lumen as your next Marketing Manager."
Then it flows into the body as before. Want me to send you the full thing clean?

you · 09:09
yes love it, that's so much better. is this good enough to send or should i change anything?

assistant · 09:10
It's solid and ready. Two optional lifts: (1) swap in one concrete metric — "grew Instagram following 40%" or "improved open rates from X to Y" — specifics beat adjectives, and (2) name one specific thing about Lumen's product to show you researched them.

you · 09:11
i don't really have exact metrics off the top of my head lol, just leave it as is. can you also write a short email to send it with?

assistant · 09:12
Of course:
Subject: Marketing Manager Application — [Your Name]
Hi [Hiring Manager], I've attached my cover letter and resume for the Marketing Manager role at Lumen. I'd love to bring my marketing experience to your team as you scale, and welcome the chance to talk. Thank you for your time. Best, [Your Name]

you · 09:13
great, thanks, this is perfect

════════════════════════════════════════════════════════════════════
PART C — TOP PANEL (data)
════════════════════════════════════════════════════════════════════
MAIN GOAL:      Cover letter for Lumen
CURRENT GOAL:   Write the accompanying email
RELATION TAG:   ↳ part of main goal

DIRECTION bar (who shaped the direction overall):
  YOU — 25%   |   AI — 75%      (bar mostly orange)
  dot legend: blue "You", orange "AI"

THE ONE NUMBER:
  💡 0 of your choices were the AI's idea
  (note: in this chat the AI didn't seed YOUR decisions — it just executed them
   wholesale. The story here isn't hidden influence, it's total handoff. If showing
   "0" feels flat, swap this card for: "🤖 the AI produced 100% of the content")

════════════════════════════════════════════════════════════════════
PART D — MIDDLE TIMELINE (the rows)
════════════════════════════════════════════════════════════════════
Component (same as Chat 1): one row per pair, ~32px tall. Columns L→R:
  [pair label 24px] [agency-canvas 40px w/ center tick, bar grows left=blue/you,
   right=orange/AI, length=consequential] [gap] [requirement/topic label, flex]
   [mode dot 7px far right]

ROWS (note the front-loaded orange — P1 is the big one):
  P1  bar: RIGHT/orange LARGE   label: "AI wrote the whole letter"     dot: AI
  P2  bar: RIGHT/orange medium  label: "AI expanded it (+1 para)"      dot: AI
  P3  bar: RIGHT/orange medium  label: "AI authored the hook"          dot: AI
  P4  bar: RIGHT/orange small   label: "AI suggested metrics (declined)" dot: AI
  P5  bar: RIGHT/orange medium  label: "AI wrote the email"            dot: AI
  (tiny blue stubs optional on P2/P3/P5 left side = your one-line nudges, ~4px)

Result: a column leaning RIGHT, orange, with one LARGE bar at the top (P1) then a
thinning tail. The all-right orange reads "the AI drove" at a glance.

════════════════════════════════════════════════════════════════════
PART E — BOTTOM PANEL (data)
════════════════════════════════════════════════════════════════════
HOW (the analogy — single line, driving system):
  "You're in the back seat — the AI's driving."
  sub: "you gave the destination; the AI did the rest."

(Optional, only if it adds — else omit; the row dots already show the mix)
MODE SPLIT:  You driving 15% · Figuring together 0% · AI driving 85%

════════════════════════════════════════════════════════════════════
PART F — INTERACTIONS (identical to Chat 1)
════════════════════════════════════════════════════════════════════
1. Hover a timeline row → row bg lightens (#000 @4%), tooltip shows full label +
   "Shaped by: AI" + that pair's goal. Cursor = pointer.
2. Click a row → main chat scrolls to that pair + soft ~1s highlight on those bubbles.
3. Scroll-sync → as the main chat scrolls, a translucent slider (#000 @6%, 1px border)
   covers the row(s) for the visible pairs (VS Code minimap style). Slides smoothly
   (~150ms ease); rows don't recompute.
4. Active row → 2px orange left-edge accent on the pair nearest viewport center.
5. On load → slider at the BOTTOM (newest pair).
6. Top + bottom panels show the LATEST/overall values; they do NOT time-travel in v1.
