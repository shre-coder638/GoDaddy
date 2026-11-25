# Data analyst pack - Rush Hour (Yellow)

All data is synthetic (seeded, reproducible). Run `python3 generate_data.py` then `python3 rush_hour_insights.py`.

## Files
| File | Who uses it | What it is |
|---|---|---|
| `orders.csv` | everyone | 30 open days (Mon-Sat), ~25,600 orders, ~40,300 lines: item, time, quantity, price |
| `menu.json` | backend | 12 items with ids (M01..M12) and prices - serve this as the menu |
| `slot_config.json` | backend + analysis | 15-min slots 09:30-16:15, **capacity 60 orders/slot**, gate slot 13:00 |
| `peak_slots.csv` | pitch | busiest 15-min slots (1:00 and 1:15 pm carry ~34% of orders) |
| `top5_by_weekday.csv` | pitch | top 5 items per weekday |
| `cook_ahead.json` | kitchen UI | avg units per item in the 12:45-1:45 rush, by weekday |
| `slot_load.json` | student UI | demand vs capacity per slot (heat bar) |
| `combo_of_day.csv` | UI | most frequent pair per weekday, bundle = 10% off |
| `insights_results.json` | pitch | all simulation numbers |
| `rush_hour_insights.py` | backend | importable functions (below) |

## Functions for the backend dev
- `book_slot(desired_min, booked)` - THE GATE: accepts, or refuses with `next_slot`. `booked` = `{slot_start_minute: count}` (13:00 = 780).
- `suggest_slot(desired_min, booked)` - nudge message before a slot is full.
- `queue_wait_minutes(open_orders, open_lines)` - live queue meter.
- `cook_next(open_orders)` - kitchen screen: items to cook, biggest first.
- `gate_selftest()` - books 60 orders into 1:00-1:15, checks the 61st is refused and 1:15 is offered (passes).

## Headline numbers (assumption: counter takes 6 s/order + 5 s/item line)
- One counter, no slots: average rush wait **20.6 min**, **64%** wait over 10 min.
- With the slot cap: average wait **0.7 min**, but **71%** of rush students move to a later slot, by **34 min** on average.
- Cook-ahead vs same-of-everything: **-61%** sell-out units, **-57%** wasted units.
- Happy-slot pricing (Rs 5 off) helps only partly (wait 17.8 / 15.5 / 14.0 min at 10 / 20 / 30% shifting) - say this honestly; the slot cap does the heavy lifting.

## Prompt log - what the AI got wrong
1. Counted slot demand per line item, so multi-item orders inflated the peaks. Fixed: count per order.
2. First data was too small (~490 orders/day, ~210 in the rush) so the baseline wait was only 5.3 min and did not match the brief's 400 students. Rescaled to ~850 orders/day.
3. Left an empty junk key (`happy_slot_cost_per_day_inr`) in the results file and first omitted the discount cost. Fixed.
4. Mixed up the nudge (suggest_slot, 70% threshold) with the gate (refuse only when full). Split into two functions.
5. Combo pairs have lift near 1 (popularity-driven) - do not claim real affinity from synthetic data.
