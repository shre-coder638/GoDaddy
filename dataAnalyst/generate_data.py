"""Rush Hour - fake canteen data generator (30 days) + analysis.
All data is synthetic. Seeded so the numbers are reproducible."""
import numpy as np, pandas as pd, json
from datetime import date, datetime, timedelta

rng = np.random.default_rng(42)

MENU = {  # item: (price in INR, base popularity)
    "Samosa":          (15, 10), "Chole Bhature":   (60, 8),
    "Veg Thali":       (80, 7),  "Paneer Roll":     (50, 7),
    "Veg Burger":      (40, 6),  "Masala Dosa":     (55, 5),
    "Maggi":           (30, 8),  "Aloo Paratha":    (35, 5),
    "Cold Coffee":     (40, 7),  "Masala Chai":     (10, 9),
    "Bread Pakora":    (15, 4),  "Fried Rice":      (65, 4),
}
# weekday-specific boosts (0=Mon). Makes the "top 5 by day" question interesting.
BOOST = {
    0: {"Samosa": 1.8, "Aloo Paratha": 1.4},
    1: {"Chole Bhature": 2.2},
    2: {"Paneer Roll": 1.7, "Cold Coffee": 1.4},
    3: {"Veg Thali": 2.0, "Fried Rice": 1.6},
    4: {"Maggi": 1.8, "Veg Burger": 1.6},
    5: {"Masala Dosa": 1.9, "Cold Coffee": 1.5},
}
DAY_LOAD = {0: 1.0, 1: 1.05, 2: 1.1, 3: 1.0, 4: 0.9, 5: 0.5}  # Sat is a half day

# arrival-rate profile through the day: (start_hour, end_hour, weight)
# a sharp lunch spike at 12:45-1:30 pm, plus smaller tea/snack bumps
PROFILE = [(9.5, 11, 0.10), (11, 12.5, 0.12), (12.5, 13.0, 0.14),
           (13.0, 13.5, 0.34), (13.5, 14.5, 0.15), (14.5, 16.5, 0.15)]

def sample_time(day):
    r = rng.random() * sum(w for *_, w in PROFILE)
    acc = 0
    for s, e, w in PROFILE:
        acc += w
        if r <= acc:
            h = rng.uniform(s, e)
            return datetime(day.year, day.month, day.day) + timedelta(hours=h)

end = date(2026, 11, 24)
days = [end - timedelta(days=i) for i in range(35)][::-1]
days = [d for d in days if d.weekday() != 6][-30:]      # canteen closed Sundays; keep 30 open days

rows, oid = [], 1000
json.dump([{"id": f"M{i+1:02d}", "name": n, "price": p} for i, (n, (p, _)) in enumerate(MENU.items())],
          open("/mnt/user-data/outputs/menu.json", "w"), indent=1)          # backend serves this menu
json.dump({"slot_minutes": 15, "first_slot": "09:30", "last_slot": "16:15", "capacity_per_slot": 60,
           "gate_slot": "13:00", "rush_window": ["12:45", "13:45"]},
          open("/mnt/user-data/outputs/slot_config.json", "w"), indent=1)   # shared constants: backend + analysis
items = list(MENU)
for d in days:
    wd = d.weekday()
    n_orders = int(rng.normal(920, 60) * DAY_LOAD[wd])   # ~400 orders in the 12:45-1:45 rush, as in the brief
    w = np.array([MENU[i][1] * BOOST.get(wd, {}).get(i, 1.0) for i in items], float)
    w /= w.sum()
    for _ in range(n_orders):
        oid += 1
        t = sample_time(d)
        for it in rng.choice(items, size=rng.choice([1, 2, 3], p=[.55, .33, .12]), replace=False, p=w):
            rows.append([f"ORD{oid}", d.isoformat(), d.strftime("%A"), t.strftime("%H:%M"),
                         it, int(rng.choice([1, 2, 3], p=[.78, .17, .05])), MENU[it][0]])

df = pd.DataFrame(rows, columns=["order_id", "date", "weekday", "time", "item", "quantity", "unit_price"])
df["line_total"] = df.quantity * df.unit_price
df.to_csv("/mnt/user-data/outputs/orders.csv", index=False)

# ---------- analysis ----------
ts = pd.to_datetime(df.date + " " + df.time)
df["slot"] = ts.dt.floor("15min").dt.strftime("%H:%M")
orders = df.drop_duplicates("order_id")
slot_orders = orders.assign(slot=orders.order_id.map(df.drop_duplicates("order_id").set_index("order_id").slot))
per_day_slot = slot_orders.groupby(["date", "slot"]).size().rename("orders").reset_index()
peak = (per_day_slot.groupby("slot").orders.agg(avg_orders_per_day="mean", max_orders="max")
        .round(1).sort_values("avg_orders_per_day", ascending=False))
peak["share_of_daily_orders_pct"] = (peak.avg_orders_per_day / peak.avg_orders_per_day.sum() * 100).round(1)
peak.head(8).to_csv("/mnt/user-data/outputs/peak_slots.csv")

order_idx = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
top5 = (df.groupby(["weekday", "item"]).quantity.sum().rename("units").reset_index()
        .sort_values(["weekday", "units"], ascending=[True, False]).groupby("weekday").head(5))
top5["rank"] = top5.groupby("weekday").cumcount() + 1
top5 = top5.set_index("weekday").loc[order_idx].reset_index()
top5.to_csv("/mnt/user-data/outputs/top5_by_weekday.csv", index=False)

# Level-3 "cook ahead": average units per item per weekday in the 12:30-13:45 rush
rush = df[(df.time >= "12:45") & (df.time < "13:45")]
cook = (rush.groupby(["weekday", "item", "date"]).quantity.sum().groupby(["weekday", "item"]).mean().round().astype(int))
cook_json = {wd: cook.loc[wd].sort_values(ascending=False).head(5).to_dict() for wd in order_idx}
json.dump({"note": "avg units sold per item in the 12:45-13:45 rush, by weekday",
           "cook_ahead": cook_json}, open("/mnt/user-data/outputs/cook_ahead.json", "w"), indent=2)

# headline numbers
rush_share = slot_orders[(slot_orders.slot >= "12:45") & (slot_orders.slot < "13:45")].shape[0] / len(slot_orders) * 100
print("days:", df.date.nunique(), "| orders:", df.order_id.nunique(), "| line items:", len(df))
print("avg orders/day:", round(df.order_id.nunique() / df.date.nunique()))
print("revenue (INR):", int(df.line_total.sum()))
print("\nPEAK 15-MIN SLOTS\n", peak.head(6))
print("\nTOP 5 BY WEEKDAY\n", top5.pivot(index="rank", columns="weekday", values="item")[order_idx])
print(f"\n12:45-13:45 carries {rush_share:.0f}% of the day's orders")
top = peak.iloc[0]
print("busiest slot avg:", peak.index[0], top.avg_orders_per_day, "max:", top.max_orders)
