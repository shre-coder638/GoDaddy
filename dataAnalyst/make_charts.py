"""Slide-ready PNG charts -> charts/ (run after rush_hour_insights.py)"""
import os, json, pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
H = os.path.dirname(os.path.abspath(__file__)); os.makedirs(f"{H}/charts", exist_ok=True)
r = json.load(open(f"{H}/insights_results.json")); Y, G = "#F2B705", "#9a9a8a"
plt.rcParams.update({"font.size": 16, "axes.spines.top": False, "axes.spines.right": False, "figure.figsize": (12.8, 7.2)})
def save(n): plt.tight_layout(); plt.savefig(f"{H}/charts/{n}.png", dpi=100); plt.close()
sl = r["slot_load"]; x = [s["slot"] for s in sl]; v = [s["demand_vs_capacity_pct"] for s in sl]
plt.bar(x, v, color=[Y if a >= 100 else G for a in v]); plt.axhline(100, color="k", ls="--"); plt.xticks(x[::4])
plt.title("Demand vs counter capacity by 15-min slot (100% = 60 orders)"); plt.ylabel("% of capacity"); save("1_peak_slots")
c = r["capacity_tradeoff"]; k = ["1 counter, no slots", "2 counters, no slots", "1 counter, cap 60", "2 counters, cap 120"]
plt.barh(k[::-1], [c[a]["avg_wait_min"] for a in k][::-1], color=[Y, G, G, G]); plt.xlabel("Average rush-hour wait (min)")
plt.title("Average wait in the 12:45-1:45 rush"); save("2_wait_before_after")
w = r["waste_vs_stockout_30days_rush"]; n = ["flat_plan", "cook_ahead"]; xs = range(2)
plt.bar([i - .2 for i in xs], [w[a]["units_short"] for a in n], .4, color=Y, label="Units sold out")
plt.bar([i + .2 for i in xs], [w[a]["units_wasted"] for a in n], .4, color=G, label="Units wasted")
plt.xticks(xs, ["Same of everything", "Cook-ahead plan"]); plt.legend(); plt.title("Sell-outs and waste over 30 days"); save("3_waste")
hm = pd.read_csv(f"{H}/heatmap_weekday_slot.csv", index_col=0).loc[:, "11:00":"14:45"]
plt.imshow(hm.values, cmap="RdYlGn_r", aspect="auto"); plt.yticks(range(len(hm)), hm.index); plt.xticks(range(0, hm.shape[1], 2), hm.columns[::2], rotation=45)
plt.colorbar(label="avg orders per slot"); plt.title("Best time to come: green = quiet"); save("4_heatmap")
