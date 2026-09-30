/*
  Two buttons and one lever.

    lever HIGH  = RUN      lever LOW = PROGRAM
    BTN_SET / BTN_ADJ change meaning with the lever, so two buttons cover
    everything the original three did - and setting the time can never be
    entered by accident, which is what you want in a shipped product.

    BOARD_TYPE 4 has no lever: readLever() reports the fascia's MODE rotary
    instead, LOW (PROGRAM) on SET TIME and HIGH (RUN) anywhere else. See
    ts06pair.ino.
*/

// blink the field currently being edited
void settingsTick() {
  if (curMode == 1 && blinkTimer.isReady()) {
    sendHM(changeHrs, changeMins);
    sendSeconds(0);
    lampState = !lampState;
    if (lampState) {
      for (byte i = 0; i < NUM_HM; i++) anodeStates[i] = 1;
    } else {
      if (!currentDigit) { anodeStates[0] = 0; anodeStates[1] = 0; }
      else               { anodeStates[2] = 0; anodeStates[3] = 0; }
    }
  }
}

static boolean timeEdited = false;      // set by bumpTime(): leaving PROGRAM writes the RTC only then

static void bumpTime(int8_t dir) {
  timeEdited = true;
  if (!currentDigit) {
    changeHrs += dir;
    if (changeHrs > 23) changeHrs = 0;
    if (changeHrs < 0)  changeHrs = 23;
  } else {
    changeMins += dir;
    if (changeMins > 59) changeMins = 0;
    if (changeMins < 0)  changeMins = 59;
  }
  sendHM(changeHrs, changeMins);
}

static void enterProgram() {
  curMode = 1;
  currentDigit = false;
  timeEdited = false;
  changeHrs = hrs;
  changeMins = mins;
  for (byte i = 0; i < NUM_INDI; i++) anodeStates[i] = 1;
  applyBright();
  newTimeFlag = false;
  flipInit = false;
  sendHM(changeHrs, changeMins);
  sendSeconds(0);
}

static void leaveProgram() {
  curMode = 0;
  DateTime now = rtc.now();
  if (timeEdited) {
    // Keep the date; only the edited hours and minutes change, and the seconds restart.
    hrs = changeHrs;
    mins = changeMins;
    secs = 0;
    rtc.adjust(DateTime(now.year(), now.month(), now.day(), hrs, mins, 0));
  } else {
    // Passing through PROGRAM without an edit leaves the clock alone.
    hrs = now.hour();
    mins = now.minute();
    secs = now.second();
  }
  for (byte i = 0; i < NUM_INDI; i++) anodeStates[i] = 1;
  changeBright();
  sendTime(hrs, mins, secs);
  dotTimer.reset();
}

void buttonsTick() {
  btnSet.tick();
  btnAdj.tick();

  // ---- lever: debounced level read ----
  boolean lv = readLever();
  if (lv != leverState) {
    delay(5);
    if (readLever() == lv) {
      leverState = lv;
      if (leverState) leaveProgram();   // back to RUN
      else            enterProgram();   // into PROGRAM
    }
  }

  if (curMode == 1) {                   // ---------- PROGRAM ----------
    if (btnSet.isClick()) currentDigit = !currentDigit;
    if (btnAdj.isClick()) bumpTime(+1);
    if (btnAdj.isHold() && repeatTimer.isReady()) bumpTime(+1);

  } else {                              // ---------- RUN ----------
    // BTN_SET: backlight mode
    if (btnSet.isClick()) {
      if (++BACKL_MODE >= 3) BACKL_MODE = 0;
      EEPROM.put(1, BACKL_MODE);
      if (BACKL_MODE == 1)      setPWM(BACKL, backlMaxBright);
      else if (BACKL_MODE == 2) digitalWrite(BACKL, 0);
    }
    // BTN_SET held: glitches on/off
    if (btnSet.isHolded()) {
      GLITCH_ALLOWED = !GLITCH_ALLOWED;
      EEPROM.put(2, GLITCH_ALLOWED);
      if (!GLITCH_ALLOWED) { glitchFlag = false; applyBright(); }
    }
    // BTN_ADJ: digit transition effect, previewed on the four HM tubes
    if (btnAdj.isClick()) {
      if (++FLIP_EFFECT >= FLIP_EFFECT_NUM) FLIP_EFFECT = 0;
      EEPROM.put(0, FLIP_EFFECT);
      flipTimer.setInterval(FLIP_SPEED[FLIP_EFFECT]);
      applyBright();
      for (byte i = 0; i < NUM_INDI; i++) anodeStates[i] = 1;
      for (byte i = 0; i < NUM_HM; i++) indiDigits[i] = FLIP_EFFECT;
      setNewTime();
      newTimeFlag = true;
      flipInit = false;
    }
  }
}
