/*
  TERMINAL-06 // SEC cathode mapping jig
  --------------------------------------------------------------
  Run this ONCE, on one board, before you build the first SEC module.
  It tells you which physical K155ID1 output pin carries which digit,
  so the seconds-module harness can be crimped the same way ten times.

  Do NOT guess this from a datasheet you found online - Soviet K155ID1
  and Western SN74141 parts are pin compatible but the marking on
  surplus chips is not always what it claims. Measure it.

  METHOD
    1. Unplug the tube board. HV OFF - pull the boost transistor's supply,
       or simply leave the HV rail unloaded and DO NOT touch the tube pads.
       This sketch never enables the boost oscillator on D9, so the board
       stays at 5 V only. Verify with a meter before probing.
    2. Upload. Open the Serial Monitor at 9600 baud.
    3. The sketch parks on one BCD code at a time, 3 s each, and prints it.
    4. With a multimeter on continuity/diode or DC volts, find which
       K155ID1 output pin is pulled LOW (near 0 V) during each step.
    5. Write the pin number into the table below. That is your harness map.

  RESULT TABLE - fill in once, keep with the build documents:

      digit 0 -> K155ID1 pin ____      digit 5 -> K155ID1 pin ____
      digit 1 -> K155ID1 pin ____      digit 6 -> K155ID1 pin ____
      digit 2 -> K155ID1 pin ____      digit 7 -> K155ID1 pin ____
      digit 3 -> K155ID1 pin ____      digit 8 -> K155ID1 pin ____
      digit 4 -> K155ID1 pin ____      digit 9 -> K155ID1 pin ____

  Then wire SEC connector J2 pin N to the K155ID1 pin for digit N, and
  the IN-17 cathode for digit N to J2 pin N on the module. One mask,
  no firmware changes.
  --------------------------------------------------------------
*/

#define BOARD_TYPE 0      // MUST match the value in nixieClock_TS06.ino

#define DECODER0 A0
#define DECODER1 A1
#define DECODER2 A2
#define DECODER3 A3

#define STEP_MS 3000

// same masks as the clock firmware - the jig walks DISPLAYED digits, so the
// pin you record is exactly the pin that digit needs on the SEC module
#if (BOARD_TYPE == 0)
const byte digitMask[] = {7, 3, 6, 4, 1, 9, 8, 0, 5, 2};
#elif (BOARD_TYPE == 1)
const byte digitMask[] = {2, 8, 1, 9, 6, 4, 3, 5, 0, 7};
#elif (BOARD_TYPE == 2)
const byte digitMask[] = {9, 8, 0, 5, 4, 7, 3, 6, 2, 1};
#else
const byte digitMask[] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9};
#endif

void setup() {
  Serial.begin(9600);
  pinMode(DECODER0, OUTPUT);
  pinMode(DECODER1, OUTPUT);
  pinMode(DECODER2, OUTPUT);
  pinMode(DECODER3, OUTPUT);
  // every anode driver stays off - nothing lights, nothing draws HV
  for (byte p = 2; p <= 6; p++) { pinMode(p, OUTPUT); digitalWrite(p, LOW); }
  pinMode(13, OUTPUT); digitalWrite(13, LOW);
  pinMode(9, OUTPUT);  digitalWrite(9, LOW);   // boost oscillator OFF

  Serial.println(F("TERMINAL-06 cathode mapping jig"));
  Serial.println(F("Confirm the HV rail reads ~0 V before probing."));
}

void loop() {
  for (byte d = 0; d < 10; d++) {
    byte v = digitMask[d];          // the code the clock sends for this digit
    // same bit order the clock firmware uses
    digitalWrite(DECODER3, bitRead(v, 0));
    digitalWrite(DECODER1, bitRead(v, 1));
    digitalWrite(DECODER0, bitRead(v, 2));
    digitalWrite(DECODER2, bitRead(v, 3));

    Serial.print(F("DISPLAYED DIGIT "));
    Serial.print(d);
    Serial.print(F("   (BCD "));
    Serial.print(v);
    Serial.println(F(")  -  record the K155ID1 output pin that is LOW"));
    delay(STEP_MS);
  }
  Serial.println(F("--- cycle complete, repeating ---"));
}
