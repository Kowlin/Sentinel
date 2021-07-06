import discord

from redbot.core import commands
from redbot.core import checks
from redbot.core.utils.chat_formatting import pagify, escape
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

BaseCog = getattr(commands, "Cog", object)


class TestSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
        )
        for x in range(1, 6):
            self.add_option(label=f"Option {x}")
        self.options[1].default = True

    async def callback(self, interaction: discord.Interaction):
        print(interaction.data)
        await interaction.response.send_message(
            content=f"You choose {interaction.data['values'][0]}",
            ephemeral=True,
        )


class TestMultiSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
            min_values=1,
            max_values=5,
            placeholder="UwU someone get Sharky"
        )
        for x in range(1, 11):
            self.add_option(label=f"Option {x}")
        self.options[2].default = True
        self.options[3].default = True

    async def callback(self, interaction: discord.Interaction):
        print(interaction.data)
        print(self.view)
        await interaction.response.send_message(
            content=f"You choose the following:\n{', '.join(interaction.data['values'])}",
            ephemeral=True
        )


class TestButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label='Hello world'
        )

    async def callback(self, interaction: discord.Interaction):
        print(f"{interaction.user.name} pressed")
        await interaction.response.send_message(
            content=f"Hello, {interaction.user.display_name}",
            ephemeral=True
        )


class TestDisabledButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="Goodbye world",
            disabled=True
        )


class TestView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=600)

        self.add_item(TestButton())
        self.add_item(TestDisabledButton())
        self.add_item(TestSelect())
        self.add_item(TestMultiSelect())

    async def start(self, ctx: commands.Context):
        self.ctx = ctx
        self.message = await ctx.send(
            content="Buttons & Select demo:\n - Buttons\n - Select box (Single)\n - Select box (Multi)",
            view=self
        )

        """    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.message.id != self.message.id:
            await interaction.response.send_message(
                content=_("You are not authorized to interact with this."), ephemeral=True
            )
            return False
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                content=_("You are not authorized to interact with this."), ephemeral=True
            )
            return False
        return True"""


class Butts(BaseCog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def test(self, ctx):
        v = TestView()
        await v.start(ctx)
