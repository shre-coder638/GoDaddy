"""Rush Hour - extra insights on top of orders.csv (all data is synthetic).
1 queue simulation  2 combo of the day  3 waste vs stock-out  4 slot nudge
5 live queue meter  6 happy-slot pricing sim  (7 = dashboard.html)
Backend dev: import slot_load_table, suggest_slot, queue_wait_minutes, combo_of_day."""
import json, numpy as np, pandas as pd
from collections import Counter
from itertools import combinations

OUT = "/mnt/user-data/outputs"
SERVICE_BASE, PER_LINE = 6, 5      # ASSUMPTION: counter takes 6s per order + 5s per item line
CAP = json.load(open(f"{OUT}/slot_config.json"))["capacity_per_slot"]   # max orders per 15-min slot (~93% of counter capacity)
QUIET = [750, 765, 825, 840]       # 12:30, 12:45, 13:45, 14:00 - quieter slots around the peak
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
rng = np.random.default_rng(7)

def service_s(lines): return SERVICE_BASE + PER_LINE * lines
def lab(m): return f"{m // 60:02d}:{m % 60:02d}"

def load():
    df = pd.read_csv(f"{OUT}/orders.csv")
    df["minute"] = df.time.str[:2].astype(int) * 60 + df.time.str[3:].astype(int)
    o = df.groupby("order_id").agg(date=("date", "first"), weekday=("weekday", "first"),
                                   minute=("minute", "first"), lines=("item", "count"),
                                   items=("item", list)).reset_index()
    o["slot"] = o.minute // 15 * 15
    return df, o

# ---------- 1 + 6: queue simulation (single counter, FIFO) ----------
def fifo_waits(arrive, lines):
    free, w = 0.0, np.zeros(len(arrive))
    for i in np.argsort(arrive):
        s = max(arrive[i], free); w[i] = s - arrive[i]; free = s + service_s(lines[i])
    return w

def simulate(o, mode, f=0.0):
    waits, shifted, moved, peak = [], [], [], []
    for _, g in o.groupby("date"):
        minute, lines, orig = g.minute.values, g.lines.values, g.slot.values
        n = len(g); final = orig.copy()
        arrive = minute * 60 + rng.uniform(0, 60, n)
        order = np.argsort(minute + rng.uniform(0, 1, n))
        if mode == "slotted":                       # cap each slot, push overflow to next free slot
            cnt = Counter()
            for i in order:
                s = orig[i]
                while cnt[s] >= CAP: s += 15
                cnt[s] += 1; final[i] = s
            arrive = final * 60 + rng.uniform(0, 900, n)
        if mode == "price":                         # f of 13:00-13:30 students take the discount
            load = Counter(orig)
            for i in order:
                if orig[i] in (780, 795) and rng.random() < f:
                    t = min(QUIET, key=lambda q: load[q])
                    load[orig[i]] -= 1; load[t] += 1
                    final[i] = t; arrive[i] = t * 60 + rng.uniform(0, 900)
        w = fifo_waits(arrive, lines)
        rush = (minute >= 765) & (minute < 825)
        waits += list(w[rush] / 60)
        d = (final - orig)[rush]; shifted += list(d != 0); moved += list(d[d != 0])
        c = Counter(final); peak.append((c[780] + c[795]) / 2)
    w = np.array(waits)
    return {"avg_wait_min": round(w.mean(), 1), "pct_wait_over_10min": round((w > 10).mean() * 100, 1),
            "p90_wait_min": round(np.percentile(w, 90), 1),
            "pct_moved_slot": round(np.mean(shifted) * 100, 1),
            "discount_cost_inr_per_day": round(5 * sum(shifted) / o.date.nunique()) if mode == "price" else 0,
            "avg_shift_min": round(float(np.mean(moved)), 1) if moved else 0.0,
            "avg_orders_in_peak_slots": round(float(np.mean(peak)), 1)}

# ---------- 2: combo of the day ----------
def combo_of_day(df, o):
    price = df.drop_duplicates("item").set_index("item").unit_price.to_dict()
    n_all, item_n, res = len(o), Counter(i for it in o["items"] for i in it), {}
    for wd in DAYS:
        g = o[o.weekday == wd]; pc = Counter()
        for it in g["items"]:
            for a, b in combinations(sorted(it), 2): pc[(a, b)] += 1
        (a, b), c = pc.most_common(1)[0]
        lift = (c / len(g)) / ((item_n[a] / n_all) * (item_n[b] / n_all))
        full = price[a] + price[b]
        res[wd] = {"combo": f"{a} + {b}", "pct_of_orders": round(c / len(g) * 100, 1), "lift": round(lift, 2),
                   "full_price": full, "bundle_price": int(round(full * 0.9)), "valid": "1:45 pm onwards (quiet slots)"}
    return res

# ---------- 3: waste vs stock-out (leave-one-day-out) ----------
def waste(df):
    r = df[(df.minute >= 765) & (df.minute < 825)]
    D = r.pivot_table(index="date", columns="item", values="quantity", aggfunc="sum", fill_value=0)
    wd = pd.to_datetime(D.index).day_name()
    def score(plan):
        short = np.clip(D.values - plan, 0, None).sum(); left = np.clip(plan - D.values, 0, None).sum()
        return int(short), int(left)
    flat = np.tile(round(D.values.mean()), D.shape)           # same quantity of everything, every day
    loo = np.vstack([D[(wd == wd[k]) & (D.index != D.index[k])].mean().values for k in range(len(D))])
    out = {"flat_plan": score(flat), "cook_ahead": score(np.ceil(loo)), "cook_ahead_plus10": score(np.ceil(loo * 1.1))}
    return {k: {"units_short": s, "units_wasted": w} for k, (s, w) in out.items()}

# ---------- 4: slot nudge ----------
def slot_load_table(o):
    n_days = o.date.nunique(); cnt = o.groupby("slot").size() / n_days
    rows = []
    for s in range(570, 990, 15):
        a = float(cnt.get(s, 0)); pct = round(a / CAP * 100)
        rows.append({"slot": lab(s), "avg_orders": round(a, 1), "demand_vs_capacity_pct": pct,
                     "status": "full" if pct >= 100 else "busy" if pct >= 60 else "quiet"})
    return rows

def suggest_slot(desired_min, booked, cap=CAP):
    """NUDGE only (suggests quieter slots before one is full). Hard refusal is book_slot(). booked: {slot_start_minute: orders_booked}. Returns the slot to book + a UI message."""
    if booked.get(desired_min, 0) < cap * 0.7:
        return {"slot": lab(desired_min), "message": "Slot available"}
    for d in range(15, 181, 15):
        for s in (desired_min + d, desired_min - d):
            if booked.get(s, 0) < cap * 0.7:
                pct = round(100 - booked.get(s, 0) / max(booked.get(desired_min, 1), 1) * 100)
                return {"slot": lab(s), "message": f"{lab(desired_min)} is busy. {lab(s)} is {pct}% emptier - ready faster!"}
    return {"slot": None, "message": "All nearby slots are full"}

def book_slot(desired_min, booked, cap=CAP):
    """THE GATE: accept if the slot has space, else refuse and offer the next free slot."""
    if booked.get(desired_min, 0) < cap:
        booked[desired_min] = booked.get(desired_min, 0) + 1
        return {"accepted": True, "slot": lab(desired_min)}
    for s in range(desired_min + 15, 976, 15):
        if booked.get(s, 0) < cap:
            return {"accepted": False, "reason": "slot_full", "next_slot": lab(s)}
    return {"accepted": False, "reason": "day_full", "next_slot": None}

def gate_selftest():
    booked = {}
    for _ in range(CAP): assert book_slot(780, booked)["accepted"]
    r = book_slot(780, booked); assert not r["accepted"] and r["next_slot"] == "13:15", r
    return {"passed": True, "refused_with": r}

def cook_next(open_orders):
    """Kitchen screen: open_orders = [{"items": {"Samosa": 2}}, ...] -> items to cook, biggest first."""
    c = Counter()
    for od in open_orders:
        for it, q in od["items"].items(): c[it] += q
    return [{"item": i, "qty": q} for i, q in c.most_common()]

# ---------- 5: live queue meter ----------
def queue_wait_minutes(open_orders, open_lines, counters=1):
    return round((open_orders * SERVICE_BASE + open_lines * PER_LINE) / 60 / counters, 1)

if __name__ == "__main__":
    df, o = load()
    res = {"assumptions": {"service_seconds": f"{SERVICE_BASE}s per order + {PER_LINE}s per item line",
                           "slot_capacity_orders": CAP, "rush_window": "12:45-13:45"}}
    res["queue_sim"] = {"today_one_counter": simulate(o, "base"), "with_slot_cap": simulate(o, "slotted"),
                        **{f"happy_slot_{int(f*100)}pct_shift": simulate(o, "price", f) for f in (0.1, 0.2, 0.3)}}
    res["combo_of_day"] = combo_of_day(df, o)
    res["waste_vs_stockout_30days_rush"] = waste(df)
    res["slot_load"] = slot_load_table(o)
    res["gate_selftest"] = gate_selftest()
    res["cook_next_demo"] = cook_next([{"items": {"Samosa": 2, "Maggi": 1}}, {"items": {"Samosa": 1}}])
    res["suggest_slot_demo"] = suggest_slot(795, {780: 58, 795: 55, 810: 30, 765: 20})
    res["queue_meter_demo_min"] = queue_wait_minutes(open_orders=24, open_lines=38)
    json.dump(res, open(f"{OUT}/insights_results.json", "w"), indent=2)
    pd.DataFrame(res["combo_of_day"]).T.to_csv(f"{OUT}/combo_of_day.csv")
    pd.DataFrame(res["slot_load"]).to_json(f"{OUT}/slot_load.json", orient="records", indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "slot_load"}, indent=1))
