# im a utilitlituy file!

from discord import app_commands, Interaction, User, TextChannel
from discord.ext import commands
import discord
import aiohttp
import random
import qrcode
import io
import asyncio
import re
import json

class Utility(commands.GroupCog, group_name="utility"):
    def __init__(self, bot):
        self.bot = bot

    def parse_time(self, time_str: str) -> int:
        matches = re.findall(r"(\d+)([smhdw])", time_str.lower())

        if not matches:
            return -1

        multipliers = {
            "s": 1,
            "m": 60,
            "h": 3600,
            "d": 86400,
            "w": 604800
        }

        total_seconds = 0

        for value, unit in matches:
            total_seconds += int(value) * multipliers[unit]

        return total_seconds if total_seconds > 0 else -1
    
    group_1 = app_commands.Group(
        name="1",
        description="Utility commands - page 1"
    )

    @group_1.command(
        name="dadjoke",
        description="random dad joke very funny haha"
    )
    async def dadjoke(
        self,
        interaction: Interaction
    ):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://icanhazdadjoke.com/",
                headers={"Accept": "application/json"}
            ) as resp:
                data = await resp.json()

        embed = discord.Embed(
            title="Dad Joke 😂",
            description=data["joke"],
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(embed=embed)

    @group_1.command(
        name="dog",
        description="i like dog"
    )
    async def dog(
        self,
        interaction: Interaction
    ):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://dog.ceo/api/breeds/image/random"
            ) as resp:
                data = await resp.json()

        embed = discord.Embed(
            title="Random Dog 🐶",
            color=discord.Color.blurple()
        )

        embed.set_image(url=data["message"])

        await interaction.response.send_message(embed=embed)

    @group_1.command(
        name="cat",
        description="i like cat"
    )
    async def cat(
        self,
        interaction: Interaction
    ):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.thecatapi.com/v1/images/search"
            ) as resp:
                data = await resp.json()

        embed = discord.Embed(
            title="🐱 Random Cat",
            color=discord.Color.blurple()
        )

        embed.set_image(url=data[0]["url"])

        await interaction.response.send_message(embed=embed)

    @group_1.command(
        name="duck",
        description="i like duck"
    )
    async def duck(
        self,
        interaction: Interaction
    ):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://random-d.uk/api/v2/random"
            ) as resp:
                data = await resp.json()

        embed = discord.Embed(
            title="🦆 Random Duck",
            color=discord.Color.blurple()
        )

        embed.set_image(url=data["url"])

        await interaction.response.send_message(embed=embed)

    @group_1.command(
        name="oliver",
        description="get a random picture of dashcrikeydash's cat"
    )
    async def oliver(
        self,
        interaction: Interaction
    ):
        json_url = "https://dashcrikeydash.github.io/images.json"
        base_url = "https://dashcrikeydash.github.io/"

        async with aiohttp.ClientSession() as session:
            async with session.get(json_url) as resp:
                if resp.status != 200:
                    return await interaction.response.send_message(
                        "Failed to fetch cat images ❌",
                        ephemeral=True
                    )

                text = await resp.text()

        lines = text.splitlines()

        valid_lines = [
            line.strip().strip('",')
            for line in lines
            if line.strip() not in ["[", "]"] and line.strip()
        ]

        if not valid_lines:
            return await interaction.response.send_message(
                "No cat images found ❌",
                ephemeral=True
            )

        random_image = random.choice(valid_lines)
        final_url = base_url + random_image

        embed = discord.Embed(
            title="Random Oliver Image 🐱",
            color=discord.Color.blurple()
        )

        embed.set_image(url=final_url)

        await interaction.response.send_message(embed=embed)

    @group_1.command(
        name="password",
        description="get an actually good password"
    )
    @app_commands.describe(
        length="Length of the password (4-100)"
    )
    async def password(
        self,
        interaction: Interaction,
        length: int = 12
    ):
        if length < 4 or length > 100:
            embed = discord.Embed(
                title="Invalid Length ❌",
                description=(
                    "Password length must be between "
                    "4 and 100 characters."
                ),
                color=discord.Color.red()
            )

            return await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

        chars = (
            "abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789"
            "!@#$%^&*()-_=+[]{}|;:,.<>?/~`"
        )

        password = "".join(
            random.choice(chars)
            for _ in range(length)
        )

        embed = discord.Embed(
            title="🔐 Generated Password",
            description=f"```\n{password}\n```",
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    @group_1.command(
        name="qr",
        description="generate a qr code for a url"
    )
    @app_commands.describe(
        url="url to qr code-ify"
    )
    async def qr(
        self,
        interaction: Interaction,
        url: str
    ):
        qr_img = qrcode.make(url)

        buffer = io.BytesIO()
        qr_img.save(buffer, format="PNG")
        buffer.seek(0)

        embed = discord.Embed(
            title="📱 QR Code",
            description=f"QR code for: `{url}`",
            color=discord.Color.blurple()
        )

        file = discord.File(
            fp=buffer,
            filename="qr.png"
        )

        embed.set_image(
            url="attachment://qr.png"
        )

        await interaction.response.send_message(
            embed=embed,
            file=file
        )

    @group_1.command(
        name="remindme",
        description="set a reminder (10m, 2h, 1d, etc)"
    )
    @app_commands.describe(
        time="time like 10s, 5m, 2h, 1d, 1w",
        message="what should I remind you about"
    )
    async def remindme(
        self,
        interaction: Interaction,
        time: str,
        message: str
    ):
        seconds = self.parse_time(time)

        if seconds <= 0:
            return await interaction.response.send_message(
                "❌ Invalid time format. Use `10s`, `5m`, `2h`, `1d`, `1w`.",
                ephemeral=True
            )

        if seconds > 604800:
            return await interaction.response.send_message(
                "❌ Max reminder time is 1 week.",
                ephemeral=True
            )

        embed = discord.Embed(
            title="⏰ Reminder Set!",
            description=message,
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

        await asyncio.sleep(seconds)

        embed = discord.Embed(
            title="⏰ Reminder",
            description=message,
            color=discord.Color.blurple()
        )

        try:
            await interaction.user.send(embed=embed)

        except:
            await interaction.channel.send(
                content=interaction.user.mention,
                embed=embed
            )

    @group_1.command(
        name="forgetme",
        description="Export your Clanker data and delete everything (GDPR wipe)"
    )
    async def forgetme(
        self,
        interaction: Interaction
    ):
        await interaction.response.defer(ephemeral=True)

        try:
            guild_id = interaction.guild.id
            user_id = interaction.user.id

            self.cursor.execute(
                """
                SELECT * FROM users
                WHERE guild_id=? AND user_id=?
                """,
                (guild_id, user_id)
            )

            row = self.cursor.fetchone()

            if not row:
                return await interaction.followup.send(
                    embed=discord.Embed(
                        title="Nothing to delete",
                        description="You have no stored Clanker data.",
                        color=discord.Color.blurple()
                    ),
                    ephemeral=True
                )

            user_data = self.user_dict(row)

            json_bytes = io.BytesIO(
                json.dumps(
                    user_data,
                    indent=4
                ).encode("utf-8")
            )

            file = discord.File(
                json_bytes,
                filename="clanker_data_export.json"
            )

            self.cursor.execute(
                """
                DELETE FROM users
                WHERE guild_id=? AND user_id=?
                """,
                (guild_id, user_id)
            )

            self.db.commit()

            embed = discord.Embed(
                title="🧨 Data Wiped",
                description=(
                    "Your Clanker data has been exported and deleted.\n"
                    "You are gone from the system."
                ),
                color=discord.Color.red()
            )

            await interaction.followup.send(
                embed=embed,
                file=file,
                ephemeral=True
            )

        except Exception as e:
            print("FORGETME ERROR:", e)

            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error",
                    description=(
                        "Something went wrong while "
                        "deleting your data."
                    ),
                    color=discord.Color.red()
                ),
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(Utility(bot))