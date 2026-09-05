/*
  Multiplex ISR - Timer2 compare A.

  Timer2 runs Fast PWM, TOP = 255, prescaler 1  ->  62.5 kHz, one tick per
  16 us. The tick rate is fixed by the prescaler and does NOT change with
  the slot length, so this ISR always runs at 62.5 kHz.

  Each tube owns SLOT_TICKS interrupts, split into two parts:

    ticks 1 .. MAX_BRIGHT          lit window. The anode goes off at
                                   curDimm, anywhere in this window.
    ticks MAX_BRIGHT+1 .. SLOT     dead time. Anode already off, decoder
                                   blanked, nothing driven at all.

  With SLOT_TICKS 52 / DEAD_TICKS 18 (see nixieClock_TS06.ino) that is a
  200 Hz six-tube frame and 288 us of dead time.

  The dead time is the whole point. The TLP627 optocoupler driving each
  anode has a Darlington output that keeps conducting for ~250-300 us after
  its drive is removed. If the decoder is switched to the next tube's digit
  inside that tail, the outgoing tube lights that digit too - the ghosting
  this timing exists to prevent. Blanking the decoder at MAX_BRIGHT rather
  than merely turning the anode off means that even a still-conducting
  anode has no cathode pulled low to light.

  Note the anode-off test is == curDimm, not >= curDimm: it fires on
  exactly one tick, so a curDimm past the end of the slot would never fire
  at all and the anode would stay on across the changeover. That is why
  curDimm is clamped to MAX_BRIGHT below - the clamp is load-bearing, not
  defensive.

  Budget: one PWM period is 256 CPU cycles, and the ISR must finish inside
  it. Everything the common path needs is cached in scalars at changeover
  time (curDimm / curPort / curMask) to keep it cheap.

  Measured on the linked ELF (avr-gcc 7.3.0 -Os, cycle-counted from the
  disassembly, including the 7-cycle interrupt dispatch):

      lit tick, nothing to do ....  84 cy
      anode-off tick ............  94 cy
      dead-time blank tick ......  96 cy
      changeover ...............  161 cy   <- worst case, 63% of the period
      ---------------------------------
      mean over a 52-tick slot ..  86 cy   = 33.5% of the CPU

  The old 26-tick slot measured 85 cy mean / 155 cy worst case (33.3%), so
  this change is cost-neutral: the ISR rate is set by the prescaler, not by
  the slot length, and the one expensive path now runs half as often, which
  offsets the extra dead-time branch. (The 45 cy / 18% figure that used to
  be written here was simply wrong - it was never measured.)
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

ISR(TIMER2_COMPA_vect) {
  uint8_t c = curCount + 1;

  if (c == curDimm) *curPort &= curMaskOff;   // brightness reached -> tube off

  if (c == MAX_BRIGHT) {                      // ---- dead time starts ----
    PORTC = (PORTC & 0xF0) | decoderNibble[10];   // blank the decoder; the
  }                                           // anode is already off (clamp)

  if (c >= SLOT_TICKS) {                      // ---- changeover: gap elapsed ----
    curCount = 0;

    uint8_t i = curIndi + 1;
    if (i >= NUM_INDI) i = 0;
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
