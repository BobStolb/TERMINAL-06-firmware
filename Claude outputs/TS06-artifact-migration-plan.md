# Plan: fold the existing artifacts into the TS06 product page

**Asked by the owner** (review answer on viewer v2, 30.09.26 06:22 UTC): "plan out a workflow to replace all my existing
artifacts into this product page".

**Status:** approved by the owner, 30.09.26 06:52 UTC, from the review queue: "1b 2b 3a 4a".
* scope A and B (B as a Family view);
* old artifacts left untouched (not the recommended "moved to" page);
* a Family view on this page;
* the read-only inventory started now.

**The product page** is TS06 Board Viewer (v2, https://claude.ai/artifact/FzK6sTskEh2GvBRHAfNCBS). It already has:
* the assembled clock in 3D, with an explode slider;
* 18 build steps;
* the circuit sections;
* the fascia variants;
* test steps;
* what the 3D model shows.

## What exists (26 artifacts, 30.09.26; sorted by title only, not yet read)
**Group A: TERMINAL-06 itself (9, plus the page):**
* TS06-FASCIA Panel Drawing (pinned), TS06-FASCIA Reference, TS06-FASCIA Buy List
* TERMINAL·06 Rev F, TERMINAL-06 Plate Set, TERMINAL-06 Open Deck
* Terminal·06 Concept Plates (two copies, 24.08 and 25.08)
* Terminal 06 3D model

**Group B: sibling clock and tube projects (8):**
* MIMI-06 Kuro (pinned) and Mimi·06 Concept Plates (pinned)
* QUADRANT Desk Miniature, SCALER-06 Decatron, Staircase Nixie Clock
* Not a Nixie, Meshok Tube Board, Meshok Watchlist

**Group C: not about the clock (8):**
* Затраты на сайт XSTREAM, Вопросы к команде XSTREAM
* the two VR artillery pages
* Геометрия Кронштадта 1721, От жаровни до светодиода
* Закупка инструмента в цех сварки, The Japanese Shelf

## The workflow
1. **Inventory** (one read-only agent). It reads every in-scope artifact and writes a table:
   * what each one holds;
   * its images and files;
   * what is superseded by the current design (for example Rev F against today's rev B boards);
   * what exists nowhere else.

   Each row is marked seen or inferred.
2. **Page structure.** One body of information, many views, as the owner set for the dashboard. Proposed views:
   * **Product** (today's assembly);
   * **Build**;
   * **Circuit**;
   * **Front panel:** drawing, reference, variants, buy list;
   * **Case;**
   * **Parts and buying:** BOM and buy lists;
   * **History:** concept plates, Rev F, plate set, open deck. Each is dated and marked "superseded by …"; nothing is deleted.
   * **Family** (only if the scope includes group B).
3. **Migration**, one view per step, by 1–2 agents at a time within the 50/50 quota.
   * Content moves as it is, and its images go into the page's asset store.
   * Every migrated item gets a check in the page's test suite (`test/run.mjs`), so nothing is lost silently.
4. **Review.** One review item per view, in the owner's queue: the old artifact beside the new view, with before/after pairs.
5. **Old artifacts, after the owner approves a view:**
   * each old artifact is replaced by a short "moved to" page that links to its new view, so old links keep working;
   * deleting is permanent and breaks links, so it happens only on the owner's own yes, one artifact at a time;
   * pins move to the product page only when the owner asks.

## Decisions for the owner
1. **Scope:**
   * (a) group A only;
   * (b) A and B, with B as a Family view (**recommended**: one maker's line of clocks);
   * (c) all 26. Not recommended: group C isn't about this product, and the XSTREAM pages concern the partner nation's business.
2. **Old artifacts after migration:**
   * (a) a "moved to" page (**recommended**);
   * (b) leave them untouched;
   * (c) delete, each only on your own yes.
3. **Sibling projects:**
   * (a) a Family view on this page (**recommended** with scope b);
   * (b) their own product pages later, built the same way.
4. **When:**
   * (a) start the inventory now, as part of the quiet routine (**recommended**: read-only and cheap);
   * (b) wait until you are at the PC.

## Cost and risk (inferred)
* **Inventory:** one agent, read-only.
* **Migration:** about one view per agent run, 6–8 runs for scope (b).
* **Page size:** it is 25 MB in 79 files today. The limits are 16 MB per file and 256 MB per version, so the images fit as assets.
* **Main risk:** content lost in the move. The per-item tests and the review pairs guard against it.

## Progress
* 30.09.26 07:25: inventory done (read-only, 17 artifacts): `Claude outputs/TS06-artifact-inventory.md`.
  * Primary views: History 6, Family 8, Front panel 2, Parts and buying 1.
  * The two Concept Plates copies are different revisions (Rev C and Rev A).
  * Open Deck is a subset of Plate Set.
  * The Buy List ticks live only in the owner's browser.
  * Eight pages carry seller or personal details (not copied).
