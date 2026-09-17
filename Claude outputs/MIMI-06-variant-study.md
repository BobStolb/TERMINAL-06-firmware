# MIMI-06 «KURO» — cute variant of TERMINAL-06, with a VFD (Rev 2.1)

**Concept plates (Rev 2.1): https://claude.ai/code/artifact/c072e08f-a478-4486-85bf-ff68926cd506**
Superseded MILK plates (Rev 1): https://claude.ai/code/artifact/d0f9fdf0-f955-4377-b34e-8ab33b046b72

**Rev 2 (01.09.26) — two things resolved at once.**

1. **The display path is chosen: the FUTABA character-VFD family.** The 128 × 32 graphic panel this
   concept was drawn around was never a sourcing path — it was a datasheet. The 16-digit FUTABA
   variant is 150 × 25 mm and lands **inside the 148 × 26 mm bezel already cut for a display that did
   not exist.**
2. **The shell inverts from milk white to ink black.** Dark cyberpunk colourway, cute face retained —
   and it deletes two production problems and one filament order.

**Rev 2.1 (02.09.26) — drawn views, and the panel is alive between states.** A three-quarter hero and
a general-arrangement sheet (front, right profile, plan) now exist, with the VFD drawn at its real
16 × 5 × 7 cell geometry rather than as a placeholder. The published page animates the panel
**within** each state, not only between them — see §2.4.

**Scope note, flagged honestly:** the "dark shell, cute face retained" reading was taken as a
recommendation when the question went unanswered. The alternatives were *hard cyberpunk, retire the
face* and *two colourways from one chassis*. Cheap to change.

---

## 1. Form

- **176 W × 96 D × 112 H mm chassis, 150 mm overall with glass.** Upright, front face raked 8°.
- **Tube deck on top, inset and proud** — MIMI takes the same case revision TERMINAL-06 took in its
  Rev E, for the same reason: the old upright put the tubes in a trench.
- **Plinth 154 W × 44 D × 14 H, inset 11 mm each side, set back 26 mm** from the front edge. *(Sized
  from the drawing, not asserted — the tube row spans x = 13.5 → 162.5 and the plinth has to clear it.
  TERMINAL-06 Rev E made exactly this mistake and the plan view caught it.)*
- The VFD sits on the rake below the tubes as a wide grin; the shared control panel runs underneath.
  Face reads as a face at three metres, which was always the point.
- **Ears**: kept, but they lose their round — **hard-edged fins at the rear top corners with a single
  magenta strip down each**. Print as part of the top deck so there is no seam; overhangs under 45°.
- Tube X unchanged from the shared board: ИН-12А at 24.5 / 49.5 / 81.5 / 106.5, ИНС-1 colon at 65.5,
  ИН-17 at 137 / 155. Control X unchanged: rotary 42, levers 100 / 120, buttons 146 / 164.
- Screen labels stay lowercase: run · time · glow · amb · info · date.

**Provisional:** every Rev 2.1 dimension is derived from the shared board and the chosen module. One
test print before the chassis is committed.

### KURO palette

SUMI #07070B · SLATE #15151F · NEON #FF2E88 · SIGNAL CYAN #21E6FF · LILAC #A06BFF ·
VFD #7CF5DC · NIXIE #FF9E36.

**Nothing in this product emits pink.** Magenta and cyan appear only in printed and anodised surfaces.
The three emitters are the VFD's ≈505 nm blue-green, the nixies' ≈605 nm orange, and the colon.

### Why KURO is cheaper to build than MILK

Rev 1 flagged that milk PETG shows layer lines, scuffs and fingerprints in every photograph, and
required a second bright low-contrast lighting set because a cream body on a dark background reads
grey. Going dark deletes both:

- **One filament batch across both products** — matte black PETG, same as TERMINAL-06.
- **No extra finishing pass** on visible layer lines.
- **One dark photography set** instead of two — and the two products now photograph as one shop.

The colourway was chosen for looks and pays for itself in production.

---

## 2. The display — path 2, decided

### 2.1 What was chased and closed

**Path 1 — a genuine 128 × 32 graphic VFD.** Four hunts, nothing buyable:

- New stock runs through industrial distributors at POS/ATM/medical pricing, not stocked or priced for
  a maker buying ten.
- The hobbyist VFD market is almost entirely **character-clock modules** — segment "88:88:88" types or
  small character-cell modules. There is no mass-produced, cheap, small-MOQ 128 × 32 *graphic* VFD.
- Genuine Noritake panels circulate as **pulls/surplus** on eBay and forums — real but sporadic, and
  no guarantee of ten matching tested units on a schedule.
- **Japan (26.08, `claude/JAPAN-lot-register.md` §K):** every VFD lot found is a **segment-type digit
  tube** — Ise Denshi DG10F1, NEC LD8062, Futaba DG12G, the clock-IC sets. A follow-up search for
  ドットマトリクス / GU-3000 / GU128 turned up nothing on Yahoo Auctions or Mercari.
- **ПИУ-2 / ГИПС-16-1 (Avito, 2 900 ₽, bought):** a Soviet gas-discharge **plasma** indicator, not a
  VFD. 345–365 V, 16 positions of 7×5, driven through its own internal character-scan chip — fixed
  font, not arbitrary graphics, without reverse-engineering that driver. Fun, on-theme, **not a MIMI
  display.**
- **GU112X16 (Avito, 6 000 ₽):** real hardware — a currently-manufactured Noritake graphic VFD.
  **The seller sells finished clocks only and will not discuss the bare display.** Dead end because of
  the seller, not the part.

**Path 3 — substitute a modern OLED.** Cheap, ubiquitous, tiny MOQ, keeps the pixel-face art.
**Rejected:** not a VFD, no warm phosphor, and it breaks the "all the emitters here are the same
glowing-tube family" story that is most of MIMI's charm.

### 2.2 The chosen part

A manufacturer/reseller sells genuine **FUTABA-glass character VFDs** directly, with a manual and
driver source (user-supplied via a shared Drive folder) and stated technical support. The most
concretely purchasable lead found, and the first with a seller willing to sell the bare part.

**What it is:** an 8-bit 5×7 dot-matrix VFD, **SPI**, sold as bare screen / bare module / serial
module with its own driver board. ~10 mm thick, 4×M2 + 2×M3 mounting, EN solder jumper (J1) enables
the power stage. Same driver IC across the family.

| Variant | Size | vs MIMI's 148 × 26 window | Verdict |
|---|---|---|---|
| 6-digit | 75 × 20 mm | −73 mm | Too short to write anything |
| 8-digit | 93 × 20 mm | −55 mm | A face *or* a word, not both |
| **16-digit** | **150 × 25 mm** | **+2 / −1 mm** | **Take it.** Face plus text on one line |

**Command set:** set digit count · set brightness · power on · write a character at a position · write
a string from a position. Driver source in C for both 8051 and Arduino targets.

### 2.3 The consequence: faces become text, and that is the right answer

"Write a character at a position" reads like an ASCII-in, glyph-out font ROM. **If there is no
CGRAM-style "define this 5×7 pattern as character N" command, the expressions cannot be hand-drawn
pixel icons** — they become kaomoji strings.

That is not a fallback. **Kaomoji are what a 16-cell character display was born to do**, the asset
pipeline collapses from a bitmap toolchain (`vfd.py`) to a string table, and the look lands closer to
a 1980s Japanese appliance than a modern OLED pretending to be one.

Six states, exactly 16 cells each:

| State | 16 characters | Trigger |
|---|---|---|
| idle | `(^_^)  20:47 SUN` | default |
| greeting | `\(^O^)/ OKAERI  ` | motion, or dial back to RUN after 4 h idle |
| night | `(-_-)z  OYASUMI ` | ambient screen, or after 23:00 |
| alarm | `(*O*)  07:00 MON` | 60 s either side of alarm |
| wink | `(^_-) CATHODE OK` | the 03:00 anti-poisoning sweep — the clock says what the tubes are doing |
| setting | `(._.) SET: DIAL ` | dial off position 1 |

**Confirm CGRAM with the seller anyway** — it decides whether an ear-twitch is ever possible.

### 2.4 The panel is never a static image — Rev 2.1

A face that only changes when the state changes is a picture, not a character. Four cheap behaviours
make it alive, and **all four are just "write a character at a position" on a timer** — no extra
hardware, no CGRAM, single-digit bytes per update:

- **Blink.** Every ~4.2 s the eye cells swap to `-` for ~120 ms, occasionally twice. Two cells written.
- **Colon.** In idle and alarm, the `:` blanks on the half second. One cell written.
- **Breath.** In night, the `z` cycles `z` → `Z` → `z` → blank on ~420 ms. One cell.
- **Cursor.** In setting, the last cell blinks `_` while a value is live. One cell.
- **The state change itself is a left-to-right reveal**, one cell per frame — which is not a stylistic
  choice but literally what the module's own write command produces if you feed it in order. **The
  transition and the hardware are the same thing.**

Firmware cost is one 60 ms tick and a dirty-check so unchanged frames are never rewritten.

---

## 3. The pin finding — unchanged, and it still governs

Rev C moved the controls onto A6/A7 ladders, leaving exactly one spare digital pin (D12).
Electrically a serial display fits. **In time it does not, if driven the naive way.**

| Quantity | Value | Consequence |
|---|---|---|
| Timer2 multiplex ISR period | 16 µs | the clock's heartbeat |
| One anode slot | 416 µs | how long a single tube is lit |
| SoftwareSerial, one byte at 19 200 baud | **520 µs** | **longer than a whole digit slot**, interrupts off throughout |
| A 512-byte bitmap frame that way | ≈0.27 s | visible stall, one cathode left sitting lit |

**Use bit-banged SPI on D0/D1.** SPI's clock is self-timed by whichever side drives it, so a write
never needs a whole byte of interrupt-free framing — at most the instant around each clock edge. Cost:
a 1 kΩ series resistor and a two-pin jumper to lift the module during flashing, because D0/D1 see
bootloader chatter at reset. **D12 stays the real spare.** ~50 ₽, against the new main board an
earlier study called for.

The §2.4 animations make this easier, not harder: a blink is **two bytes**, not a frame.

**This is reasoning, not a bench result.** Measure it before ten units depend on it.

---

## 4. Deltas against TERMINAL-06 Rev E.1

| Item | TERMINAL-06 Rev E.1 | MIMI-06 KURO |
|---|---|---|
| Display | 4× ИН-12А, 2× ИН-17, ИНС-1 colon, ИН-15 AM/PM pair | identical **minus the ИН-15 pair**, **+ 16-digit FUTABA VFD** |
| Tube board | pitch 24.5 / 49.5 / 81.5 / 106.5 | **unchanged** |
| TS06-SEC | seconds + colon, 46 × 34 | **unchanged** (MCP23017s unpopulated) |
| Fascia | 237 × 52, 2.0 mm | **176 × 52 — no longer shared** |
| Controls | rotary + 2 МТ1 + 2 КМД-1, A6/A7 | **identical**, same 6-pin XS1 |
| Enclosure | 237 × 104 × 96 overall, open deck | 176 × 96 × 150 overall, open deck, ear fins |
| Plinth | 213 × 46 × 16, inset 12 | 154 × 44 × 14, inset 11 |
| 5 V rail | Nano's onboard regulator | **dedicated 12 V → 5 V buck, 1 A** |
| Display data | — | **bit-banged SPI on D0/D1** |
| Firmware gap | rotary state machine, expanders, cycling | + VFD driver, string table, per-frame animator |
| Materials/unit | ≈10 600 ₽ | **re-cost pending** — the old +2 600 ₽ assumed the graphic panel |
| List price | 27 000 ₽ | 31 000 ₽ · founder 27 000 · floor 24 000 |

### The economy Rev E broke

TERMINAL-06 grew its face to 237 mm to seat the ИН-15 annex. **MIMI does not need that annex — a VFD
that can spell "OKAERI" can obviously spell "AM"** — so MIMI stays at 176 mm and the two products
**stop sharing a fascia outline**. That was real: one artwork, one Rezonit order of 30 instead of two
of 15. Everything else stays common. **Price both quantities**; if the split is unaffordable, the
fallback is TERMINAL-06 keeping a 176 mm fascia left-justified with a badge plate in the spare 61 mm.

---

## 5. Still open

1. **Price and MOQ from the FUTABA seller.** Every cost line is stale until this lands.
2. **CGRAM support.** Decides whether faces are ever pixel-drawn or stay strings.
3. **Bit-banged SPI against the live multiplex** — reasoned, not measured.
4. **The VFD will out-shine the tubes.** ≈505 nm sits almost on the eye's peak; the nixies at ≈605 nm
   do not, and run at 1.10 mA average with no headroom. **Dim the panel to the tubes, never the
   reverse.**
5. **Everything TERMINAL-06 waits on, this waits on too** — including the **P2 anode-quench block**.
   Same tube board, same ISR, same ghosting.
6. **Different buyer.** Kawaii-after-dark desk decor, cyberpunk room, cozy gaming setup. **The video
   opens on the face, not the tubes** — unchanged by the colourway.
7. **The old render toolchain is stale.** `mimi.py` / `mimihero.py` / `mimisheet.py` / `vfd.py` all
   describe the milk shell and a 128 × 32 bitmap. `vfd.py` now needs to render 16 cells of 5×7 from a
   string table.
8. **Nothing has been printed.** Plinth, ear fins, rake — one test print.

---

## 6. Photography

**Rev 1 required two lighting setups. Rev 2 requires one.** A cream body on black read grey and fought
the dark set that flatters nixie tubes; an ink-black body does not. KURO shoots on the same set as
TERMINAL-06 — which also means the two products photograph as one shop, which they did not before.
