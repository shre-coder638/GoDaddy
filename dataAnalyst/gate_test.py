"""Gate test for the 90-minute check. Fills 13:00-13:15 (60 orders), then one more must be refused with 13:15 offered.
  python gate_test.py                      -> tests the reference logic (book_slot)
  python gate_test.py http://localhost:8000/orders   -> tests YOUR API (edit FIELDS/status rules below to match the contract)
Assumed API contract: POST JSON {student, pickup_slot, items:[{item_id, quantity}]}; 2xx = accepted; 400/409/422 = refused
with JSON {"next_slot": "13:15"}."""
import json, os, sys, urllib.request, urllib.error
HERE = os.path.dirname(os.path.abspath(__file__)); replay = json.load(open(f"{HERE}/gate_replay.json"))
url = sys.argv[1] if len(sys.argv) > 1 else None
if url is None:
    from rush_hour_insights import book_slot; booked = {}
def send(od):
    if url is None:
        r = book_slot(780, booked); return r["accepted"], r.get("next_slot")
    req = urllib.request.Request(url, json.dumps({k: od[k] for k in ("student", "pickup_slot", "items")}).encode(), {"Content-Type": "application/json"})
    try: urllib.request.urlopen(req); return True, None
    except urllib.error.HTTPError as e:
        if e.code in (400, 409, 422): return False, json.loads(e.read() or b"{}").get("next_slot")
        raise
fails = 0
for od in replay:
    ok, nxt = send(od); want = od["expect"] == "accepted"
    if ok != want or (not want and nxt != od["expect_next_slot"]):
        fails += 1; print(f"FAIL order {od['order_no']}: accepted={ok}, next_slot={nxt}")
print("GATE PASSED" if not fails else f"GATE FAILED ({fails} problems)")
