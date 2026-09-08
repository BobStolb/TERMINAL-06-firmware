void setup() {
  randomSeed(analogRead(6) + analogRead(7));

  // ---------- pin directions ----------
  pinMode(DECODER0, OUTPUT);
  pinMode(DECODER1, OUTPUT);
  pinMode(DECODER2, OUTPUT);
  pinMode(DECODER3, OUTPUT);
  for (byte i = 0; i < NUM_INDI; i++) {
    pinMode(opts[i], OUTPUT);
    digitalWrite(opts[i], LOW);
  }
  pinMode(GEN, OUTPUT);
  pinMode(DOT, OUTPUT);
  pinMode(BACKL, OUTPUT);
  pinMode(LEVER, INPUT_PULLUP);

  // ---------- precompute the anode port access ----------
  for (byte i = 0; i < NUM_INDI; i++) {
    byte p = opts[i];
    if (p < 8) {                 // D0..D7 -> PORTD
      anodeReg[i] = &PORTD;
      anodeBit[i] = _BV(p);
    } else {                     // D8..D13 -> PORTB
      anodeReg[i] = &PORTB;
      anodeBit[i] = _BV(p - 8);
    }
  }

  /*
    Precompute the PORTC low nibble for every digit.
    Board wiring: DECODER3->A0? no - the original mapping is
        A0 = DECODER0 = bit2 of the mask value
        A1 = DECODER1 = bit1
        A2 = DECODER2 = bit3
        A3 = DECODER3 = bit0
    Index 10 writes 0b1111, an invalid BCD code, which blanks the K155ID1.
  */
  for (byte d = 0; d < 10; d++) {
    byte m = digitMask[d];
    decoderNibble[d] = (bitRead(m, 2) << 0)    // A0
                       | (bitRead(m, 1) << 1)  // A1
                       | (bitRead(m, 3) << 2)  // A2
                       | (bitRead(m, 0) << 3); // A3
  }
  decoderNibble[10] = 0x0F;                    // blank

  // ---------- HV boost oscillator: 31 kHz on D9 ----------
  TCCR1B = TCCR1B & 0b11111000 | 1;
  setPWM(GEN, DUTY);

  // ---------- RTC (before the multiplex ISR is armed) ----------
  rtc.begin();
  rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
  DateTime now = rtc.now();
  secs = now.second();
  mins = now.minute();
  hrs  = now.hour();

  // ---------- Timer2: fast PWM, prescaler 8, COMPA interrupt ----------
  // Prescaler 8 is AlexGyver's original value. See MULTIPLEX TIMING in
  // nixieClock_TS06.ino for why we came back to it.
  TCCR2A = _BV(WGM21) | _BV(WGM20);            // fast PWM, TOP = 0xFF
  TCCR2B = (TCCR2B & B11111000) | 2;           // prescaler 8 -> 7812.5 Hz
  TIMSK2 |= _BV(OCIE2A);

  // ---------- EEPROM ----------
  if (EEPROM.read(1023) != 100) {
    EEPROM.put(1023, 100);
    EEPROM.put(0, FLIP_EFFECT);
    EEPROM.put(1, BACKL_MODE);
    EEPROM.put(2, GLITCH_ALLOWED);
  }
  EEPROM.get(0, FLIP_EFFECT);
  EEPROM.get(1, BACKL_MODE);
  EEPROM.get(2, GLITCH_ALLOWED);
  if (FLIP_EFFECT >= FLIP_EFFECT_NUM) FLIP_EFFECT = 1;
  if (BACKL_MODE > 2) BACKL_MODE = 0;

  sendTime(hrs, mins, secs);
  changeBright();

  dotBrightStep = ceil((float)dotMaxBright * 2 / DOT_TIME * DOT_TIMER);
  if (dotBrightStep == 0) dotBrightStep = 1;

  if (backlMaxBright > 0)
    backlBrightTimer.setInterval((float)BACKL_STEP / backlMaxBright / 2 * BACKL_TIME);

  glitchTimer.setInterval(random(GLITCH_MIN * 1000L, GLITCH_MAX * 1000L));
  indiBrightCounter = indiMaxBright;
  flipTimer.setInterval(FLIP_SPEED[FLIP_EFFECT]);

  leverState = digitalRead(LEVER);
  curMode = leverState ? 0 : 1;
  if (curMode == 1) { changeHrs = hrs; changeMins = mins; }

  // power-on self test: run every cathode of every tube once
  burnIndicators();
}
