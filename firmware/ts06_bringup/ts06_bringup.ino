/*
  TERMINAL-06 // bring-up sketch for the through-hole pair TS06-DISP + TS06-DRV
  ---------------------------------------------------------------------------
  A bench tool, not the clock. It drives the driver board one block at a time
  from the Serial Monitor, so each stage of PCB/TS06-pair-testing.md (part C)
  can be tested on its own. The clock firmware (firmware/nixieClock_TS06 with
  BOARD_TYPE 4) is not touched by this sketch and is flashed after it.

  Serial Monitor: 9600 baud, any line ending. Commands are single characters.

  SAFE BY DEFAULT
    * After every reset the 185 V converter is OFF (D9 held low), every anode
      is off, all four decoders are blank and every LED is off. Opening the
      Serial Monitor resets the Nano, so it switches the high voltage off too.
      (C7 still holds its charge for a few seconds: see the testing guide.)
    * The converter starts only on a capital H. A lower-case h stops it.
    * Only one anode is ever on. With the converter on, a tube runs at the
      clock's own duty, 21 of 156 ticks of 128 us (2.69 ms lit in each
      19.97 ms frame, 13.5 %), unless you ask for 's': a steady burst of 5 s
      for reading the voltage across its anode resistor. With the converter
      off (the rail is then only the 12 V input, ~11 V) 's' stays on until
      you change it, so a meter can read the switch at leisure.
    * The IN-15 pair has no anode switch: it is lit from the rail through
      R56 / R57 whenever its decoder gets a code with a glyph. So with the
      converter on, 'g', 'a', 'p' and 'c' light the IN-15s at full current.

  COMMANDS
    ?        help and status
    H / h    185 V converter on / off (31.4 kHz on D9, duty 190, as the clock)
    i        I2C scan: expects 0x20 (MCP23017, U3) and 0x68 (DS3231, U13)
    0 .. 9   that digit on U2 + U17 (the IN-12 bus and the IN-17 pair)
    g        next code on U15 + U16 (the IN-15 pair): 0 .. 9, then blank
    a / p    IN-15B shows A (AM) / IN-15A shows P (PM), the other one blank
    b        blank all four decoders
    c        cycle: every second the next code on all four decoders, with
             the decoder pin and the strip pin that should now be low
    t        next anode: H10 H1 M10 M1 S10 S1, then none
    x        all anodes off
    s        steady burst on the selected anode (5 s with the converter on);
             s again ends it early
    k        colon switch on / off (D10 -> R1 -> VT1)
    l        backlight: all nine, then HL1 .. HL8, HL9 (m) alone, then off
    r        live A6 / A7 / buttons, four times a second (r again stops)

  Every table below is the board's, from tools/ts06pair.py, and
  tools/verify_pair.sh checks them against it.
*/
#include <Wire.h>
#include <avr/pgmspace.h>

#define BAUD      9600
#define PIN_HV    9       // D9 -> R66 -> PWM_G -> TC4420 -> IRF840: the converter's clock
#define PIN_COLON 10      // D10 -> R1 10k -> VT1 base: both colon lamps
#define PIN_BACKL 11      // D11 -> R20 470R -> VT20 base: BL_K, every LED's cathode
#define PIN_M     12      // D12 -> R53 220R -> HL9, the "m" LED
#define PIN_MINUS 7       // fascia "-" button, to ground
#define PIN_PLUS  8       // fascia "+" button, to ground
#define DUTY      190     // the clock's DUTY: 23.8 us on in each 31.9 us period
#define MCP_ADDR  0x20    // U3, A0-A2 grounded
#define RTC_ADDR  0x68    // DS3231 on the module in U13

#define FRAME_TICKS 156   // 6 slots x 26 ticks of 128 us: the clock's 19.97 ms frame
#define LIT_TICKS   21    // SLOT_TICKS 26 - DEAD_TICKS 5 at INDI_BRIGHT 21: 13.5 %
#define BURST_MS    5000  // the steady burst, when the converter is on

// ---------------------------------------------------------------- the board's tables
// anode drive, in tube order H10 H1 M10 M1 S10 S1 (TUBE_PIN4)
const uint8_t ANODE_PIN[6] = {6, 5, 4, 3, 2, 13};
// digit -> K155ID1 code on U2 and U17 (DIGIT_MASK4, the firmware's BOARD_TYPE 4 digitMask)
const uint8_t DIGIT_CODE[10] = {1, 0, 5, 4, 6, 7, 3, 2, 9, 8};
// which bit carries code weight 1, 2, 4, 8: PORTC bit (Nano A0..A3) for U2 + U17 (K155_INPUT),
// MCP23017 port-A bit for U15 and for U16 (XA_IN)
const uint8_t NANO_BIT[4] = {3, 1, 0, 2};
const uint8_t U15_BIT[4] = {3, 1, 0, 2};
const uint8_t U16_BIT[4] = {7, 5, 4, 6};
// K155ID1 output Qn -> its DIP-16 pin
const uint8_t Q_PIN[10] = {16, 15, 8, 9, 13, 14, 11, 10, 1, 2};
// digit -> the strip pin that carries it: XS11 (IN-12 bus), XS12 pins 1-10 (IN-17 pair)
const uint8_t XS11_PIN[10] = {9, 10, 8, 6, 4, 2, 1, 3, 5, 7};
const uint8_t XS12_PIN[10] = {8, 7, 6, 5, 4, 3, 2, 1, 10, 9};
// IN-15 decoder code -> glyph (GLYPH_Q) and -> its XS12 pin (0: that output has no glyph)
const char G_U15[] PROGMEM = "WATT FARAD AMP OHM HENRY HERTZ VOLT SIEMENS - -";
const char G_U16[] PROGMEM = "MINUS PLUS NANO PCT MEGA MILLI KILO PI P MICRO";
const uint8_t U15_XS12[10] = {21, 20, 14, 15, 18, 19, 17, 16, 0, 0};
const uint8_t U16_XS12[10] = {29, 28, 22, 23, 26, 27, 25, 24, 30, 31};
// backlight: GPBk lights HL(k+1) through RN1 pins (8-k)-(9+k); the strip and pin of its anode
const uint8_t BL_STRIP[8] = {21, 21, 23, 23, 24, 24, 25, 25};
const uint8_t BL_PIN[8] = {2, 5, 1, 4, 1, 4, 1, 6};
// the anode resistor and the strip pin of each tube
const char TUBE_TXT[] PROGMEM =
  "H10 V1 IN-12 R27 6k8 XS21.3|H1 V2 IN-12 R28 6k8 XS21.4|M10 V3 IN-12 R29 6k8 XS23.2|"
  "M1 V4 IN-12 R30 6k8 XS23.3|S10 V5 IN-17 R31 12k XS24.2|S1 V6 IN-17 R32 12k XS24.3";
const char MODE_TXT[] PROGMEM = "NORMAL|SET TIME|DISPLAY|AMBIENT|FORMAT/DATE|INFO";

// ---------------------------------------------------------------- state
volatile uint8_t *volatile aPort = 0;   // the selected anode's port, and its bit (0: none)
volatile uint8_t aMask = 0;
volatile bool steady = false;
volatile uint8_t tick = 0;
int8_t tube = -1;                       // selected anode, -1: none
bool hv = false, colon = false, live = false, cycling = false, mcpOk = false;
bool busOk = false;                    // SDA and SCL idle high: safe to talk on the bus
uint8_t digitCode = 15, c15 = 15, c16 = 15, ledState = 0, cycleStep = 0;
uint32_t burstStart = 0, lastLive = 0, lastCycle = 0;

// ---------------------------------------------------------------- helpers
// the n-th item of a PROGMEM list separated by sep
void printItem(const char *p, uint8_t n, char sep) {
  char ch;
  while (n && (ch = pgm_read_byte(p++))) if (ch == sep) n--;
  while ((ch = pgm_read_byte(p++)) && ch != sep) Serial.write(ch);
}

uint8_t nibble(uint8_t code, const uint8_t *bitOf) {
  uint8_t v = 0;
  for (uint8_t w = 0; w < 4; w++)
    if (code & (1 << w)) v |= 1 << bitOf[w];
  return v;
}

uint8_t mcpWrite(uint8_t reg, uint8_t val) {
  if (!busOk) return 4;
  Wire.beginTransmission(MCP_ADDR);
  Wire.write(reg);
  Wire.write(val);
  return Wire.endTransmission();
}

int readReg(uint8_t addr, uint8_t reg) {
  if (!busOk) return -1;
  Wire.beginTransmission(addr);
  Wire.write(reg);
  if (Wire.endTransmission(false)) return -1;
  if (Wire.requestFrom(addr, (uint8_t)1) != 1) return -1;
  return Wire.read();
}

void writeDecoders() {
  PORTC = (PORTC & 0xF0) | nibble(digitCode, NANO_BIT);
  mcpWrite(0x12, nibble(c15, U15_BIT) | nibble(c16, U16_BIT));   // GPIOA
}

// Latches first, then directions, so no pin ever drives the power-on latch 0x00 (code 0,
// which would light a glyph on both IN-15s). Register 0x05 is IOCON in BANK = 1: a 0
// there brings a chip left in BANK = 1 back to BANK = 0 (in BANK = 0 it is GPINTENB).
void mcpInit() {
  mcpWrite(0x05, 0x00);
  writeDecoders();
  mcpWrite(0x13, 0x00);                 // GPIOB: LEDs off
  mcpWrite(0x00, 0x00);                 // IODIRA: outputs
  mcpWrite(0x01, 0x00);                 // IODIRB
  mcpOk = (readReg(MCP_ADDR, 0x00) == 0x00 && readReg(MCP_ADDR, 0x01) == 0x00);
}

// Timer2 overflow, 7812.5 Hz: the selected anode is lit for LIT_TICKS of every FRAME_TICKS,
// like one slot of the clock's multiplex, or all the time in a steady burst.
ISR(TIMER2_OVF_vect) {
  if (++tick >= FRAME_TICKS) tick = 0;
  if (aMask) {
    if (steady || tick < LIT_TICKS) *aPort |= aMask;
    else *aPort &= (uint8_t)~aMask;
  }
}

void selectTube(int8_t t) {
  cli();
  aMask = 0;
  for (uint8_t i = 0; i < 6; i++) digitalWrite(ANODE_PIN[i], LOW);
  steady = false;
  tube = t;
  if (t >= 0) {
    aPort = portOutputRegister(digitalPinToPort(ANODE_PIN[t]));
    aMask = digitalPinToBitMask(ANODE_PIN[t]);
  }
  sei();
}

void setHV(bool on) {
  if (on) {
    steady = false;                     // a burst started with the rail at 12 V ends here
    TCCR1B = (TCCR1B & 0xF8) | 1;       // Timer1 prescaler 1: 16 MHz / 510 = 31.4 kHz
    analogWrite(PIN_HV, DUTY);
  } else {
    analogWrite(PIN_HV, 0);             // pin low, PWM disconnected
  }
  hv = on;
}

// ---------------------------------------------------------------- reports
void printTube() {
  Serial.print(F("anode: "));
  if (tube < 0) { Serial.println(F("none")); return; }
  printItem(TUBE_TXT, tube, '|');
  Serial.print(F(", pin D"));
  Serial.print(ANODE_PIN[tube]);
  Serial.println(steady ? F(", STEADY") : F(", 13.5 % duty"));
}

void printDigit(uint8_t d) {
  uint8_t c = DIGIT_CODE[d];
  Serial.print(F("digit "));
  Serial.print(d);
  Serial.print(F(" = code "));
  Serial.print(c);
  Serial.print(F(": U2/U17 pin "));
  Serial.print(Q_PIN[c]);
  Serial.print(F(" low -> XS11."));
  Serial.print(XS11_PIN[d]);
  Serial.print(F(" (IN-12), XS12."));
  Serial.print(XS12_PIN[d]);
  Serial.println(F(" (IN-17)"));
}

void printIn15() {
  Serial.print(F("IN-15B (U15) "));
  if (c15 > 9) Serial.print(F("blank"));
  else {
    Serial.print(F("code ")); Serial.print(c15); Serial.print(' ');
    printItem(G_U15, c15, ' ');
    if (U15_XS12[c15]) { Serial.print(F(": pin ")); Serial.print(Q_PIN[c15]); Serial.print(F(" low -> XS12.")); Serial.print(U15_XS12[c15]); }
  }
  Serial.print(F(" | IN-15A (U16) "));
  if (c16 > 9) Serial.println(F("blank"));
  else {
    Serial.print(F("code ")); Serial.print(c16); Serial.print(' ');
    printItem(G_U16, c16, ' ');
    Serial.print(F(": pin ")); Serial.print(Q_PIN[c16]); Serial.print(F(" low -> XS12.")); Serial.println(U16_XS12[c16]);
  }
}

void applyLeds() {
  uint8_t b = 0;
  if (ledState == 1) b = 0xFF;
  else if (ledState >= 2 && ledState <= 9) b = 1 << (ledState - 2);
  mcpWrite(0x13, b);
  digitalWrite(PIN_M, (ledState == 1 || ledState == 10) ? HIGH : LOW);
  digitalWrite(PIN_BACKL, ledState ? HIGH : LOW);   // VT20 grounds BL_K
  Serial.print(F("LEDs: "));
  if (ledState == 0) Serial.println(F("off"));
  else if (ledState == 1) Serial.println(F("all nine on (VT20 on, GPB0-7 high, D12 high)"));
  else if (ledState == 10) Serial.println(F("HL9, the m, alone (D12 -> R53 -> XS25.4)"));
  else {
    uint8_t k = ledState - 2;
    Serial.print(F("HL")); Serial.print(k + 1);
    Serial.print(F(" alone (GPB")); Serial.print(k);
    Serial.print(F(", RN1 pins ")); Serial.print(8 - k); Serial.print('-'); Serial.print(9 + k);
    Serial.print(F(", XS")); Serial.print(BL_STRIP[k]); Serial.print('.'); Serial.print(BL_PIN[k]);
    Serial.println(')');
  }
}

void scanI2C() {
  // the idle bus first: R54 / R55 (4k7) hold SDA and SCL high; the AVR's own pull-ups are off here
  Wire.end();
  pinMode(A4, INPUT);
  pinMode(A5, INPUT);
  delay(2);
  bool sda = digitalRead(A4), scl = digitalRead(A5);
  Wire.begin();
#if defined(WIRE_HAS_TIMEOUT)
  Wire.setWireTimeout(25000, true);
#endif
  Serial.print(F("idle bus: SDA ")); Serial.print(sda ? F("high") : F("LOW"));
  Serial.print(F(", SCL ")); Serial.print(scl ? F("high") : F("LOW"));
  Serial.println((sda && scl) ? F(" - ok") : F(" - a line held low or a pull-up missing (R54 / R55)"));
  busOk = sda && scl;
  if (!busOk) {                         // a stuck line can hang an AVR core without Wire timeouts
    Serial.println(F("  scan skipped: find the short first (U3 pins 12/13, U13 pins 3/4, R54, R55)"));
    return;
  }
  bool mcp = false, rtc = false;
  uint8_t n = 0;
  for (uint8_t a = 0x08; a < 0x78; a++) {
    Wire.beginTransmission(a);
    if (Wire.endTransmission() != 0) continue;
    n++;
    Serial.print(F("  0x")); if (a < 16) Serial.print('0'); Serial.print(a, HEX); Serial.print(F("  "));
    if (a == MCP_ADDR) { mcp = true; Serial.println(F("MCP23017, U3 - expected")); }
    else if (a > MCP_ADDR && a <= 0x27) Serial.println(F("an MCP23017 at the wrong address: U3 pins 15-17 must be grounded"));
    else if (a == RTC_ADDR) { rtc = true; Serial.println(F("DS3231, the RTC module in U13 - expected")); }
    else if (a >= 0x50 && a <= 0x57) Serial.println(F("EEPROM on the RTC module (AT24C32 class) - fine if the module has one"));
    else Serial.println(F("unknown device"));
  }
  Serial.print(n); Serial.println(F(" device(s)"));
  if (!mcp) Serial.println(F("  0x20 MISSING: U3 not fitted, turned round, or no +5 V on its pin 9"));
  if (!rtc) Serial.println(F("  0x68 MISSING: the module not fitted, or its pins in another order (gate 6: - NC C D +)"));
  if (mcp) {
    mcpInit();
    applyLeds();
    Serial.println(mcpOk ? F("  MCP23017 takes register writes and reads them back") : F("  MCP23017 answers but did not read back its registers"));
  }
  if (rtc) {
    int s = readReg(RTC_ADDR, 0), m = readReg(RTC_ADDR, 1), h = readReg(RTC_ADDR, 2);
    int st = readReg(RTC_ADDR, 0x0F), tm = readReg(RTC_ADDR, 0x11), tl = readReg(RTC_ADDR, 0x12);
    if (s >= 0 && m >= 0 && h >= 0) {
      Serial.print(F("  DS3231 time "));
      Serial.print((h >> 4) & 3); Serial.print(h & 15); Serial.print(':');
      Serial.print(m >> 4); Serial.print(m & 15); Serial.print(':');
      Serial.print((s >> 4) & 7); Serial.print(s & 15);
      if (tm >= 0 && tl >= 0) { Serial.print(F(", ")); Serial.print((int8_t)tm + (tl >> 6) * 0.25); Serial.print(F(" C")); }
      if (st >= 0 && (st & 0x80)) Serial.print(F(", OSF set: the clock stopped since it was last set (new battery?)"));
      Serial.println();
    }
  }
}

void printLive() {
  int a6 = analogRead(A6), a7 = analogRead(A7);
  uint8_t pos = (a6 + 102) / 205 + 1;               // the firmware's own rounding (ts06pair.ino)
  int ideal = (1023L * (pos - 1) + 2) / 5;          // 0 205 409 614 818 1023
  const int LV[4] = {1023, 682, 512, 409};           // open, FIELD, SUB, both
  uint8_t best = 0;
  for (uint8_t i = 1; i < 4; i++) if (abs(a7 - LV[i]) < abs(a7 - LV[best])) best = i;
  Serial.print(F("A6 ")); Serial.print(a6);
  Serial.print(F(" = MODE ")); Serial.print(pos); Serial.print(' ');
  printItem(MODE_TXT, pos - 1, '|');
  Serial.print(F(" (")); Serial.print(a6 - ideal >= 0 ? F("+") : F("")); Serial.print(a6 - ideal);
  Serial.print(F(")  A7 ")); Serial.print(a7);
  Serial.print(best == 0 ? F(" = levers open") : best == 1 ? F(" = FIELD") : best == 2 ? F(" = SUB") : F(" = FIELD+SUB"));
  Serial.print(F(" (")); Serial.print(a7 - LV[best] >= 0 ? F("+") : F("")); Serial.print(a7 - LV[best]);
  Serial.print(F(")  - ")); Serial.print(digitalRead(PIN_MINUS) ? F("up") : F("DOWN"));
  Serial.print(F("  + ")); Serial.println(digitalRead(PIN_PLUS) ? F("up") : F("DOWN"));
}

void cycleOnce() {
  if (cycleStep > 10) cycleStep = 0;
  if (cycleStep == 10) {
    digitCode = c15 = c16 = 15;
    writeDecoders();
    Serial.println(F("-- all four decoders blank (code 15): no strip pin low --"));
  } else {
    digitCode = DIGIT_CODE[cycleStep];
    c15 = c16 = cycleStep;
    writeDecoders();
    printDigit(cycleStep);
    Serial.print(F("        "));
    printIn15();
  }
  cycleStep++;
}

void help() {
  Serial.println(F("\nTS06 pair bring-up. 9600 baud.  ? help   H/h HV on/off   i I2C scan"));
  Serial.println(F("0-9 digit on U2+U17   g next IN-15 code   a / p  AM / PM   b blank   c cycle all decoders"));
  Serial.println(F("t next anode   x anodes off   s steady burst   k colon   l LEDs   r live A6/A7/buttons"));
  Serial.print(F("HV ")); Serial.print(hv ? F("ON  (185 V on C7, the optos, the anode and colon resistors)") : F("off"));
  Serial.print(F("   colon ")); Serial.print(colon ? F("on") : F("off"));
  Serial.print(F("   MCP23017 ")); Serial.println(mcpOk ? F("ok") : F("not answering (press i)"));
  printTube();
  if (digitCode > 9) Serial.println(F("U2/U17 blank"));
  else for (uint8_t d = 0; d < 10; d++) if (DIGIT_CODE[d] == digitCode) printDigit(d);
  printIn15();
}

// ---------------------------------------------------------------- setup / loop
void setup() {
  // everything safe before anything else: converter clock low, anodes low, decoders blank
  pinMode(PIN_HV, OUTPUT); digitalWrite(PIN_HV, LOW);
  for (uint8_t i = 0; i < 6; i++) { pinMode(ANODE_PIN[i], OUTPUT); digitalWrite(ANODE_PIN[i], LOW); }
  DDRC |= 0x0F;
  PORTC = (PORTC & 0xF0) | 0x0F;        // code 15 on U2 and U17: nothing lit
  pinMode(PIN_COLON, OUTPUT); digitalWrite(PIN_COLON, LOW);
  pinMode(PIN_BACKL, OUTPUT); digitalWrite(PIN_BACKL, LOW);
  pinMode(PIN_M, OUTPUT); digitalWrite(PIN_M, LOW);
  pinMode(PIN_MINUS, INPUT_PULLUP);
  pinMode(PIN_PLUS, INPUT_PULLUP);

  Serial.begin(BAUD);
  bool busIdle = digitalRead(A4) && digitalRead(A5);   // R54 / R55 hold an idle bus high
  Wire.begin();
#if defined(WIRE_HAS_TIMEOUT)
  Wire.setWireTimeout(25000, true);     // a missing or stuck chip must not hang the sketch
#endif
  busOk = busIdle;
  if (busOk) mcpInit();               // both IN-15 blank, LEDs off (harmless if U3 is absent)
  else Serial.println(F("I2C: SDA or SCL is low at reset - not touching the bus (press i)"));

  // Timer2: fast PWM, prescaler 8, overflow interrupt at 7812.5 Hz (the clock's tick)
  TCCR2A = _BV(WGM21) | _BV(WGM20);
  TCCR2B = (TCCR2B & 0xF8) | 2;
  TIMSK2 = _BV(TOIE2);

  help();
}

void loop() {
  uint32_t now = millis();
  if (steady && hv && now - burstStart >= BURST_MS) {
    steady = false;
    Serial.println(F("steady burst over: back to 13.5 %"));
  }
  if (live && now - lastLive >= 250) { lastLive = now; printLive(); }
  if (cycling && now - lastCycle >= 1000) { lastCycle = now; cycleOnce(); }

  if (!Serial.available()) return;
  char ch = Serial.read();
  if (ch >= '0' && ch <= '9') {
    cycling = false;
    digitCode = DIGIT_CODE[ch - '0'];
    writeDecoders();
    printDigit(ch - '0');
    return;
  }
  switch (ch) {
    case '?': help(); break;
    case 'H': setHV(true);  Serial.println(F("HV ON: the converter is running. One hand; meter leads clipped before power-up.")); break;
    case 'h': setHV(false); Serial.println(F("HV off: C7 is still charged - wait 15 s and check it is under 10 V")); break;
    case 'i': scanI2C(); break;
    case 'g': cycling = false; c15 = c16 = (c15 == 9) ? 15 : (c15 > 9) ? 0 : c15 + 1; writeDecoders(); printIn15(); break;
    case 'a': cycling = false; c15 = 2; c16 = 15; writeDecoders(); printIn15(); break;
    case 'p': cycling = false; c15 = 15; c16 = 8; writeDecoders(); printIn15(); break;
    case 'b': cycling = false; digitCode = c15 = c16 = 15; writeDecoders(); Serial.println(F("all four decoders blank")); break;
    case 'c': cycling = !cycling; cycleStep = 0; lastCycle = now - 1000; Serial.println(cycling ? F("cycling (c stops)") : F("cycle stopped")); break;
    case 't': selectTube(tube >= 5 ? -1 : tube + 1); printTube(); break;
    case 'x': selectTube(-1); printTube(); break;
    case 's':
      if (tube < 0) { Serial.println(F("no anode selected: t first")); break; }
      if (steady) { steady = false; printTube(); break; }
      burstStart = now; steady = true;
      Serial.println(hv ? F("steady burst, 5 s") : F("steady (HV off: until t, x or s again)"));
      printTube();
      break;
    case 'k': colon = !colon; digitalWrite(PIN_COLON, colon); Serial.println(colon ? F("colon on (VT1 conducting)") : F("colon off")); break;
    case 'l': ledState = (ledState >= 10) ? 0 : ledState + 1; applyLeds(); break;
    case 'r': live = !live; break;
    default: break;                      // line endings and anything else: ignored
  }
}
