# TERMINAL-06 — control scheme rev B (08.09.26)

Two changes to `claude/TERMINAL-06-spec.md` §1, decided during the TS06-FASCIA panel
design. **§1 has not been rewritten yet** — this file is the authority until it is, and
the sweep is queued alongside the withdrawn 26.94 mm rotary figure.

## Change 1 — INFO and FORMAT/DATE swap places

| Pos | Rev A | **Rev B** |
|---|---|---|
| 1 | Normal | Normal |
| 2 | Set Time | Set Time |
| 3 | Display | Display |
| 4 | Ambient | Ambient |
| 5 | Info | **Format / Date** |
| 6 | Format / Date | **Info** |

**Why.** §1 already identified positions 1 and 5 as the two screens that ignore every
input — "safe parking positions where a knock does nothing". Rev A left one of them in
the middle of the arc. Rev B puts both on **end stops**: NORMAL at one extreme, INFO at
the other, every live editing screen between them. The knob cannot be knocked past
either end into something that changes a setting, because past either end there is
nothing.

**Cost.** One row of the A6 threshold table. Position 5 is 4.00 V / ADC 818 and position
6 is 5.00 V / ADC 1023, unchanged as voltages — only the screen each maps to moves. No
hardware change, no ladder change, no fascia change beyond the printed word order.

## Change 2 — SUB gains the glitch rate on Display

Rev A read Lever B on **one** screen out of six (Format/Date, and only while Lever A
pointed at Date). A lever that is dead five times out of six is hard to letter honestly
and reads as broken hardware.

Rev B gives it a second job on position 3:

- **FIELD** picks Brightness ↔ **Effects**
- **SUB**, read only while FIELD = Effects, picks Transition ↔ **Glitch**
- Buttons adjust whichever is selected. **Glitch runs off at the bottom of its range**,
  so "how often, if at all" is one continuous control rather than a separate on/off.

**The reason this is worth doing is not the extra feature — it is that SUB now has a
rule instead of an exception:**

> **SUB is read only when FIELD is thrown to its second position.**

That holds on both screens that use it (Effects on Display, Date on Format/Date) with no
special case. A rule can be learned once; an exception has to be printed.

Firmware note: `GLITCH_ALLOWED` is currently a compile-time flag. This makes it a runtime
setting with a rate, stored in EEPROM alongside format/brightness/effect/ambient — one
more item on §5's "still to write" list, not a new mechanism.

## Face decisions, same session

- **No maker's mark and no wordmark on the fascia.** The hexagon-and-breaking-bar in spec
  §6 was never chosen by the owner — it entered the project through an earlier session's
  document. Rather than inherit it, the face now carries controls and their names and
  nothing else. **Identity moves to the enclosure and the packaging**, where it is not
  competing with a dial. §6's Identity line needs updating to match; the colour palette
  in it is unaffected.
- **The gold enable trace ends beneath FIELD, not on it.** Nothing is drawn in the space
  the lever physically occupies when thrown down — the real lever closes that gap, which
  is stronger than a picture of one.

## Consequence for TS06-FASCIA

The face letters the levers **FIELD** and **SUB** — the invariant role, true on all six
screens — and marks SUB's two live positions with **gold ENIG traces** running from the
lever to positions 3 and 5 on the dial. The panel states its own asymmetry in copper
rather than hiding it or over-lettering it.

Rotary positions, left to right on the dial arc:
`NORMAL · SET TIME · DISPLAY · AMBIENT · FORMAT/DATE · INFO`

## Still open

- ~~**Step angle.**~~ **CLOSED 08.09.26 — twelve detents counted, so the step is exactly
  30.00°** and six positions span 150°. Counted rather than measured, so it is exact, not
  estimated. It agrees with the twelve outer taps already in the model — the same claim
  arriving from a second, independent direction. The earlier ~32°/160° figure was an eye
  estimate of a swept arc and is **withdrawn**.
- **Bushing stack depth.** Diameters are measured and settled. The open question is
  whether nut + washer + chassis recess fit in the 5.00 mm left after 7.00 mm of usable
  bushing minus 2.0 mm of FR4. A depth question against the printed chassis.
