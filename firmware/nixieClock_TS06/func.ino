/*
  Anti-poisoning / cathode-cleaning sweep.
  Runs every BURN_PERIOD minutes and once at power-on.
  Covers all six tubes - the IN-17s poison faster than the IN-12s because
  they spend most of their life showing the same handful of digits.

  Gated on BURN_ENABLED: the sweep deliberately walks every tube through
  every digit, which is indistinguishable from ghosting when you are
  staring at the display trying to judge the multiplex timing. With the
  flag at 0 this becomes an empty function and every call site is a no-op,
  so nothing else needs to change.
*/
void burnIndicators() {
#if BURN_ENABLED
  for (byte k = 0; k < BURN_LOOPS; k++) {
    for (byte d = 0; d < 10; d++) {
      for (byte i = 0; i < NUM_INDI; i++) {
        indiDigits[i]--;
        if (indiDigits[i] < 0) indiDigits[i] = 9;
      }
      delay(BURN_TIME);
    }
  }
#endif
}
