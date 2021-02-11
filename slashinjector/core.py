"""
  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

from redbot.core.bot import Red
from redbot.core import commands


class SlashInjector(commands.Cog):
    """Inject a interaction_create parser into discord.py"""

    def __init__(self, bot) -> None:
        self.bot: Red = bot
        setattr(bot._connection, "parse_interaction_create", self.parse_interaction_create)
        bot._connection.parsers["INTERACTION_CREATE"] = self.parse_interaction_create

    def cog_unload(self):
        del self.bot._connection.parsers["INTERACTION_CREATE"]

    def parse_interaction_create(self, data):
        self.bot.dispatch("interaction_create", data)
