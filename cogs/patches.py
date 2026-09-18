import asyncio
import random
import discord
from discord.ext import commands

class PromoPatch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chance = 0.10
        self.titles = [
            "hey! thanks for using clanker <3",
            "thx for using the bot :)",
            "oh hey, you're still here",
            "don't ignore me, i'm not a normal promotional message"
        ]
        self.messages = [
            "if you enjoy using Clanker, here's a few things you might like :)",
            "since you're already using Clanker, you might as well check these out <3",
            "wanna see more Clanker stuff? here you go:",
            "you've used the bot, so here's some cool stuff you can check out:",
            "supporting me is massively appreciated as this is a hobby project, there's even free ways that you can do it (like adding the bot to your server)!!"
        ]

        if not hasattr(discord.InteractionResponse, "_topgg_original_send_message"):
            discord.InteractionResponse._topgg_original_send_message = discord.InteractionResponse.send_message

            async def patched_send_message(response, content=None, **kwargs):
                interaction = response._parent

                result = await discord.InteractionResponse._topgg_original_send_message(
                    response,
                    content,
                    **kwargs
                )

                if random.random() < self.chance:
                    asyncio.create_task(self.send_promo(interaction))

                return result

            discord.InteractionResponse.send_message = patched_send_message

    async def send_promo(self, interaction):
        await asyncio.sleep(0.2)

        embed = discord.Embed(
            title=random.choice(self.titles),
            description=(
                f"{random.choice(self.messages)}\n\n"
                "[💬 Join the Discord](https://discord.gg/YtQdrkxfg7)\n"
                "[🌐 Visit the Website](https://clanker.pxsl.dev/)\n"
                "[💜 Support Us](https://pxsl.dev/thanks/)"
            ),
            color=discord.Color.blurple()
        )

        embed.set_footer(text="Automated Message • Deleting soon • You won't see this again for a while.")

        try:
            message = await interaction.followup.send(
                embed=embed,
                wait=True
            )

            await asyncio.sleep(15)
            await message.delete()

        except (discord.HTTPException, discord.NotFound, discord.Forbidden):
            pass

async def setup(bot):
    await bot.add_cog(PromoPatch(bot))