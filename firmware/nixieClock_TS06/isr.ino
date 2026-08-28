/*
  Multiplex ISR - Timer2 compare A.

  Timer2 runs Fast PWM, TOP = 255, prescaler 1  ->  62.5 kHz.
  26 interrupts are spent on each tube (25 brightness steps + changeover),
  so a whole six-tube frame refreshes at 62500 / 26 / 6 = 400 Hz.

  400 Hz matters commercially: at the stock prescaler of 8, six tubes would
  refresh at 50 Hz and beat against camera shutters - fatal for the product
  video and the listing photos, and visibly flickery in peripheral vision.

  Budget: one PWM period is 256 CPU cycles. Everything the common path needs
  is cached in scalars at changeover time (curDimm / curPort / curMask), so
  it costs roughly 45 cycles - about 18% of the CPU. The changeover path runs
  once in 26 and stays under 130.
*/

ISR(TIMER2_COMPA_vect) {
  uint8_t c = curCount + 1;

  if (c == curDimm) *curPort &= curMaskOff;   // brightness reached -> tube off

  if (c > 25) {                               // ---- changeover ----
    curCount = 0;

    uint8_t i = curIndi + 1;
    if (i >= NUM_INDI) i = 0;
    curIndi = i;

    uint8_t d = indiDimm[i];
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
