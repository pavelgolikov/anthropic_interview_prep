"""Mock 5 reference solution — Warehouse Inventory.

Read this only AFTER your own attempt. What to look for:

  * Stock is a *list of batches*, never a bare integer. `items[id] = 5` is the
    Level 1 shortcut that Level 3 destroys; `items[id] = [{"qty": 5,
    "expires": None}]` costs two extra characters at Level 1 and survives.
  * `_take` is the only place units leave an item. `ship_at` and `place_order`
    are both three lines because they share it — and `place_order` gets the
    "which batches did I consume" bookkeeping for free, which is exactly what
    `cancel_order` needs at Level 4.
  * Every mutation is an entry in `self.log` *and* a call to `_apply`. Level 5
    is then a replay: build a fresh state, feed it the events at or before
    `time_at`, measure. Nothing else in the file changes.
  * Timestamped forms are the real implementations; the plain Level 1/2 forms
    delegate with `timestamp=0`. Writing it the other way round means rewriting
    five methods at Level 3.

~120 lines.
"""


class Warehouse:
    def __init__(self):
        self.state = {"items": {}, "orders": {}}
        self.log = []  # (timestamp, event) for every successful mutation

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _alive(batch, timestamp):
        return batch["expires"] is None or batch["expires"] > timestamp

    @classmethod
    def _live_qty(cls, batches, timestamp):
        return sum(b["qty"] for b in batches if cls._alive(b, timestamp))

    @classmethod
    def _take(cls, batches, timestamp, quantity):
        """Consume `quantity` live units, soonest-expiring first.

        Returns the batches consumed, or None if there is not enough stock
        (in which case nothing is modified).
        """
        if cls._live_qty(batches, timestamp) < quantity:
            return None
        order = sorted(
            (b for b in batches if cls._alive(b, timestamp)),
            key=lambda b: (b["expires"] is None, b["expires"]),
        )
        taken, left = [], quantity
        for batch in order:
            if left == 0:
                break
            n = min(left, batch["qty"])
            batch["qty"] -= n
            left -= n
            taken.append({"qty": n, "expires": batch["expires"]})
        batches[:] = [b for b in batches if b["qty"] > 0 and cls._alive(b, timestamp)]
        return taken

    @classmethod
    def _apply(cls, state, timestamp, event):
        """The single mutation point. Replayed verbatim at Level 5."""
        kind = event[0]
        if kind == "add":
            _, item_id, quantity, expires = event
            state["items"].setdefault(item_id, []).append(
                {"qty": quantity, "expires": expires}
            )
        elif kind == "ship":
            _, item_id, quantity = event
            cls._take(state["items"][item_id], timestamp, quantity)
        elif kind == "order":
            _, order_id, item_id, quantity = event
            taken = cls._take(state["items"][item_id], timestamp, quantity)
            state["orders"][order_id] = {"item": item_id, "units": taken}
        elif kind == "cancel":
            _, order_id = event
            order = state["orders"].pop(order_id)
            for batch in order["units"]:
                if cls._alive(batch, timestamp):
                    state["items"][order["item"]].append(dict(batch))

    def _record(self, timestamp, event):
        self._apply(self.state, timestamp, event)
        self.log.append((timestamp, event))

    # ------------------------------------------------------------------ level 3
    def add_stock_at(self, timestamp, item_id, quantity):
        return self.add_stock_at_with_expiry(timestamp, item_id, quantity, None)

    def add_stock_at_with_expiry(self, timestamp, item_id, quantity, ttl):
        expires = None if ttl is None else timestamp + ttl
        self._record(timestamp, ("add", item_id, quantity, expires))
        return self._live_qty(self.state["items"][item_id], timestamp)

    def get_quantity_at(self, timestamp, item_id):
        if item_id not in self.state["items"]:
            return None
        return self._live_qty(self.state["items"][item_id], timestamp)

    def ship_at(self, timestamp, item_id, quantity):
        batches = self.state["items"].get(item_id)
        if batches is None or self._live_qty(batches, timestamp) < quantity:
            return None
        self._record(timestamp, ("ship", item_id, quantity))
        return self._live_qty(batches, timestamp)

    def search_at(self, timestamp, prefix):
        hits = []
        for item_id, batches in self.state["items"].items():
            if not item_id.startswith(prefix):
                continue
            qty = self._live_qty(batches, timestamp)
            if qty > 0:
                hits.append((item_id, qty))
        hits.sort(key=lambda pair: (-pair[1], pair[0]))
        return [f"{item_id}({qty})" for item_id, qty in hits[:10]]

    # ------------------------------------------------------------------ level 1
    def add_stock(self, item_id, quantity):
        return self.add_stock_at(0, item_id, quantity)

    def get_quantity(self, item_id):
        return self.get_quantity_at(0, item_id)

    def ship(self, item_id, quantity):
        return self.ship_at(0, item_id, quantity)

    # ------------------------------------------------------------------ level 2
    def search(self, prefix):
        return self.search_at(0, prefix)

    # ------------------------------------------------------------------ level 4
    def place_order(self, timestamp, order_id, item_id, quantity):
        if order_id in self.state["orders"]:
            return False
        batches = self.state["items"].get(item_id)
        if batches is None or self._live_qty(batches, timestamp) < quantity:
            return False
        self._record(timestamp, ("order", order_id, item_id, quantity))
        return True

    def cancel_order(self, timestamp, order_id):
        order = self.state["orders"].get(order_id)
        if order is None:
            return None
        returned = sum(b["qty"] for b in order["units"] if self._alive(b, timestamp))
        self._record(timestamp, ("cancel", order_id))
        return returned

    # ------------------------------------------------------------------ level 5
    def quantity_at(self, timestamp, item_id, time_at):
        state = {"items": {}, "orders": {}}
        for event_time, event in self.log:
            if event_time <= time_at:
                self._apply(state, event_time, event)
        if item_id not in state["items"]:
            return None
        return self._live_qty(state["items"][item_id], time_at)
