"""Mock 5 — Warehouse Inventory.  Implement Warehouse here."""

from collections import defaultdict
from math import inf
import copy
import bisect


class Warehouse:
    def __init__(self):
        self.wh = {}    # item_id: [{'quant': int, 'exp': int}, {'quant': int, 'exp': int}]
        self.orders = {}# order_id: {"item_id": {'item_id':int, 'quant':int}}, {"item_id": {}}
        self._tss = []
        self._snaps = []
        
    def _commit(self, ts):
        if len(self._tss) > 0 and self._tss[-1] == ts:
            self._snaps[-1] = copy.deepcopy(self.wh)
        else:
            self._tss.append(ts)
            self._snaps.append(copy.deepcopy(self.wh))
        
    def add_stock_at_with_expiry(self, ts, item_id, quantity, ttl):
        if item_id not in self.wh:
            self.wh[item_id] = []
        # if stock with this expiry date already exists, we add to it
        for unit in self.wh[item_id]:
            if unit['exp'] == ts + ttl:
                unit['quant'] += quantity
                self._commit(ts)
                return self.get_quantity_at(ts, item_id)
        # otherwise, we add new stock unit
        self.wh[item_id].append({'quant': quantity, 'exp': ts + ttl})
        self._commit(ts)
        return self.get_quantity_at(ts, item_id)

    def _remove_stock(self, ts, item_id, quantity):
        # ship with algo - earliest first
        live_key_units = sorted([v for v in self.wh[item_id] if self._live(ts, v)], key=lambda x: x['exp'])
        taken = []
        for unit in live_key_units:
            if quantity <= 0:
                break
            # compute how much we are removing
            min_val = min(quantity, unit['quant'])
            # reduce unit quant
            unit['quant'] -= min_val
            # reduce quantity we are reducing by
            quantity -= min_val
            # put the item back after potentially taking stock
            taken.append({"quant": min_val, 'exp': unit['exp'], 'item_id': item_id})
        self.wh[item_id] = [u for u in live_key_units if self.get_quantity_at(ts, item_id) > 0]
        self._commit(ts)
        return taken

    def add_stock_at(self, ts, item_id, quantity):
        return self.add_stock_at_with_expiry(ts, item_id, quantity, inf)
    
    def add_stock(self, item_id, quantity):
        return self.add_stock_at(0, item_id, quantity)

    def _live(self, ts, unit):
        return unit['exp'] > ts
    
    def ship_at(self, ts, item_id, quantity):
        if item_id not in self.wh or self.get_quantity_at(ts, item_id) < quantity:
            return None
        self._remove_stock(ts, item_id, quantity)
        return self.get_quantity_at(ts, item_id)
    
    def ship(self, item_id, quantity):
        return self.ship_at(0, item_id, quantity)

    def get_quantity_at(self, ts, item_id):
        if item_id not in self.wh:
            return None
        # sum all units tht are live at ts
        live_unit_quant = sum([x['quant'] for x in self.wh[item_id] if self._live(ts, x)])
        # print("get_quantity_at", live_unit_quant)
        return live_unit_quant
        
    def get_quantity(self, item_id):
        return self.get_quantity_at(0, item_id)

    def search_at(self, ts, prefix):
        pairs = [(k,self.get_quantity_at(ts, k)) for k, v in self.wh.items() if k.startswith(prefix) and self.get_quantity_at(ts, k) > 0]
        # pairs = [(k, v['quant']) for k,v in self.wh.items() if k.startswith(prefix) and self.get_quantity_at(ts, v)]
        sorted_pairs = sorted(pairs, key=lambda x: (-x[1], x[0]))
        ret_pairs = [f"{x[0]}({x[1]})" for x in sorted_pairs][:10]
        return ret_pairs
    
    def search(self, prefix):
        return self.search_at(0, prefix)
    
    def place_order(self, ts, order_id, item_id, quantity):
        if order_id in self.orders or item_id not in self.wh or self.get_quantity_at(ts, item_id) < quantity:
            return False
        taken_units = self._remove_stock(ts, item_id, quantity)
        self.orders[order_id] = taken_units
        print('placing order', self.orders)
        self._commit(ts)
        return True

    def cancel_order(self, ts, order_id):
        if order_id not in self.orders:
            print('returning none in cancel order', self.orders)
            return None
        num_returned = 0
        print('cancel order self.orders', self.orders)
        for unit in self.orders[order_id]:
            if self._live(ts, unit):
                self.add_stock_at_with_expiry(ts, unit['item_id'], unit['quant'], unit['exp'])
                num_returned += unit['quant']
        del self.orders[order_id]
        print('cancel order self.orders', self.orders)
        self._commit(ts)
        return num_returned
        
    def quantity_at(self, ts, item_id, time_at):
        i = bisect.bisect_right(self._tss, time_at) - 1
        if i >= 0:
            tmp = copy.deepcopy(self.wh)
            self.wh = self._snaps[i]
            to_ret = self.get_quantity_at(time_at, item_id)
            self.wh = tmp
            return to_ret
            


# every write is behind a commit

# - `quantity_at(timestamp, item_id, time_at)`
#   - Returns the item's live quantity as it was at `time_at`, where
#     `time_at <= timestamp`.
#   - Reflects every operation whose timestamp is at or before `time_at`, and only
#     those.
#   - Returns `None` if the item did not exist at `time_at`.