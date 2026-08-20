# Mock 4 — Warehouse Inventory


You are implementing the stock ledger for a warehouse. Items are identified by a
string id and hold some number of **units**. All state is in memory. Quantities
are non-negative integers; timestamps are non-negative integers and are
non-decreasing across calls.

---

## Level 1 — Initial design & basic functions

- `add_stock(item_id, quantity)`
  - Adds `quantity` units of `item_id`, creating the item if it does not exist.
  - Returns the item's total quantity afterwards.
- `get_quantity(item_id)`
  - Returns the item's total quantity, or `None` if the item does not exist.
- `ship(item_id, quantity)`
  - Removes `quantity` units and returns the quantity remaining.
  - Returns `None` if the item does not exist or holds fewer than `quantity`
    units. Nothing is removed in those cases.

An item that has been shipped down to zero units still exists.

---

## Level 2 — Data structures & data processing

- `search(prefix)`
  - Returns at most **10** strings of the form `"item_id(quantity)"` for items
    whose id begins with `prefix`, ordered by quantity descending, ties by item
    id ascending.
  - Items holding zero units are not included. Returns `[]` if nothing matches.

---

## Level 3 — Refactoring & encapsulation

Stock is now perishable. Every Level 1/2 method gains a timestamped twin, and
the originals must keep working — treat them as operating at timestamp `0` on
units that never expire.

Units added at `t` with `ttl = n` are alive for timestamps in `[t, t + n)` and
are gone at exactly `t + n`. Expired units vanish silently: they are never
counted and never shipped.

- `add_stock_at(timestamp, item_id, quantity)` — these units never expire.
- `add_stock_at_with_expiry(timestamp, item_id, quantity, ttl)`
- `get_quantity_at(timestamp, item_id)`
- `ship_at(timestamp, item_id, quantity)`
  - Ships the units that expire soonest first. Units that never expire are
    shipped last.
- `search_at(timestamp, prefix)`

An item whose units have all expired still exists and reports a quantity of `0`.

---

## Level 4 — Orders

- `place_order(timestamp, order_id, item_id, quantity)`
  - Removes `quantity` units from stock — soonest-expiring first, exactly as
    `ship_at` does — and records the order under `order_id`.
  - Returns `True`, or `False` if an order with that id already exists, the item
    does not exist, or the item holds fewer than `quantity` live units. Nothing
    is removed in those cases.
- `cancel_order(timestamp, order_id)`
  - Returns the order's units to stock. Each returned unit keeps the expiry it
    had when the order was placed, so units that have expired in the meantime
    are **not** returned.
  - Returns the number of units actually returned to stock, or `None` if there
    is no open order with that id.
  - An order can be cancelled only once.

---

## Level 5 — Historical quantities

- `quantity_at(timestamp, item_id, time_at)`
  - Returns the item's live quantity as it was at `time_at`, where
    `time_at <= timestamp`.
  - Reflects every operation whose timestamp is at or before `time_at`, and only
    those.
  - Returns `None` if the item did not exist at `time_at`.
