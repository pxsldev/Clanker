# im a tehxt file!

from discord import app_commands, Interaction, User, TextChannel
from discord.ext import commands
import discord
import random

def uwuify(text: str) -> str:
    faces = ["(・`ω´・)", "uwu", "owo", ">w<", "^w^"]

    text = text.replace("r", "w").replace("l", "w")
    text = text.replace("R", "W").replace("L", "W")

    return text + " " + random.choice(faces)


def reverse_text(text: str) -> str:
    return text[::-1]


def random_case(text: str) -> str:
    return "".join(
        c.upper() if random.random() > 0.5 else c.lower()
        for c in text
    )


def no_vowels(text: str) -> str:
    return "".join(
        c for c in text
        if c.lower() not in "aeiou"
    )


def snake_case(text: str) -> str:
    return text.replace(" ", "_").lower()


def mock(text: str) -> str:
    return "".join(
        c.upper() if i % 2 else c.lower()
        for i, c in enumerate(text)
    )


def leet(text: str) -> str:
    mapping = str.maketrans({
        "a": "4",
        "e": "3",
        "i": "1",
        "o": "0",
        "s": "5",
        "t": "7"
    })

    return text.translate(mapping)


def zalgo(text: str) -> str:
    zalgo_chars = [
        "̍", "̎", "̄", "̅", "̿",
        "̑", "̆", "̐", "͒", "͗", "͑"
    ]

    return "".join(
        c + "".join(
            random.choice(zalgo_chars)
            for _ in range(2)
        )
        for c in text
    )

class Text(commands.GroupCog, group_name="text"):

    def __init__(self, bot):
        self.bot = bot

    async def transform_text(
        self,
        interaction: Interaction,
        text: str,
        action_name: str,
        transform_func
    ):
        channel = interaction.channel

        if not isinstance(channel, TextChannel):
            embed = discord.Embed(
                title="Error ❌",
                description="Cannot use this command here!",
                color=discord.Color.red()
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )
            return

        transformed = transform_func(text)

        embed = discord.Embed(
            title=f"{action_name} Text ⌨️",
            description=transformed,
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(embed=embed)

    group_1 = app_commands.Group(
        name="1",
        description="Text - page 1"
    )

    @group_1.command(
        name="uwu",
        description="uwuify text"
    )
    @app_commands.describe(
        text="Text to transform"
    )
    async def uwu(
        self,
        interaction: Interaction,
        text: str
    ):
        await self.transform_text(
            interaction,
            text,
            "UwUifying",
            uwuify
        )


    @group_1.command(
        name="caps",
        description="uppercase text"
    )
    @app_commands.describe(
        text="Text to transform"
    )
    async def caps(
        self,
        interaction: Interaction,
        text: str
    ):
        await self.transform_text(
            interaction,
            text,
            "Making",
            str.upper
        )


    @group_1.command(
        name="lower",
        description="lowercase text"
    )
    @app_commands.describe(
        text="Text to transform"
    )
    async def lower(
        self,
        interaction: Interaction,
        text: str
    ):
        await self.transform_text(
            interaction,
            text,
            "Making",
            str.lower
        )


    @group_1.command(
        name="reverse",
        description="reverse text"
    )
    @app_commands.describe(
        text="Text to transform"
    )
    async def reverse(
        self,
        interaction: Interaction,
        text: str
    ):
        await self.transform_text(
            interaction,
            text,
            "Reversing",
            reverse_text
        )


    @group_1.command(
        name="randomcase",
        description="randomize letter casing"
    )
    @app_commands.describe(
        text="Text to transform"
    )
    async def randomcase(
        self,
        interaction: Interaction,
        text: str
    ):
        await self.transform_text(
            interaction,
            text,
            "Randomizing",
            random_case
        )

    @group_1.command(
        name="novowels",
        description="remove vowels from text"
    )
    @app_commands.describe(
        text="Text to transform"
    )
    async def novowels(
        self,
        interaction: Interaction,
        text: str
    ):
        await self.transform_text(
            interaction,
            text,
            "Removing vowels from",
            no_vowels
        )

    @group_1.command(
        name="snake",
        description="convert text to snake_case"
    )
    @app_commands.describe(
        text="Text to transform"
    )
    async def snake(
        self,
        interaction: Interaction,
        text: str
    ):
        await self.transform_text(
            interaction,
            text,
            "Snake-casing",
            snake_case
        )


    @group_1.command(
        name="mock",
        description="mocking spongebob text"
    )
    @app_commands.describe(
        text="Text to transform"
    )
    async def mock_cmd(
        self,
        interaction: Interaction,
        text: str
    ):
        await self.transform_text(
            interaction,
            text,
            "Mocking",
            mock
        )


    @group_1.command(
        name="leet",
        description="make text l33t c4s3"
    )
    @app_commands.describe(
        text="Text to transform"
    )
    async def leet_cmd(
        self,
        interaction: Interaction,
        text: str
    ):
        await self.transform_text(
            interaction,
            text,
            "Leeting",
            leet
        )


    @group_1.command(
        name="zalgo",
        description="make text z̍͗͑a̎̄̐l̅̿͒g̑̆͗o"
    )
    @app_commands.describe(
        text="Text to transform"
    )
    async def zalgo_cmd(
        self,
        interaction: Interaction,
        text: str
    ):
        await self.transform_text(
            interaction,
            text,
            "Zalgoifying",
            zalgo
        )

async def setup(bot):
    await bot.add_cog(Text(bot))