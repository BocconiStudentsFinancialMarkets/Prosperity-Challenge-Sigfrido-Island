from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List, Dict
import string
import math
import json
import jsonpickle
from typing import Any

from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState

POSITION_LIMIT = 50
ORDER_SIZE = 10  # Default order size

class Logger:
    def __init__(self) -> None:
        self.logs = ""
        self.max_log_length = 3750

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders: dict[Symbol, list[Order]], conversions: int, trader_data: str) -> None:
        base_length = len(
            self.to_json(
                [
                    self.compress_state(state, ""),
                    self.compress_orders(orders),
                    conversions,
                    "",
                    "",
                ]
            )
        )

        # We truncate state.traderData, trader_data, and self.logs to the same max. length to fit the log limit
        max_item_length = (self.max_log_length - base_length) // 3

        print(
            self.to_json(
                [
                    self.compress_state(state, self.truncate(state.traderData, max_item_length)),
                    self.compress_orders(orders),
                    conversions,
                    self.truncate(trader_data, max_item_length),
                    self.truncate(self.logs, max_item_length),
                ]
            )
        )

        self.logs = ""

    def compress_state(self, state: TradingState, trader_data: str) -> list[Any]:
        return [
            state.timestamp,
            trader_data,
            self.compress_listings(state.listings),
            self.compress_order_depths(state.order_depths),
            self.compress_trades(state.own_trades),
            self.compress_trades(state.market_trades),
            state.position,
            self.compress_observations(state.observations),
        ]

    def compress_listings(self, listings: dict[Symbol, Listing]) -> list[list[Any]]:
        compressed = []
        for listing in listings.values():
            compressed.append([listing.symbol, listing.product, listing.denomination])

        return compressed

    def compress_order_depths(self, order_depths: dict[Symbol, OrderDepth]) -> dict[Symbol, list[Any]]:
        compressed = {}
        for symbol, order_depth in order_depths.items():
            compressed[symbol] = [order_depth.buy_orders, order_depth.sell_orders]

        return compressed

    def compress_trades(self, trades: dict[Symbol, list[Trade]]) -> list[list[Any]]:
        compressed = []
        for arr in trades.values():
            for trade in arr:
                compressed.append(
                    [
                        trade.symbol,
                        trade.price,
                        trade.quantity,
                        trade.buyer,
                        trade.seller,
                        trade.timestamp,
                    ]
                )

        return compressed

    def compress_observations(self, observations: Observation) -> list[Any]:
        conversion_observations = {}
        for product, observation in observations.conversionObservations.items():
            conversion_observations[product] = [
                observation.bidPrice,
                observation.askPrice,
                observation.transportFees,
                observation.exportTariff,
                observation.importTariff,
                observation.sugarPrice,
                observation.sunlightIndex,
            ]

        return [observations.plainValueObservations, conversion_observations]

    def compress_orders(self, orders: dict[Symbol, list[Order]]) -> list[list[Any]]:
        compressed = []
        for arr in orders.values():
            for order in arr:
                compressed.append([order.symbol, order.price, order.quantity])

        return compressed

    def to_json(self, value: Any) -> str:
        return json.dumps(value, cls=ProsperityEncoder, separators=(",", ":"))

    def truncate(self, value: str, max_length: int) -> str:
        if len(value) <= max_length:
            return value

        return value[: max_length - 3] + "..."


logger = Logger()

class Trader:
    def run(self, state: TradingState):
        result = {}
        traderData = state.traderData
        print("Trader Data:", traderData)

        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []

            # Position tracking
            position = state.position.get(product, 0)
            print(f"\n--- {product} ---")
            print(f"Current position: {position}")

            buy_orders = order_depth.buy_orders
            sell_orders = order_depth.sell_orders

            # Determine best bid and ask
            best_bid = max(buy_orders.keys()) if buy_orders else None
            best_ask = min(sell_orders.keys()) if sell_orders else None

            if best_bid is not None and best_ask is not None:
                fair_price = (best_bid + best_ask) / 2
            else:
                fair_price = 10  # fallback default
            print(f"Fair price estimate: {fair_price}")

            # === BUY Logic ===
            for ask_price, ask_volume in sorted(sell_orders.items()):
                if ask_price < fair_price and position < POSITION_LIMIT:
                    buy_volume = min(-ask_volume, POSITION_LIMIT - position, ORDER_SIZE)
                    print(f"BUY {buy_volume} @ {ask_price}")
                    orders.append(Order(product, ask_price, buy_volume))
                    position += buy_volume

            # === SELL Logic ===
            for bid_price, bid_volume in sorted(buy_orders.items(), reverse=True):
                if bid_price > fair_price and position > -POSITION_LIMIT:
                    sell_volume = min(bid_volume, POSITION_LIMIT + position, ORDER_SIZE)
                    print(f"SELL {sell_volume} @ {bid_price}")
                    orders.append(Order(product, bid_price, -sell_volume))
                    position -= sell_volume

            result[product] = orders

        # Optional: traderData can store trends or custom state
        traderData = ""
        conversions = 1  # No conversion strategy in tutorial

        return result, conversions, traderData

