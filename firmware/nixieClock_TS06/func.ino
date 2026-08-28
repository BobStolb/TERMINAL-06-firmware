/*
  Anti-poisoning / cathode-cleaning sweep.
  Runs every BURN_PERIOD minutes and once at power-on.
  Covers all six tubes - the IN-17s poison faster than the IN-12s because
  they spend most of their life showing the same handful of digits.
*/
void burnIndicators() {
  for (byte k = 0; k < BURN_LOOPS; k++) {
    for (byte d = 0; d < 10; d++) {
      for (byte i = 0; i < NUM_INDI; i++) {
        indiDigits[i]--;
        if (indiDigits[i] < 0) indiDigits[i] = 9;
      }
      delay(BURN_TIME);
    }
  }
}
