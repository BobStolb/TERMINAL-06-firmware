/*
  BOARD_TYPE 4 only: TS06-DISP + TS06-DRV, the through-hole pair
  (tools/ts06pair.py), with the TS06-FASCIA panel on its cable J1.
  Everything below is compiled out for types 0-3.

  What this board has that the inherited one does not, as the firmware sees it:

    D12   the "m" LED: D12 -> R53 220R -> HL9 anode, cathode on BL_K, the
          backlight's common cathode switched by the MPSA42 on D11. Not a lever.
          Driven high once at setup, so it is on and follows the backlight's
          brightness, breathing and off modes like the other eight LEDs.

    I2C   U3, an MCP23017 at 0x20 (A0-A2 grounded), on A4/A5 with the RTC.
            port A  two K155ID1 nibbles for the IN-15 pair, inputs A D B C:
                      GPA3..0 -> U15 (IN-15B)     GPA7..4 -> U16 (IN-15A)
            port B  the anodes of backlight LEDs HL1-HL8 through RN1
                    (8 x 220R), GPBk -> HL(k+1). Their cathodes are BL_K,
                    so D11's PWM is still the one brightness control.

    J1    the fascia, pin order +5V GND A6 A7 D7 D8:
            A6  MODE rotary, five 4.7k 1% across the rail; positions
                1 NORMAL, 2 SET TIME, 3 DISPLAY, 4 AMBIENT, 5 FORMAT/DATE,
                6 INFO land at 0/1/2/3/4/5 V = ADC 0/205/409/614/818/1023
            A7  levers FIELD and SUB: 10k pull-up, FIELD closes 20k and SUB
                10k to ground = ADC 1023 open / 682 FIELD / 512 SUB / 409 both
            D7  the "-" button (to ground)  = BTN_SET, as on types 0-3
            D8  the "+" button (to ground)  = BTN_ADJ
          100 nF on A6 and A7 at the driver-board end (C5, C6).
          There is no PROGRAM/RUN lever anywhere on the panel: see readLever().

  TODO - not written yet (TERMINAL-06-spec.txt section 1, rev B controls):
    * The rotary's six screens. Today SET TIME is PROGRAM and the other five
      positions are all RUN, i.e. the two-button UI of types 0-3 unchanged:
      in RUN "-" cycles the backlight mode (hold: glitch on/off) and "+"
      cycles the transition effect; in PROGRAM "-" switches HH <-> MM and
      "+" counts up. NORMAL and INFO are meant to ignore every input.
    * The spec's agreement filter on A6 (five identical readings ~10 ms
      apart). Only the 5 ms confirm-read of buttonsTick() guards it now.
      Turning the knob past SET TIME enters and leaves PROGRAM, and leaving
      writes the RTC with the seconds zeroed, as flicking SW3 does.
    * A7 is not read. On SET TIME the spec has FIELD pick HH/MM and the
      buttons count down/up (bumpTime(-1) already exists).
    * IN-15 content: AM/PM from the RTC hour, the NORMAL idle cycle. Port A
      is held at code 15, both tubes dark. The glyph <-> decoder output
      tables are GLYPH_Q in tools/ts06pair.py.
    * Per-LED backlight on port B (all eight are on), and whether "m" is
      always on or 12-hour-mode only.
*/
#if (BOARD_TYPE == 4)

// ---------------- MCP23017 (U3) ----------------
#define MCP_ADDR   0x20
#define MCP_IODIRA 0x00     // register addresses in the IOCON.BANK = 0 map,
#define MCP_IODIRB 0x01     // the power-on default
#define MCP_GPIOA  0x12     // writing GPIOx writes the output latch OLATx
#define MCP_GPIOB  0x13

static void mcpWrite(uint8_t reg, uint8_t val) {
  Wire.beginTransmission(MCP_ADDR);
  Wire.write(reg);
  Wire.write(val);
  Wire.endTransmission();
}

// Called from setup() where the other types set SW3's pin up: before the HV
// converter starts, before rtc.begin(), before the multiplex ISR is armed.
void pairInit() {
  pinMode(M_LED, OUTPUT);
  digitalWrite(M_LED, HIGH);

  // Bring the bus up here, ahead of the RTC. rtc.begin() (RTClib 1.2.0) is
  // only a second Wire.begin(), which just reloads the TWI registers.
  Wire.begin();

  // U3's RESET pin is tied to +5V, so the expander keeps its registers through
  // a Nano reset: write everything this firmware relies on, every boot.
  // Register 0x05 is IOCON in the BANK = 1 map, so a 0 there puts a chip left
  // in BANK = 1 back into BANK = 0. In BANK = 0 it is GPINTENB, already 0.
  mcpWrite(0x05, 0x00);

  // Latches first, then directions, so each pin goes from input straight to
  // its final level and never drives the power-on latch value 0x00 (code 0,
  // which would light a glyph on both IN-15s).
  mcpWrite(MCP_GPIOA, 0xFF);    // code 15 into both K155ID1s: 10-15 light nothing
  mcpWrite(MCP_GPIOB, 0xFF);    // HL1-HL8 sourced; D11 sets their brightness
  mcpWrite(MCP_IODIRA, 0x00);   // all outputs
  mcpWrite(MCP_IODIRB, 0x00);
}

// ---------------- fascia ----------------
#define ROTARY A6
#define ROT_SET_TIME 2

// MODE rotary position, 1-6. Rounds to the nearest tap, so each threshold sits
// halfway (~102 codes) between two taps 205 codes apart. The taps are
// calculated from the ladder, not measured: check them on the bench with the
// real panel and cable.
byte rotaryPos() {
  return (analogRead(ROTARY) + 102) / 205 + 1;
}

// Same contract as digitalRead(LEVER) on types 0-3: HIGH = RUN, LOW = PROGRAM.
// The panel has no PROGRAM/RUN lever. Its "set the time" control is the MODE
// rotary's SET TIME position, so that is PROGRAM and the rest is RUN.
boolean readLever() {
  return rotaryPos() != ROT_SET_TIME;
}

#endif
