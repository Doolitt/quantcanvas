# Codebase Issue Triage: Proposed Tasks

## 1) Typo fix task
**Title:** Replace invalid Tailwind color token `gray-750` with a supported token (`gray-700` or `gray-800`).

**Why:** Two dashboard cards use `dark:hover:bg-gray-750`, but Tailwind’s default gray scale does not include `750`. This is likely a typo and prevents the intended hover style from being applied in dark mode.

**Where:**
- `src/components/dashboard/EconomicCalendar.tsx`
- `src/components/dashboard/StrategyBuilder.tsx`

---

## 2) Bug fix task
**Title:** Apply date filtering in `EconomicCalendar` so the selected date actually controls the displayed events.

**Why:** The component stores `selectedDate` in state and renders a date input, but the event list is always rendered from the full `events` array without filtering by date. The UI implies filtering behavior that currently does not happen.

**Where:**
- `src/components/dashboard/EconomicCalendar.tsx`

---

## 3) Comment/documentation discrepancy task
**Title:** Reconcile roadmap status in `README.md` with the current implementation state.

**Why:** The roadmap still marks `Basic dashboard layout`, `Portfolio tracker UI`, and `Strategy builder interface` as incomplete, but these components are already implemented and rendered in `Dashboard.tsx`. The docs and code are out of sync.

**Where:**
- `README.md`
- `src/components/dashboard/Dashboard.tsx`

---

## 4) Test improvement task
**Title:** Add unit tests for Econoday scraping utility functions (`parse_time`, `parse_date`, `get_cat`, `fix_url`).

**Why:** `scripts/scrape_and_store.py` contains non-trivial parsing logic that can regress silently (date parsing, category mapping, time extraction), but there are no automated tests covering edge cases. Add targeted tests with representative inputs from live Econoday variations.

**Where:**
- `scripts/scrape_and_store.py`
- New test file (for example `tests/test_scrape_and_store.py`)
