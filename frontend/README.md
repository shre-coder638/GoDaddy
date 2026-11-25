# Rush Hour — Campus Canteen (Yellow problem)
Run: `node gen_data.js` (30 days of fake orders → data/orders.csv + insights.json), then `node server.js` → http://localhost:3000
Needs only Node 18+. No npm install.

Pages (all linked from the nav bar): Sign up · Log in · Order (3 taps) · My orders (pickup pass) · Kitchen (staff) · Insights.
Kitchen sign-up staff code: `canteen123`. Slot capacity: `SLOT_CAPACITY=10` (env var).

API: POST /api/signup, /api/login · GET /api/menu, /api/slots, /api/queue, /api/insights ·
POST /api/orders {items:[{id,qty}],slot:"13:00",name?} → 201 order | 409 {error:"SLOT_FULL",nextSlot} ·
GET /api/orders/mine · GET /api/kitchen/orders, /api/kitchen/cook-next · PATCH /api/kitchen/orders/:id/status

Gate test: `for i in $(seq 11); do curl -s -XPOST localhost:3000/api/orders -H 'content-type: application/json' -d '{"items":[{"id":"samosa","qty":1}],"slot":"13:00"}'; echo; done` → the 11th returns SLOT_FULL + next slot.
