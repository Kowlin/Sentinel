"""
  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""


from redbot.core import commands


class RepoData(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> dict:
        cache = ctx.cog.active_prefix_matchers.get(ctx.guild.id, None)
        if cache is None:
            raise commands.BadArgument("There are no configured repositories on this server.")
        repo_data = cache["data"].get(argument, None)
        if repo_data is None:
            raise commands.BadArgument(
                f"There's no repo with prefix `{argument}` configured on this server"
            )
        return repo_data
