# TERMINAL-06 firmware

Six-digit Soviet nixie tube clock firmware — 4x IN-12A (HH:MM) + 2x IN-17 (SS),
built on Arduino Nano / ATmega328P.

Derived from [AlexGyver's NixieClock v2.5](https://github.com/AlexGyver/NixieClock_v2)
(MIT-spirited open project). Keep the original attribution if you redistribute
this source — see the header of `nixieClock_TS06.ino`.

## What's in here

- `firmware/nixieClock_TS06/` — the main clock sketch. Open
  `nixieClock_TS06.ino` in the Arduino IDE; the other `.ino` files in the same
  folder are tabs of the same sketch and compile together automatically.
  `nixieClock_TS06.hex` alongside them is a precompiled build — flashable
  directly with avrdude if you don't want to rebuild from source.
- `firmware/secCathodeMap/` — a standalone bench jig (its own `setup()`/
  `loop()`, deliberately kept in a separate sketch folder from the main
  firmware so the two don't collide at compile time). Run it once per new
  SEC module to map IN-17 cathodes to K155ID1 pins — see the comment header
  in `secCathodeMap.ino` for the full procedure.
- `libraries/` — third-party libraries this sketch depends on (GyverButton,
  RTClib). Not yet added to this repo as of the first commit — Wire and
  EEPROM are built into the Arduino AVR core and don't need anything extra.

## Status vs. the project spec (as of 28.08.26)

This code is the display-layer port described in `TERMINAL-06-spec.md` §5:
six-tube multiplex ISR (Timer2 prescaler 1, ~400 Hz refresh), anti-poisoning
and glitch effects extended to all six tubes, buzzer removed (D2 reused),
old rev B control scheme (2 buttons + 1 lever) — not the rotary/lever panel
described elsewhere in the project, which is a later firmware milestone.

**One known discrepancy, not yet fixed here:** the spec states `DOT_BRIGHT`
was retuned for neon (170/90) instead of the LED-era default (35/15), but
this source still has `DOT_BRIGHT 35` / `DOT_BRIGHT_N 15`
(`nixieClock_TS06.ino`). Doesn't affect the digit-multiplex testing this
firmware is used for (P2 in the prototype plan), but worth fixing before the
colon step (P6).

## Board settings for flashing

Arduino IDE: Board = Arduino Nano, Processor = ATmega328P. If upload fails
with a programmer-not-responding error, switch Processor to
"ATmega328P (Old Bootloader)" — common on CH340-based Nano clones.
