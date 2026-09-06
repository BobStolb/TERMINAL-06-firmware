/*
  TERMINAL-06 // six-digit nixie clock firmware
  --------------------------------------------------------------
  Derived from AlexGyver's NixieClock v2.5 (MIT-spirited open project,
  https://github.com/AlexGyver/NixieClock_v2) with substantial changes:

    * 4 tubes -> 6 tubes  (4x IN-12 HH:MM + 2x IN-17 SS on the SEC module)
    * anode drivers 5 and 6 on D2 (freed from the buzzer) and D13
    * multiplex ISR rewritten with direct port access (Timer2 prescaler
      stays at AlexGyver's 8) => 7812.5 Hz ISR, 50 Hz whole-display
      refresh with 640 us of optocoupler dead time - the measured
      ghost-free setting (see MULTIPLEX TIMING below and isr.ino)
    * 3 buttons -> 2 buttons + 1 PROGRAM/RUN lever on D12
    * alarm/buzzer removed (D2 reused)
    * anti-poisoning cycle and glitch effect extended over all 6 tubes

  Keep the original attribution if you redistribute the source.
  --------------------------------------------------------------

  CONTROLS
    Lever SW3 down = PROGRAM
      BTN_SET  click : switch field   HH <-> MM   (blinking pair)
      BTN_ADJ  click : +1
      BTN_ADJ  hold  : fast +1
      lever back up  : time written to RTC, seconds zeroed

    Lever SW3 up = RUN
      BTN_SET  click : backlight mode  (breathe / steady / off)
      BTN_SET  hold  : glitch effect on/off
      BTN_ADJ  click : digit transition effect (6 of them)

    Lever SW1 = mains          (hard cut, no pin)
    Lever SW2 = tube backlight (hard cut of the LED +5V rail, no pin)
*/

// ************************** SETTINGS **************************
#define BOARD_TYPE 0
// hours/minutes board type:
// 0 - IN-12 turned (tubes mounted the right way up)   <-- confirmed on this board
// 1 - IN-12 (tubes upside down)   <-- AlexGyver IN-12 board as shipped
// 2 - IN-14
// 3 - custom

#define DUTY 190        // boost PWM duty. Sets HV. 180 ~ 175 V, 190 ~ 185 V.
                        // Six tubes need a little more headroom than four:
                        // tune on the bench for 180-190 V no-load (see manual).

// ==================  MULTIPLEX TIMING ==================
/*
  Every number the multiplex ISR uses is derived from these two. Nothing
  else in the firmware may assume a slot length or a brightness range -
  hardcoding those is what caused the ghosting bug this timing fixes.

  WHAT WE ARE OPTIMISING FOR: ghost-free digits, not camera-clean video.
  An earlier revision chased a ~400 Hz refresh so the display would not
  band on camera for the product video, and moved Timer2 to prescaler 1
  to get it. That was the wrong trade. Ghosting is a defect every owner
  looks at every day; 60 fps video flicker is a photography problem we
  can solve with a shutter speed. The camera requirement is dropped, and
  everything it justified - the prescaler rewrite included - goes with it.

  Timer2 runs at prescaler 8, AlexGyver's original: one tick =
  1 / 7812.5 Hz = 128 us. Eight times the tick length means the dead time
  we need costs only a handful of ticks instead of eighteen, which is
  what makes a short slot and a bright display compatible. It also cuts
  the ISR from ~34 % of the CPU to ~4 %.

  SLOT_TICKS   ticks each tube owns: brightness steps plus dead time.
  DEAD_TICKS   ticks at the END of every slot with the anode off AND the
               decoder blanked. This is the ghost margin. The TLP627's
               Darlington output keeps conducting for a few hundred us
               after its drive is removed, so the next tube's digit must
               not reach the shared cathode bus until that tail has died.
               640 us is the bench-measured ghost-free figure for six
               tubes. 256 us (what stock INDI_BRIGHT 24 would give here)
               sits in the band where faint ghosting was still visible,
               which is why INDI_BRIGHT is 21 and not 24 - do not
               "restore" it.

  Derived:
    frame rate = 7812.5 / SLOT_TICKS / NUM_INDI = 7812.5 / 26 / 6 = 50.1 Hz
    dead time  = DEAD_TICKS * 128 us            = 640 us
    slot duty  = MAX_BRIGHT / SLOT_TICKS        = 21 / 26 = 81 %
    per-tube duty = MAX_BRIGHT / (SLOT * NUM)   = 21 / 156 = 13.5 %

  50 Hz is the whole-display refresh. It is above flicker fusion for a
  steady glow and is what the stock firmware always ran, but it WILL beat
  against camera shutters - that is the accepted cost, not an oversight.
*/
#define SLOT_TICKS 26       // ticks per tube slot
#define DEAD_TICKS 5        // forced-blank ticks at the end of each slot

// Highest brightness a tube may be given. The ISR clamps to this, so the
// dead-time gap can never be eaten by turning the brightness up.
#define MAX_BRIGHT (SLOT_TICKS - DEAD_TICKS)

// ================  BENCH BUILD FLAGS  ==================
/*
  Both of these deliberately light digits that are not the current time,
  which makes it impossible to tell real ghosting from intended effect
  when judging the display by eye. Set either to 0 to compile it out for a
  bench session; the code stays in the tree either way.
*/
#define GLITCH_ENABLED 0    // 0 = no random "bad contact" flicker
#define BURN_ENABLED   0    // 0 = no anti-poisoning cathode sweep

// ======================= EFFECTS =======================
byte FLIP_EFFECT = 1;   // stored in EEPROM, changed with BTN_ADJ
// 0 none / 1 crossfade / 2 count / 3 cathode scroll / 4 train / 5 elastic

// =======================  BRIGHTNESS =======================
#define NIGHT_LIGHT 1
#define NIGHT_START 23
#define NIGHT_END 7

// Brightness is measured in ISR ticks, so the usable range is
// 1 - MAX_BRIGHT (21). Values above MAX_BRIGHT are clamped by the ISR and
// behave identically to MAX_BRIGHT - they do not get brighter.
// Dimmer is always safer: dead time is SLOT_TICKS - brightness, so lowering
// a brightness value only ever widens the ghost margin.
#define INDI_BRIGHT 21      // day digit brightness   (1 - 21) - see the
                            // MULTIPLEX TIMING note before raising this
#define INDI_BRIGHT_N 6     // night digit brightness (1 - 21)

#define SEC_BRIGHT_TRIM 4   // added to the seconds tubes only.
                            // IN-17 is a small tube on the same 1/6 duty as
                            // the IN-12s; a few ticks balance them by eye.
                            // Result is clamped to MAX_BRIGHT.
                            // NOTE: with INDI_BRIGHT sitting at MAX_BRIGHT
                            // this trim has no headroom left - lower
                            // INDI_BRIGHT if the seconds need lifting.

#define DOT_BRIGHT 35
#define DOT_BRIGHT_N 15

#define BACKL_BRIGHT 250
#define BACKL_BRIGHT_N 50
#define BACKL_MIN_BRIGHT 20
#define BACKL_PAUSE 400

// =======================  GLITCHES =======================
#define GLITCH_MIN 30
#define GLITCH_MAX 120

// ======================  BLINKING =======================
#define DOT_TIME 500
#define DOT_TIMER 20

#define BACKL_STEP 2
#define BACKL_TIME 5000

// ==================  ANTI-POISONING ====================
#define BURN_TIME 10
#define BURN_LOOPS 3
#define BURN_PERIOD 15      // minutes

// *********************** INTERNALS ***********************
byte BACKL_MODE = 0;
// ms per effect step. Index 1 (crossfade) steps brightness, so its step
// COUNT is indiMaxBright and its duration scales with the brightness range.
// Retune it whenever MAX_BRIGHT changes: interval = 130 * 23 / MAX_BRIGHT,
// which holds the fade at the ~6 s it has always been (the 23-step, 130 ms
// original). At MAX_BRIGHT 21 that is 142. The other effects step digits,
// not brightness, and are unaffected by the slot length.
byte FLIP_SPEED[] = {0, 142, 50, 40, 70, 70};
byte FLIP_EFFECT_NUM = sizeof(FLIP_SPEED);
boolean GLITCH_ALLOWED = 1;

#define NUM_INDI 6          // total tubes
#define NUM_HM   4          // tubes carrying hours+minutes (effects act on these)

// ---------------- pins ----------------
#define KEY4 2      // anode, seconds TENS   (was PIEZO)
#define KEY0 3      // anode, hours tens
#define KEY1 4      // anode, hours units
#define KEY2 5      // anode, minutes tens
#define KEY3 6      // anode, minutes units
#define BTN_SET 7   // button 1
#define BTN_ADJ 8   // button 2
#define GEN 9       // HV boost oscillator
#define DOT 10      // neon dot / colon
#define BACKL 11    // tube backlight PWM
#define LEVER 12    // SW3 PROGRAM(LOW) / RUN(HIGH)
#define KEY5 13     // anode, seconds UNITS

// decoder K155ID1 (74141)
#define DECODER0 A0
#define DECODER1 A1
#define DECODER2 A2
#define DECODER3 A3

// ---------------- tube maps ----------------
#if (BOARD_TYPE == 0)
const byte digitMask[] = {7, 3, 6, 4, 1, 9, 8, 0, 5, 2};
const byte opts[NUM_INDI] = {KEY0, KEY1, KEY2, KEY3, KEY4, KEY5};
const byte cathodeMask[] = {1, 6, 2, 7, 5, 0, 4, 9, 8, 3};

#elif (BOARD_TYPE == 1)
const byte digitMask[] = {2, 8, 1, 9, 6, 4, 3, 5, 0, 7};
const byte opts[NUM_INDI] = {KEY3, KEY2, KEY1, KEY0, KEY4, KEY5};
const byte cathodeMask[] = {1, 6, 2, 7, 5, 0, 4, 9, 8, 3};

#elif (BOARD_TYPE == 2)
const byte digitMask[] = {9, 8, 0, 5, 4, 7, 3, 6, 2, 1};
const byte opts[NUM_INDI] = {KEY3, KEY2, KEY1, KEY0, KEY4, KEY5};
const byte cathodeMask[] = {1, 0, 2, 9, 3, 8, 4, 7, 5, 6};

#elif (BOARD_TYPE == 3)
const byte digitMask[] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9};
const byte opts[NUM_INDI] = {KEY0, KEY1, KEY2, KEY3, KEY4, KEY5};
const byte cathodeMask[] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9};
#endif

/*
  The SEC module routes each IN-17 cathode to the SAME K155ID1 output the
  IN-12s use for that digit, so one digitMask covers all six tubes.
  If you wire the IN-17s differently you will need a second mask - see the
  build manual, section "SEC module cathode routing".
*/
