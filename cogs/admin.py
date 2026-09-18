# im an adminininmimimmmimin file!

from discord import app_commands, Interaction
from discord.ext import commands
import discord
import json
import math
import time

def owner_check():
    async def predicate(interaction: Interaction):
        return interaction.user.id in interaction.client.data.get("owners", [])

    return app_commands.check(predicate)

def admin_check():
    async def predicate(interaction: Interaction):
        return (
            interaction.user.id in interaction.client.data.get("admins", [])
            or interaction.user.id in interaction.client.data.get("owners", [])
        )

    return app_commands.check(predicate)

class Admin(commands.GroupCog, group_name="admin"):

    def __init__(self, bot):
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.guild is None:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Server Installation Required",
                    description=(
                        "Sorry, Clanker can only be installed in a server.\n\n"
                        "Please add Clanker to a server before using these commands."
                    ),
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return False

        try:
            await interaction.guild.fetch_member(self.bot.user.id)

        except discord.NotFound:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Clanker Isn't Installed",
                    description=(
                        "Clanker isn't installed in this server.\n\n"
                        "Please add Clanker to this server before using these commands."
                    ),
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return False

        except discord.Forbidden:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Unable to Check",
                    description=(
                        "I couldn't verify whether Clanker is installed "
                        "in this server."
                    ),
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return False

        except discord.HTTPException:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Discord Error",
                    description=(
                        "Discord didn't let me verify whether Clanker "
                        "is installed in this server. Please try again."
                    ),
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return False

        return True

    def save_data(self):
        with open("data.json", "w") as f:
            json.dump(self.bot.data, f, indent=4)

    # ============================================================
    # PAGE 1
    # ============================================================

    group_1 = app_commands.Group(
        name="1",
        description="Admin - page 1"
    )

    @group_1.command(
        name="addadmin",
        description="(OWNER) give someone admin"
    )
    @owner_check()
    async def addadmin(
        self,
        interaction: Interaction,
        user: discord.Member
    ):
        if user.id in self.bot.data.get("admins", []):
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Already Admin",
                    description=f"{user.mention} is already an admin.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        self.bot.data.setdefault("admins", []).append(user.id)
        self.save_data()

        await interaction.response.send_message(
            embed=discord.Embed(
                title="✅ Admin Added",
                description=f"{user.mention} is now an admin.",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

    @group_1.command(
        name="removeadmin",
        description="(OWNER) remove admin"
    )
    @owner_check()
    async def removeadmin(
        self,
        interaction: Interaction,
        user: discord.Member
    ):
        if user.id not in self.bot.data.get("admins", []):
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Not Admin",
                    description=f"{user.mention} is not an admin.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        self.bot.data["admins"].remove(user.id)
        self.save_data()

        await interaction.response.send_message(
            embed=discord.Embed(
                title="🗑️ Admin Removed",
                description=f"{user.mention} is no longer an admin.",
                color=discord.Color.orange()
            ),
            ephemeral=True
        )

    @group_1.command(
        name="listadmins",
        description="(OWNER) list admins"
    )
    @owner_check()
    async def listadmins(
        self,
        interaction: Interaction
    ):
        admins = self.bot.data.get("admins", [])

        if not admins:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="👮 Admin List",
                    description="No admins are currently set.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        mentions = [f"<@{uid}>" for uid in admins]

        await interaction.response.send_message(
            embed=discord.Embed(
                title="👮 Admin List",
                description="\n".join(mentions),
                color=discord.Color.blurple()
            ),
            ephemeral=True
        )

    @group_1.command(
        name="license",
        description="(OWNER) send license troll message"
    )
    async def license(
        self,
        interaction: Interaction,
        channel: discord.TextChannel
    ):
        if (
            interaction.user.id not in self.bot.data.get("admins", [])
            and interaction.user.id not in self.bot.data.get("owners", [])
        ):
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ No Permission",
                    description="You are not allowed to use this command.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        class RenewView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)

            @discord.ui.button(
                label="Renew License",
                style=discord.ButtonStyle.red
            )
            async def renew(
                self,
                interaction_btn: Interaction,
                button: discord.ui.Button
            ):
                await interaction_btn.message.delete()

                await interaction_btn.response.send_message(
                    embed=discord.Embed(
                        title="😂 Trolled",
                        description="haha lol trolled by the bot admins imagine",
                        color=discord.Color.blurple()
                    ),
                    ephemeral=True
                )

                self.stop()

        embed = discord.Embed(
            title="⚠️ License Expired",
            description="Your license is outdated.\nClick below to renew it.",
            color=discord.Color.red()
        )

        try:
            await channel.send(
                embed=embed,
                view=RenewView()
            )

            await interaction.response.send_message(
                embed=discord.Embed(
                    title="📩 License Sent",
                    description=f"Sent to {channel.mention}",
                    color=discord.Color.green()
                ),
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Missing Permissions",
                    description="I can't send messages in that channel.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

    @group_1.command(
        name="give",
        description="(OWNER) give money"
    )
    @owner_check()
    async def give(
        self,
        interaction: Interaction,
        user: discord.Member,
        amount: int
    ):
        if amount <= 0:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Invalid Amount",
                    description="Amount must be greater than 0.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        economy = self.bot.get_cog("Economy")

        if not economy:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Error",
                    description="Economy cog not loaded.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        row = economy.get_user(
            interaction.guild.id,
            user.id
        )

        target = economy.user_dict(row)

        target["balance"] += amount
        economy.update_user(target)

        await interaction.response.send_message(
            embed=discord.Embed(
                title="💰 Money Given",
                description=f"Gave **{amount} coins** to {user.mention}",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

    @group_1.command(
        name="take",
        description="(OWNER) remove money"
    )
    @owner_check()
    async def take(
        self,
        interaction: Interaction,
        user: discord.Member,
        amount: int
    ):
        if amount <= 0:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Invalid Amount",
                    description="Amount must be greater than 0.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        economy = self.bot.get_cog("Economy")

        if not economy:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Error",
                    description="Economy cog not loaded.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        row = economy.get_user(
            interaction.guild.id,
            user.id
        )

        target = economy.user_dict(row)

        removed = min(amount, target["balance"])
        target["balance"] -= removed

        economy.update_user(target)

        await interaction.response.send_message(
            embed=discord.Embed(
                title="💸 Money Removed",
                description=f"Removed **{removed} coins** from {user.mention}",
                color=discord.Color.red()
            ),
            ephemeral=True
        )

    @group_1.command(
        name="dm",
        description="(OWNER) DM a user"
    )
    @owner_check()
    async def dm(
        self,
        interaction: Interaction,
        user: discord.User,
        title: str,
        message: str
    ):
        try:
            embed = discord.Embed(
                title=title,
                description=message,
                color=discord.Color.blurple()
            )

            await user.send(embed=embed)

            await interaction.response.send_message(
                embed=discord.Embed(
                    title="📩 DM Sent",
                    description=f"Sent to {user.mention}",
                    color=discord.Color.green()
                ),
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ DM Failed",
                    description="User has DMs disabled.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

    @group_1.command(
        name="servers",
        description="(OWNER/ADMIN) list all bot servers"
    )
    @admin_check()
    async def servers(
        self,
        interaction: Interaction
    ):
        guilds = sorted(
            self.bot.guilds,
            key=lambda g: g.member_count or 0,
            reverse=True
        )

        per_page = 10
        pages = math.ceil(len(guilds) / per_page)
        page = 0

        def make_embed(page: int):
            start = page * per_page
            end = start + per_page
            chunk = guilds[start:end]

            desc = ""

            for i, g in enumerate(chunk, start=start + 1):
                desc += (
                    f"**{i}. {g.name}**\n"
                    f"👥 {g.member_count} members\n"
                    f"🆔 `{g.id}`\n\n"
                )

            embed = discord.Embed(
                title=f"🗂️ Server List ({page + 1}/{pages})",
                description=desc or "No servers found.",
                color=discord.Color.blurple()
            )

            embed.set_footer(
                text=f"Total servers: {len(guilds)}"
            )

            return embed

        class ServerView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.page = 0

            async def update(
                self,
                interaction_btn: Interaction
            ):
                await interaction_btn.response.edit_message(
                    embed=make_embed(self.page),
                    view=self
                )

            @discord.ui.button(
                label="⬅️ Prev",
                style=discord.ButtonStyle.secondary
            )
            async def prev(
                self,
                interaction_btn: Interaction,
                button: discord.ui.Button
            ):
                if self.page > 0:
                    self.page -= 1

                await self.update(interaction_btn)

            @discord.ui.button(
                label="➡️ Next",
                style=discord.ButtonStyle.secondary
            )
            async def next(
                self,
                interaction_btn: Interaction,
                button: discord.ui.Button
            ):
                if self.page < pages - 1:
                    self.page += 1

                await self.update(interaction_btn)

        await interaction.response.send_message(
            embed=make_embed(page),
            view=ServerView(),
            ephemeral=True
        )

    @group_1.command(
        name="ccu",
        description="(OWNER/ADMIN) View current CCU"
    )
    @admin_check()
    async def ccu(
        self,
        interaction: Interaction
    ):
        now = time.time()

        expired = [
            uid
            for uid, last_seen in self.bot.active_users.items()
            if now - last_seen > 300
        ]

        for uid in expired:
            del self.bot.active_users[uid]

        embed = discord.Embed(
            title="📊 Current CCU",
            colour=discord.Colour.blurple()
        )

        embed.add_field(
            name="Current",
            value=f"**{len(self.bot.active_users)}** users",
            inline=True
        )

        embed.add_field(
            name="Peak Since Restart",
            value=f"**{self.bot.peak_ccu}** users",
            inline=True
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Admin(bot))