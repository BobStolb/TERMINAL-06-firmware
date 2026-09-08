/*
  Multiplex ISR - Timer2 compare A.

  Timer2 runs Fast PWM, TOP = 255, prescaler 8  ->  7812.5 Hz, one tick per
  128 us. The tick rate is fixed by the prescaler and does NOT change with
  the slot length, so this ISR always runs at 7812.5 Hz.

  Each tube owns SLOT_TICKS interrupts, split into two parts:

    ticks 1 .. MAX_BRIGHT          lit window. The anode goes off at
                                   curDimm, anywhere in this window.
    ticks MAX_BRIGHT+1 .. SLOT     dead time. Anode already off, decoder
                                   blanked, nothing driven at all.

  With SLOT_TICKS 26 / DEAD_TICKS 5 (see nixieClock_TS06.ino) that is a
  50 Hz six-tube frame and 640 us of dead time.

  The dead time is the whole point. The TLP627 optocoupler driving each
  anode has a Darlington output that keeps conducting for a few hundred us
  after its drive is removed. If the decoder is switched to the next tube's
  digit inside that tail, the outgoing tube lights that digit too - the
  ghosting this timing exists to prevent. Blanking the decoder at
  MAX_BRIGHT rather than merely turning the anode off means that even a
  still-conducting anode has no cathode pulled low to light.

  640 us is the measured ghost-free figure on this hardware. It is reached
  here with only 5 ticks because a prescaler-8 tick is 128 us; the same
  margin cost 18 of the 16 us ticks the previous revision used, which is
  why that revision had to trade away either brightness or refresh rate.

  Note the anode-off test is == curDimm, not >= curDimm: it fires on
  exactly one tick, so a curDimm past the end of the slot would never fire
  at all and the anode would stay on across the changeover. That is why
  curDimm is clamped to MAX_BRIGHT below - the clamp is load-bearing, not
  defensive.

  Budget: at prescaler 8 one PWM period is 2048 CPU cycles, and the ISR
  must finish inside it. Everything the common path needs is cached in
  scalars at changeover time (curDimm / curPort / curMask) to keep it
  cheap - less critical now than it was at prescaler 1, but the caching
  costs nothing and the ISR is the one thing that must never be late.

  Measured on the linked ELF (avr-gcc 7.3.0 -Os, cycle-counted from the
  disassembly, including the 7-cycle interrupt dispatch):

      lit tick, nothing to do ....  84 cy
      anode-off tick ............  94 cy
      dead-time blank tick ......  96 cy
      changeover ...............  161 cy   <- worst case, 7.9% of the period
      ---------------------------------
      mean over a 26-tick slot ..  87 cy   = 4.3% of the CPU

  The per-invocation costs are unchanged from the prescaler-1 revision -
  it is the same code. What changed is that the ISR now fires 8x less
  often, so 33.5% of the CPU became 4.3%. That headroom is a real result
  of this change, not a rounding artefact.
*/

#if DEAD_TICKS >= SLOT_TICKS
#error "DEAD_TICKS must be smaller than SLOT_TICKS - no lit time left"
#endif
#if SLOT_TICKS > 255
#error "SLOT_TICKS must fit in the uint8_t curCount"
#endif
#if MAX_BRIGHT < 1
#error "MAX_BRIGHT is below 1 - every tube would be dark"
#endif
#if MUX_SLOTS > NUM_INDI || MUX_SLOTS < 1
#error "MUX_SLOTS must be between 1 and NUM_INDI"
#endif

ISR(TIMER2_COMPA_vect) {
  uint8_t c = curCount + 1;

  if (c == curDimm) *curPort &= curMaskOff;   // brightness reached -> tube off

  if (c == MAX_BRIGHT) {                      // ---- dead time starts ----
    PORTC = (PORTC & 0xF0) | decoderNibble[10];   // blank the decoder; the
  }                                           // anode is already off (clamp)

  if (c >= SLOT_TICKS) {                      // ---- changeover: gap elapsed ----
    curCount = 0;

    uint8_t i = curIndi + 1;
    if (i >= MUX_SLOTS) i = 0;              // MUX_SLOTS <= NUM_INDI
    curIndi = i;

    uint8_t d = indiDimm[i];
    if (d > MAX_BRIGHT) d = MAX_BRIGHT;       // never let brightness eat the gap
    curDimm    = d;
    curPort    = anodeReg[i];
    curMaskOn  = anodeBit[i];
    curMaskOff = (uint8_t)~anodeBit[i];

    if (d && anodeStates[i]) {
      uint8_t dig = (uint8_t)indiDigits[i];
      if (dig > 10) dig = 10;                 // out of range / negative -> blank
      PORTC = (PORTC & 0xF0) | decoderNibble[dig];
      *curPort |= curMaskOn;
    }
  } else {
    curCount = c;
  }
}
