void loop() {
  if (dotTimer.isReady()) calculateTime();          // 2 Hz: time + seconds tubes
  if (newTimeFlag && curMode == 0) flipTick();      // digit transition effect
  dotBrightTick();                                  // colon fade
  backlBrightTick();                                // backlight breathing
#if GLITCH_ENABLED
  if (GLITCH_ALLOWED && curMode == 0) glitchTick();  // random flicker
#endif
  buttonsTick();
  settingsTick();
}
