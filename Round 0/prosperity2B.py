# -*- coding: utf-8 -*-
"""
Created on Sun Apr  6 13:40:42 2025

@author: Savvina Salvaridou
"""

import requests
import json
import numpy as np


import jsonpickle
from typing import Any

from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState


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
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://prosperity.imc.com/archipelago"  
        self.position_limit = 50  # Max position for both products

    def calculate_weighted_average(self, order_dict):
        """
        Calculate weighted average of the orders (this can help us estimate the fair price).
        """
        total_volume = sum(abs(v) for v in order_dict.values())
        if total_volume == 0:
            return 0
        return sum(p * abs(v) for p, v in order_dict.items()) / total_volume

    def detect_trend(self, recent_prices):
        """
        Detect if there's an uptrend or downtrend.
        """
        if len(recent_prices) < 2:
            return "neutral"
        return "bullish" if recent_prices[-1] > recent_prices[-2] else "bearish"

    def get_balance(self):
        """
        Fetch the balance (mock implementation).
        You need to replace it with actual API call to fetch balance.
        """
        # Example return, replace with actual API call
        return 10000  # Assume balance is 10,000 for the sake of this example

    def get_current_price(self, product):
        """
        Fetch the current price (mock implementation).
        Replace with actual API call to get product price.
        """
        # Example return, replace with actual API call
        return 10  # Assume current price is 10 for the sake of this example

    def get_order_depth(self, product):
        """
        Get the order book for a product from the platform API.
        """
        url = f"{self.base_url}/orderbook/{product}"  # Replace with actual endpoint
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()  # Assuming the API returns order book in JSON format
        else:
            print(f"Error getting order depth for {product}: {response.text}")
            return None

    def get_market_trades(self, product):
        """
        Get recent market trades for a product.
        """
        url = f"{self.base_url}/trades/{product}"  # Replace with actual endpoint
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()  # Assuming the API returns market trades in JSON format
        else:
            print(f"Error getting trades for {product}: {response.text}")
            return []

    def place_order(self, product, price, volume):
        """
        Place an order on the platform via the API.
        """
        url = f"{self.base_url}/place-order"  # Replace with actual endpoint
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        order_data = {
            "product": product,
            "price": price,
            "volume": volume,
        }
        response = requests.post(url, headers=headers, json=order_data)
        if response.status_code == 200:
            print(f"Order placed successfully: {product} at {price} with volume {volume}")
        else:
            print(f"Error placing order: {response.text}")

    def calculate_position_size(self, product, max_risk_percentage=0.02):
        """
        Dynamically adjust the position size based on available capital and risk management.
        """
        balance = self.get_balance()  # Fetch balance
        product_price = self.get_current_price(product)  # Fetch the product price
        max_risk_amount = balance * max_risk_percentage
        position_size = max_risk_amount / product_price
        return position_size

    def calculate_atr(self, prices, window=14):
        """
        Calculate the Average True Range (ATR) for a given set of prices.
        ATR is used to measure volatility.
        """
        true_ranges = []
        for i in range(1, len(prices)):
            true_range = max(prices[i]['high'] - prices[i]['low'], 
                             abs(prices[i]['high'] - prices[i-1]['close']),
                             abs(prices[i]['low'] - prices[i-1]['close']))
            true_ranges.append(true_range)
        atr = np.mean(true_ranges[-window:])
        return atr

    def calculate_order_book_imbalance(self, buy_orders, sell_orders):
        """
        Calculate the order book imbalance (buy orders vs. sell orders).
        """
        total_buy_volume = sum(order['volume'] for order in buy_orders)
        total_sell_volume = sum(order['volume'] for order in sell_orders)
        imbalance = total_buy_volume - total_sell_volume
        return imbalance

    def run(self, state : TradingState):
        # Example: Running the trader strategy for Rainforest Resin and Kelp
        products = ["RAINFOREST_RESIN", "KELP"]

        for product in products:
            # Get the order depth and recent market trades for the product
            order_depth = self.get_order_depth(product)
            market_trades = self.get_market_trades(product)

            if order_depth and market_trades:
                recent_prices = [trade['price'] for trade in market_trades[-5:]]  # Get the last 5 trades
                fair_price = self.calculate_weighted_average(order_depth['buy_orders'])
                imbalance = self.calculate_order_book_imbalance(order_depth['buy_orders'], order_depth['sell_orders'])

                # Calculate ATR for volatility
                atr = self.calculate_atr(market_trades)

                # Adjust position size based on risk management
                position_size = self.calculate_position_size(product)

                if product == "RAINFOREST_RESIN":
                    # Example Mean Reverting Strategy for Rainforest Resin
                    spread = 1
                    order_size = position_size  # Adjust order size dynamically

                    if fair_price < 10:
                        self.place_order(product, fair_price - spread, order_size)
                    elif fair_price > 10:
                        self.place_order(product, fair_price + spread, -order_size)

                elif product == "KELP":
                    # Example Momentum Strategy for Kelp
                    trend = self.detect_trend(recent_prices)

                    if trend == "bullish":
                        self.place_order(product, fair_price + 1, position_size)
                    elif trend == "bearish":
                        self.place_order(product, fair_price - 1, -position_size)
                        
    
        logger.flush(state, result, conversions, trader_data)
        return result, conversions, trader_data


#api_key = "YOUR_API_KEY"  # Replace with your actual API key
#trader = Trader(api_key)
#trader.run()
