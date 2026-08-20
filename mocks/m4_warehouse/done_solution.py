"""Mock 5 — Warehouse Inventory.  Implement Warehouse here."""

from collections import defaultdict
from math import inf
import copy
import bisect


class Warehouse:
    def __init__(self):
        self.wh = {} # item_id:[{"quantity": int, "expires": int}, {"quantity": int, "expires": int}]
        self.orders = {} # order_id: {"item_id": ["quantity": int, "expires": int]}
        self.timestamps = []
        self._snaps = []
    
    def _commit(self, timestamp):
        if len(self.timestamps) > 0 and timestamp == self.timestamps[-1]:
            self._snaps[-1] = copy.deepcopy(self.wh)
        else:
            self.timestamps.append(timestamp)
            self._snaps.append(copy.deepcopy(self.wh))
    
    def add_stock_at_with_expiry(self, timestamp, item_id, quantity, ttl):
        if item_id not in self.wh:
            self.wh[item_id] = []
        
        # add to existing unit by same name and expiry
        for unit in self.wh[item_id]:
            if unit['expires'] == timestamp + ttl:
                unit["quantity"] += quantity
                self._commit(timestamp)
                return self.get_quantity_at(timestamp, item_id)

        # create a new dictionary entry for that item_id
        new_unit = {"quantity": quantity, "expires": ttl + timestamp}
        self.wh[item_id].append(new_unit)
        self._commit(timestamp)
        return self.get_quantity_at(timestamp, item_id)
    
    def _remove_stock_at(self, timestamp, item_id, quantity):
        unit_pairs = [[x['expires'], x['quantity']] for x in self.wh[item_id] if self._alive_unit(timestamp, x)]
        sorted_unit_pairs = sorted(unit_pairs)
        running_sum = 0
        ind = 0
        while running_sum < quantity:
            running_sum += sorted_unit_pairs[ind][1]
            ind += 1
        rem_units = sorted_unit_pairs[ind-1:]
        overshoot = running_sum - quantity
        rem_units[0] = (rem_units[0][0], overshoot)
        new_item_inv = [{"quantity": x[1], "expires": x[0]} for x in rem_units]
        self.wh[item_id] = new_item_inv
        self._commit(timestamp)
        return ind, sorted_unit_pairs, overshoot
    
    def add_stock_at(self, timestamp, item_id, quantity):
        return self.add_stock_at_with_expiry(timestamp, item_id, quantity, inf)

    def add_stock(self, item_id, quantity):
        return self.add_stock_at(0, item_id, quantity)
    
    def _alive_unit(self, timestamp, unit):
        if unit['expires'] == inf:
            return True
        return unit['expires'] > timestamp
    
    def get_quantity_at(self, timestamp, item_id):
        if item_id not in self.wh:
            return None
        return sum([x['quantity'] for x in self.wh[item_id] if self._alive_unit(timestamp, x)])
    
    def get_quantity(self, item_id):
        return self.get_quantity_at(0, item_id)

    def ship_at(self, timestamp, item_id, quantity):
        if item_id not in self.wh or self.get_quantity_at(timestamp, item_id) < quantity:
            # no item_id or not enough quantity
            return None
        _, __, ___ = self._remove_stock_at(timestamp, item_id, quantity)
        return self.get_quantity_at(timestamp, item_id)
        
    def ship(self, item_id, quantity):
        return self.ship_at(0, item_id, quantity)
    
    def search_at(self, timestamp, prefix):
        pairs = [(-self.get_quantity_at(timestamp, k), k) for k, v in self.wh.items() if k.startswith(prefix) and self.get_quantity_at(timestamp, k) > 0]
        pairs = sorted(pairs)
        pairs = [f"{x[1]}({-x[0]})" for x in pairs][:10]
        return pairs
    
    def search(self, prefix):
        return self.search_at(0, prefix)
    
    def place_order(self, timestamp, order_id, item_id, quantity):
        if order_id in self.orders or item_id not in self.wh or self.get_quantity_at(timestamp, item_id) < quantity:
            return False
        ind, sorted_unit_pairs, overshoot = self._remove_stock_at(timestamp, item_id, quantity)
        # order
        order = sorted_unit_pairs[:ind]
        order[-1][1] -= overshoot   # adjust the last item in order to subtract the overshoot
        self.orders[order_id] = [{"item_id": item_id, "quantity": x[1], "expires": x[0]} for x in order]
        return True
    
    def cancel_order(self, timestamp, order_id):
        if order_id not in self.orders:
            return None
        units_returned = 0
        for unit in self.orders[order_id]:
            if not self._alive_unit(timestamp, unit):
                continue
            self.add_stock_at_with_expiry(timestamp, unit['item_id'], unit['quantity'], unit['expires'] - timestamp)
            units_returned += unit['quantity']
        del self.orders[order_id]
        return units_returned
    
    def quantity_at(self, timestamp, item_id, time_at):
        i = bisect.bisect_right(self.timestamps, time_at) - 1
        temp_wh = copy.deepcopy(self.wh)
        units = 0
        if i >= 0:
            self.wh = self._snaps[i]
            units = self.get_quantity_at(time_at, item_id)
            self.wh = temp_wh
            return units





# - `quantity_at(timestamp, item_id, time_at)`
#   - Returns the item's live quantity as it was at `time_at`, where
#     `time_at <= timestamp`.
#   - Reflects every operation whose timestamp is at or before `time_at`, and only
#     those.
#   - Returns `None` if the item did not exist at `time_at`.
