# Rush Hour (Yellow) - Data Analyst Pack

**Mission:** kill the canteen queue. At 1 pm about 400 students reach one counter. This pack is the data analyst's part of the team: it generates the data, finds the insights, and gives the rest of the team numbers and functions to use.

> All data is **synthetic** (seeded, so every run gives the same numbers). No real names or figures.

---

## 1. The data analyst's role

| The brief asks the analyst to | Where it is done |
|---|---|
| Generate 30 days of realistic orders (item, time, quantity, price) | `orders.csv` |
| Find the peak 15-minute slots | `peak_slots.csv` |
| Find the top 5 items by day of the week | `top5_by_weekday.csv` |
| Pull out insights for the pitch | `insights_results.json`, `charts/`, dashboard |

Beyond the brief, this pack also supports the other roles: the backend dev (slot rules and gate logic), the UI designer (slot heat bar, kitchen screen data), and the quality lead (gate test).

---

## 2. Quick start

```
pip install pandas numpy matplotlib
python generate_data.py          # 1st: creates the data + first analysis files
python rush_hour_insights.py     # 2nd: simulations, schedules, heatmap (needs step 1)
python make_charts.py            # 3rd: slide charts (needs step 2)
python gate_test.py              # checks the 90-minute gate; should print GATE PASSED
```
Use `python3` on Mac/Linux. Run in this order. All files are written next to the scripts.

---

## 3. Files

### Raw data and shared settings
| File | What it is | Used by |
|---|---|---|
| `orders.csv` | 30 open days (Mon-Sat), ~25,600 orders, ~40,300 lines, ~850 orders a day. Columns: `order_id, date, weekday, time, item, quantity, unit_price, line_total` | everyone |
| `menu.json` | 12 items with ids M01-M12 and prices | backend serves this as the menu |
| `slot_config.json` | 15-min slots 09:30-16:15, **capacity 60 orders per slot**, gate slot 13:00, rush window 12:45-13:45 | backend + analysis (single source of truth) |

### Core insights (the brief)
| File | What it says |
|---|---|
| `peak_slots.csv` | Busiest slots: 1:15 pm (~145 orders/day) and 1:00 pm (~144). Together ~**34% of the day's orders in 30 minutes** |
| `top5_by_weekday.csv` | Top 5 items per weekday (Mon Samosa, Tue Chole Bhature, Wed Paneer Roll, Thu Veg Thali, Fri Maggi, Sat Masala Dosa) |

### For the other roles
| File | What it is | Used by |
|---|---|---|
| `slot_load.json` | Demand vs capacity per slot (1:00 and 1:15 pm are over 200% of capacity) | UI: heat bar of busy slots |
| `cook_ahead.json` | Average units per item in the rush, by weekday | kitchen screen |
| `cook_schedule.json` | Per weekday and slot: top 5 items and when to start cooking (20 min ahead) | kitchen screen |
| `need_next_hour.json` | Expected units per item for the next hour, per weekday and slot | low-stock alert |
| `combo_of_day.csv` | Most frequent pair per weekday, bundle at 10% off | UI: combo of the day |
| `heatmap_weekday_slot.csv` | Average orders per weekday and slot | UI: "best time to come" |
| `gate_replay.json` | 60 orders for 13:00-13:15, then a 61st that must be refused with 13:15 offered | quality lead |

### Results and visuals
| File | What it is |
|---|---|
| `insights_results.json` | Every simulation number in one place |
| `charts/1_peak_slots.png` | Demand vs capacity by slot |
| `charts/2_wait_before_after.png` | Average wait, four scenarios |
| `charts/3_waste.png` | Sell-outs and waste, flat plan vs cook-ahead |
| `charts/4_heatmap.png` | Best time to come |
| Dashboard (published page) | One-page view of the above: https://claude.ai/artifact/PPCtDnKC3A4wD4RHLRQTgi |

### Code
| File | What it does |
|---|---|
| `generate_data.py` | Creates `orders.csv`, `menu.json`, `slot_config.json`, `peak_slots.csv`, `top5_by_weekday.csv`, `cook_ahead.json` |
| `rush_hour_insights.py` | Queue simulation, capacity trade-off, lost sales, combos, waste comparison, schedules, heatmap. Also holds the functions below |
| `make_charts.py` | Builds the four PNG charts |
| `gate_test.py` | Tests the gate: `python gate_test.py` (reference logic) or `python gate_test.py <url>` (your API; edit the assumed contract at the top of the file) |

---

## 4. Functions for the backend dev
Import with `from rush_hour_insights import book_slot, suggest_slot, queue_wait_minutes, cook_next, low_stock_alert`.

| Function | Use |
|---|---|
| `book_slot(desired_min, booked)` | **The gate.** Accepts, or refuses with `next_slot` when the slot is full. `booked` is `{slot_start_minute: count}` (13:00 = 780) |
| `suggest_slot(desired_min, booked)` | Nudge message ("13:30 is 45% emptier") before a slot is full |
| `queue_wait_minutes(open_orders, open_lines)` | Live queue meter |
| `cook_next(open_orders)` | Kitchen screen: items to cook, biggest first |
| `low_stock_alert(stock, weekday, now_min)` | Items below what the next hour needs. `stock` must list every item |
| `gate_selftest()` | Books 60 orders, checks the 61st is refused |

---

## 5. Key findings (rush 12:45-1:45 pm, ~400 orders)

| Scenario | Avg wait | Students moved later | Est. lost sales/day |
|---|---|---|---|
| 1 counter, no slots | 20.6 min (64% wait over 10 min) | 0% | Rs 5,900 |
| 2 counters, no slots | 2.8 min | 0% | Rs 340 |
| 1 counter, cap 60 | 0.7 min | 71%, by ~34 min | Rs 850 |
| **2 counters, cap 120** | **0.3 min** | **27%, by ~15 min** | **Rs 0** |

- A **second counter alone** nearly removes the queue. Slots are the fix when a second counter is not possible.
- A cap of 70 is above what one counter can serve (~64 orders per slot), so waits rise again to 4.0 min. 60 is a good choice.
- **Cook-ahead** vs cooking the same of everything: **61% fewer sell-out units** and **57% less waste** (30 days, tested leave-one-day-out).
- **Happy-slot pricing** (Rs 5 off to move students) helps only partly (wait 14-18 min). Treat it as a small extra.
- The quietest lunch slot is 12:00-12:15 every day.

---

## 6. Assumptions - say these out loud
- The counter takes **6 s per order + 5 s per item line**. Change `SERVICE_BASE` and `PER_LINE` at the top of `rush_hour_insights.py` if you measure the real speed.
- Walk-aways are guesses: 30% leave after a 10-minute wait, 10% leave if pushed more than 30 minutes (`ABANDON_P`, `REFUSE_P`).
- Cooks start 20 minutes ahead (`PREP_LEAD`).
- The 10/20/30% price-shift rates are scenarios, not measurements.
- Combo pairs mostly follow item popularity (lift near 1). They are not real customer preferences.
- Data is fake: say "our model shows", not "students do".

---

## 7. Who needs what from the analyst
| Teammate | Give them |
|---|---|
| Product lead | `slot_config.json` and the capacity table to agree the API contract in the first 15 minutes |
| Backend dev | `menu.json`, `slot_config.json`, `book_slot()` and the other functions |
| UI designer | `slot_load.json`, `cook_schedule.json`, `combo_of_day.csv`, `heatmap_weekday_slot.csv` |
| Quality and pitch lead | `gate_replay.json` + `gate_test.py`, `charts/`, the prompt log below |

**One-line pitch insight:** "34% of orders arrive in 30 minutes. One counter means a 20-minute wait; slots plus a second counter bring it under a minute."

---

## 8. Prompt log - what the AI got wrong
1. Counted slot demand per line item, so multi-item orders inflated the peaks. Fixed: count per order.
2. First data was too small (~490 orders a day), so the baseline wait was 5.3 min and did not match the brief's 400 students. Rescaled to ~850 orders a day.
3. Left an empty junk key in the results file and first left out the discount cost. Fixed.
4. Mixed up the nudge (suggest a quieter slot) with the gate (refuse only when full). Split into two functions.
5. Suggested slots as the only fix; the simulation showed a second counter matters more.
6. Combo "affinity" looked meaningful but is just popularity in synthetic data.

*Add your own prompts next to these entries: the rules ask for what you asked and what the AI got wrong.*
