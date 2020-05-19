#  Drakkar-Software OctoBot-Trading
#  Copyright (c) Drakkar-Software, All rights reserved.
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3.0 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.
import pytest

from octobot_trading.data.book import Book
from octobot_trading.enums import ExchangeConstantsOrderBookInfoColumns as ECOBIC, TradeOrderSide
from tests.util.random_numbers import random_timestamp, random_order_book_side, random_price


@pytest.fixture()
def book():
    return Book()


def test_handle_new_book(book):
    """
    Handle ccxt request
    {
    'bids': [
        [ price, amount ], // [ float, float ]
        [ price, amount ],
        ...
    ],
    'asks': [
        [ price, amount ],
        [ price, amount ],
        ...
    ],
    'timestamp': 1499280391811, // Unix Timestamp in milliseconds (seconds * 1000)
    'datetime': '2017-07-05T18:47:14.692Z', // ISO8601 datetime string with milliseconds
    'nonce': 1499280391811, // an increasing unique identifier of the orderbook snapshot
    }
    """
    ts = random_timestamp()
    asks = list(random_order_book_side(count=100))
    bids = list(random_order_book_side(count=100))
    book.handle_new_book({
        ECOBIC.ASKS.value: asks,
        ECOBIC.BIDS.value: bids,
        ECOBIC.TIMESTAMP.value: ts
    })
    assert book.timestamp == ts
    assert book.get_ask()
    assert book.get_bid()


def test_handle_book_adds(book):
    book.handle_book_adds([
        get_test_order(TradeOrderSide.BUY.value, "1"),
        get_test_order(TradeOrderSide.BUY.value, "2"),
        get_test_order(TradeOrderSide.SELL.value, "3")
    ])
    assert get_order_at_id_in_order_list("1", book.bids)
    assert get_order_at_id_in_order_list("2", book.bids)
    assert not get_order_at_id_in_order_list("1", book.asks)
    assert not get_order_at_id_in_order_list("2", book.asks)
    assert not get_order_at_id_in_order_list("3", book.bids)
    assert get_order_at_id_in_order_list("3", book.asks)
    assert not get_order_at_id_in_order_list("4", book.asks)
    book.reset()
    assert not get_order_at_id_in_order_list("1", book.bids)
    assert not get_order_at_id_in_order_list("2", book.bids)
    assert not get_order_at_id_in_order_list("3", book.asks)


def test_handle_book_deletes(book):
    order_2 = get_test_order(TradeOrderSide.BUY.value, "2")
    order_3 = get_test_order(TradeOrderSide.SELL.value, "3")
    order_5 = get_test_order(TradeOrderSide.SELL.value, "5")
    book.handle_book_adds([
        get_test_order(TradeOrderSide.BUY.value, "1"),
        order_2,
        order_3,
        get_test_order(TradeOrderSide.SELL.value, "4"),
        order_5
    ])
    assert get_order_at_id_in_order_list("1", book.bids)
    assert get_order_at_id_in_order_list("2", book.bids)
    assert get_order_at_id_in_order_list("3", book.asks)
    assert get_order_at_id_in_order_list("4", book.asks)
    assert get_order_at_id_in_order_list("5", book.asks)
    book.handle_book_deletes([order_5])
    assert get_order_at_id_in_order_list("4", book.asks)
    assert not get_order_at_id_in_order_list("5", book.asks)
    book.handle_book_deletes([order_2, order_3])
    assert get_order_at_id_in_order_list("1", book.bids)
    assert not get_order_at_id_in_order_list("2", book.bids)
    assert not get_order_at_id_in_order_list("3", book.asks)
    assert get_order_at_id_in_order_list("4", book.asks)
    assert not get_order_at_id_in_order_list("5", book.asks)


def test_handle_book_updates(book):
    order_3 = get_test_order(TradeOrderSide.BUY.value, "3")
    order_3_2 = get_test_order(TradeOrderSide.BUY.value, "3")
    order_4 = get_test_order(TradeOrderSide.BUY.value, "4")
    order_4_2 = get_test_order(TradeOrderSide.BUY.value, "4")
    order_6 = get_test_order(TradeOrderSide.SELL.value, "6")
    order_6_2 = get_test_order(TradeOrderSide.SELL.value, "6")
    book.handle_book_adds([
        get_test_order(TradeOrderSide.BUY.value, "1"),
        get_test_order(TradeOrderSide.BUY.value, "2"),
        order_3,
        order_4,
        get_test_order(TradeOrderSide.SELL.value, "5"),
        order_6
    ])

    assert get_order_at_id_in_order_list("1", book.bids)
    assert get_order_at_id_in_order_list("2", book.bids)
    assert get_order_at_id_in_order_list("3", book.bids)
    assert get_order_at_id_in_order_list("4", book.bids)
    assert get_order_at_id_in_order_list("5", book.asks)
    assert get_order_at_id_in_order_list("6", book.asks)
    # unknown order
    book.handle_book_updates([get_test_order(TradeOrderSide.SELL.value, "10")])
    assert get_order_at_id_in_order_list("1", book.bids)
    assert get_order_at_id_in_order_list("2", book.bids)
    assert get_order_at_id_in_order_list("3", book.bids)
    assert get_order_at_id_in_order_list("3", book.bids) == order_3
    assert get_order_at_id_in_order_list("3", book.bids) != order_3_2
    book.handle_book_updates([order_3_2])
    assert get_order_at_id_in_order_list("3", book.bids) != order_3
    assert get_order_at_id_in_order_list("3", book.bids) == order_3_2
    assert get_order_at_id_in_order_list("4", book.bids) == order_4
    assert get_order_at_id_in_order_list("6", book.bids) == order_6
    book.handle_book_updates([order_4_2, order_6_2])
    assert get_order_at_id_in_order_list("4", book.bids) == order_4_2
    assert get_order_at_id_in_order_list("6", book.bids) == order_6_2


def get_test_order(order_side, order_id, order_price=None):
    return {
        ECOBIC.SIDE.value: order_side,
        ECOBIC.PRICE.value: order_price if order_price is not None else random_price(),
        ECOBIC.ORDER_ID.value: order_id
    }


def get_order_at_id_in_order_list(order_id, order_list):
    for order in order_list.values():
        if order[0][ECOBIC.ORDER_ID.value] == order_id:
            return order[0]
    return None
