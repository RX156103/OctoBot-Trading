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

"""
Handles balance changes
"""
from asyncio import CancelledError, Queue

from octobot_channels import CONSUMER_CALLBACK_TYPE
from octobot_commons.logging.logging_util import get_logger

from octobot_trading.channels.exchange_channel import ExchangeChannel, ExchangeChannelConsumer
from octobot_channels.consumer import Consumer
from octobot_channels.producer import Producer


class BalanceProducer(Producer):
    def __init__(self, channel):
        self.logger = get_logger(self.__class__.__name__)
        super().__init__(channel)

    async def push(self, balance, is_delta=False):
        await self.perform(balance, is_delta=is_delta)

    async def perform(self, balance, is_delta=False):
        try:
            changed = await self.channel.exchange_manager.exchange_personal_data.handle_portfolio_update(balance)
            if changed:
                await self.send(balance)
        except CancelledError:
            self.logger.info("Update tasks cancelled.")
        except Exception as e:
            self.logger.error(f"exception when triggering update: {e}")
            self.logger.exception(e)

    async def send(self, balance):
        for consumer in self.channel.get_consumers():
            await consumer.queue.put({
                "exchange": self.channel.exchange_manager.exchange.name,
                "balance": balance
            })


class BalanceChannel(ExchangeChannel):
    pass
