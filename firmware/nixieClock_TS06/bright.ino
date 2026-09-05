void backlBrightTick() {
  if (BACKL_MODE == 0 && backlBrightTimer.isReady()) {
    if (backlMaxBright > 0) {
      if (backlBrightDirection) {
        if (!backlBrightFlag) {
          backlBrightFlag = true;
          backlBrightTimer.setInterval((float)BACKL_STEP / backlMaxBright / 2 * BACKL_TIME);
        }
        backlBrightCounter += BACKL_STEP;
        if (backlBrightCounter >= backlMaxBright) {
          backlBrightDirection = false;
          backlBrightCounter = backlMaxBright;
        }
      } else {
        backlBrightCounter -= BACKL_STEP;
        if (backlBrightCounter <= BACKL_MIN_BRIGHT) {
          backlBrightDirection = true;
          backlBrightCounter = BACKL_MIN_BRIGHT;
          backlBrightTimer.setInterval(BACKL_PAUSE);
          backlBrightFlag = false;
        }
      }
      setPWM(BACKL, getPWM_CRT(backlBrightCounter));
    } else {
      digitalWrite(BACKL, 0);
    }
  }
}

void dotBrightTick() {
  if (dotBrightFlag && dotBrightTimer.isReady()) {
    if (dotBrightDirection) {
      dotBrightCounter += dotBrightStep;
      if (dotBrightCounter >= dotMaxBright) {
        dotBrightDirection = false;
        dotBrightCounter = dotMaxBright;
      }
    } else {
      dotBrightCounter -= dotBrightStep;
      if (dotBrightCounter <= 0) {
        dotBrightDirection = true;
        dotBrightFlag = false;
        dotBrightCounter = 0;
      }
    }
    setPWM(DOT, getPWM_CRT(dotBrightCounter));
  }
}

// applies indiMaxBright to every tube, with the seconds trim on tubes 4-5
void applyBright() {
  int16_t sec = (int16_t)indiMaxBright + SEC_BRIGHT_TRIM;
  if (sec > MAX_BRIGHT) sec = MAX_BRIGHT;   // was a hardcoded 24
  if (sec < 1) sec = 1;
  for (byte i = 0; i < NUM_INDI; i++)
    indiDimm[i] = (i < NUM_HM) ? indiMaxBright : (uint8_t)sec;
}

void changeBright() {
#if (NIGHT_LIGHT == 1)
  if ((hrs >= NIGHT_START && hrs <= 23) || (hrs >= 0 && hrs < NIGHT_END)) {
    indiMaxBright = INDI_BRIGHT_N;
    dotMaxBright  = DOT_BRIGHT_N;
    backlMaxBright = BACKL_BRIGHT_N;
  } else {
    indiMaxBright = INDI_BRIGHT;
    dotMaxBright  = DOT_BRIGHT;
    backlMaxBright = BACKL_BRIGHT;
  }
#endif
  applyBright();

  dotBrightStep = ceil((float)dotMaxBright * 2 / DOT_TIME * DOT_TIMER);
  if (dotBrightStep == 0) dotBrightStep = 1;

  if (backlMaxBright > 0)
    backlBrightTimer.setInterval((float)BACKL_STEP / backlMaxBright / 2 * BACKL_TIME);
  indiBrightCounter = indiMaxBright;

  if (BACKL_MODE == 1) setPWM(BACKL, backlMaxBright);
}
