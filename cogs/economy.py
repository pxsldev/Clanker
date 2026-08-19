# im a economy file!

from discord import app_commands, Interaction
from discord.ext import commands
import discord
import json
import random
import time
import sqlite3

DB_PATH = "economy.db"

class Economy(commands.GroupCog, group_name="economy"):
    def __init__(self, bot):
        self.bot = bot
        self.db = sqlite3.connect(DB_PATH)
        self.cursor = self.db.cursor()
        self._setup_db()

    def _setup_db(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            guild_id INTEGER,
            user_id INTEGER,
            balance INTEGER DEFAULT 0,
            bank INTEGER DEFAULT 0,
            inventory TEXT DEFAULT '[]',
            last_daily INTEGER DEFAULT 0,
            last_weekly INTEGER DEFAULT 0,
            last_work INTEGER DEFAULT 0,
            last_deposit INTEGER DEFAULT 0,
            last_rob INTEGER DEFAULT 0,
            last_fish INTEGER DEFAULT 0,
            daily_streak INTEGER DEFAULT 0,
            weekly_streak INTEGER DEFAULT 0,
            PRIMARY KEY (guild_id, user_id)
        )
        """)

        try:
            self.cursor.execute(
                "ALTER TABLE users ADD COLUMN last_fish INTEGER DEFAULT 0"
            )
        except sqlite3.OperationalError:
            pass

        self.db.commit()

    def user_dict(self, row):
        return {
            "guild_id": row[0],
            "user_id": row[1],
            "balance": row[2],
            "bank": row[3],
            "inventory": json.loads(row[4]),
            "last_daily": row[5],
            "last_weekly": row[6],
            "last_work": row[7],
            "last_deposit": row[8],
            "last_rob": row[9],
            "daily_streak": row[10],
            "weekly_streak": row[11],
            "last_fish": row[12],
        }

    def format_time(self, seconds: int) -> str:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        parts = []

        if days:
            parts.append(f"{days}d")

        if hours:
            parts.append(f"{hours}h")

        if minutes:
            parts.append(f"{minutes}m")

        if secs:
            parts.append(f"{secs}s")

        return " ".join(parts)

    def get_user(self, guild_id: int, user_id: int):
        self.cursor.execute("""
            SELECT
                guild_id,
                user_id,
                balance,
                bank,
                inventory,
                last_daily,
                last_weekly,
                last_work,
                last_deposit,
                last_rob,
                daily_streak,
                weekly_streak,
                last_fish
            FROM users
            WHERE guild_id=?
            AND user_id=?
        """, (
            guild_id,
            user_id
        ))

        row = self.cursor.fetchone()

        if row:
            return row

        self.cursor.execute("""
            INSERT INTO users (
                guild_id,
                user_id
            )
            VALUES (?, ?)
        """, (
            guild_id,
            user_id
        ))

        self.db.commit()

        return self.get_user(guild_id, user_id)

    def update_user(self, user):
        self.cursor.execute("""
            UPDATE users SET
                balance=?,
                bank=?,
                inventory=?,
                last_daily=?,
                last_weekly=?,
                last_work=?,
                last_deposit=?,
                last_rob=?,
                last_fish=?,
                daily_streak=?,
                weekly_streak=?
            WHERE guild_id=?
            AND user_id=?
        """, (
            user["balance"],
            user["bank"],
            json.dumps(user["inventory"]),
            user["last_daily"],
            user["last_weekly"],
            user["last_work"],
            user["last_deposit"],
            user["last_rob"],
            user["last_fish"],
            user["daily_streak"],
            user["weekly_streak"],
            user["guild_id"],
            user["user_id"]
        ))

        self.db.commit()

    def determine_rps_winner(self, user, bot):
        if user == bot:
            return "It's a tie!"

        if (
            (user == "rock" and bot == "scissors")
            or
            (user == "paper" and bot == "rock")
            or
            (user == "scissors" and bot == "paper")
        ):
            return "You win!"

        return "Clanker wins!"

    group_1 = app_commands.Group(
        name="1",
        description="Economy - page 1"
    )

    @group_1.command(
        name="balance",
        description="how much money you have"
    )
    @app_commands.describe(
        user="the user to check (defaults to you)"
    )
    async def balance(
        self,
        interaction: Interaction,
        user: discord.Member = None
    ):
        target = user or interaction.user

        row = self.get_user(
            interaction.guild.id,
            target.id
        )

        user_data = self.user_dict(row)

        wallet = user_data["balance"]
        bank = user_data["bank"]
        total = wallet + bank

        embed = discord.Embed(
            title=f"{target.name}'s Balance",
            description=(
                f"💰 Wallet: **{wallet}**\n"
                f"🏦 Bank: **{bank}**\n"
                f"📊 Total: **{total}**"
            ),
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(
            embed=embed
        )

    @group_1.command(
        name="daily",
        description="get your daily reward"
    )
    async def daily(
        self,
        interaction: Interaction
    ):
        row = self.get_user(
            interaction.guild.id,
            interaction.user.id
        )

        user = self.user_dict(row)

        now = int(time.time())

        if now - user["last_daily"] < 86400:
            remaining = 86400 - (
                now - user["last_daily"]
            )

            embed = discord.Embed(
                title="⏳ Daily Cooldown",
                description=(
                    f"You can claim your daily again in "
                    f"**{self.format_time(remaining)}**"
                ),
                color=discord.Color.red()
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

            return

        reward = random.randint(100, 300)

        if user["last_daily"] == 0:
            user["daily_streak"] = 1

        elif now - user["last_daily"] <= 172800:
            user["daily_streak"] += 1

        else:
            user["daily_streak"] = 1

        user["balance"] += reward
        user["last_daily"] = now

        self.update_user(user)

        embed = discord.Embed(
            title="🎁 Daily Reward",
            description=(
                f"You received **{reward} coins**!\n"
                f"🔥 Daily Streak: **{user['daily_streak']}**"
            ),
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(
            embed=embed
        )

    @group_1.command(
        name="weekly",
        description="get your weekly reward"
    )
    async def weekly(
        self,
        interaction: Interaction
    ):
        row = self.get_user(
            interaction.guild.id,
            interaction.user.id
        )

        user = self.user_dict(row)

        now = int(time.time())

        if now - user["last_weekly"] < 604800:
            remaining = 604800 - (
                now - user["last_weekly"]
            )

            embed = discord.Embed(
                title="⏳ Weekly Cooldown",
                description=(
                    f"You can claim your weekly again in "
                    f"**{self.format_time(remaining)}**"
                ),
                color=discord.Color.red()
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

            return

        reward = random.randint(700, 2100)

        if user["last_weekly"] == 0:
            user["weekly_streak"] = 1

        elif now - user["last_weekly"] <= 1209600:
            user["weekly_streak"] += 1

        else:
            user["weekly_streak"] = 1

        user["balance"] += reward
        user["last_weekly"] = now

        self.update_user(user)

        embed = discord.Embed(
            title="🎁 Weekly Reward",
            description=(
                f"You received **{reward} coins**!\n"
                f"🔥 Weekly Streak: **{user['weekly_streak']}**"
            ),
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(
            embed=embed
        )

    @group_1.command(
        name="work",
        description="gotta go to work"
    )
    async def work(
        self,
        interaction: Interaction
    ):
        row = self.get_user(
            interaction.guild.id,
            interaction.user.id
        )

        user = self.user_dict(row)

        now = int(time.time())

        if now - user.get("last_work", 0) < 3600:
            remaining = 3600 - (
                now - user.get("last_work", 0)
            )

            embed = discord.Embed(
                title="⏳ Work Cooldown",
                description=(
                    f"You can work again in "
                    f"**{self.format_time(remaining)}**"
                ),
                color=discord.Color.red()
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

            return

        jobs = [
            "You cleaned a suspicious basement",
            "You worked at a dodgy kebab shop",
            "You fixed Clanker's broken circuits",
            "You babysat a chaotic goblin"
        ]

        reward = random.randint(50, 150)
        job_text = random.choice(jobs)

        user["balance"] += reward
        user["last_work"] = now

        self.update_user(user)

        embed = discord.Embed(
            title="💼 Work Complete",
            description=(
                f"{job_text}\n\n"
                f"💰 Earned **{reward} coins**"
            ),
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(
            embed=embed
        )

    @group_1.command(
        name="atm",
        description="put money in ur bank or get it out"
    )
    @app_commands.describe(
        action="choose an action",
        amount="amount of coins"
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(
                name="Deposit",
                value="deposit"
            ),
            app_commands.Choice(
                name="Withdraw",
                value="withdraw"
            ),
        ]
    )
    async def atm(
        self,
        interaction: Interaction,
        action: app_commands.Choice[str],
        amount: int
    ):
        action = action.value

        row = self.get_user(
            interaction.guild.id,
            interaction.user.id
        )

        user = self.user_dict(row)

        now = int(time.time())

        if amount <= 0:
            embed = discord.Embed(
                title="❌ ATM Error",
                description="Amount must be greater than 0.",
                color=discord.Color.red()
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

            return

        if action == "deposit":

            if now - user["last_deposit"] < 3600:
                remaining = 3600 - (
                    now - user["last_deposit"]
                )

                embed = discord.Embed(
                    title="⏳ Deposit Cooldown",
                    description=(
                        f"You can deposit again in "
                        f"**{self.format_time(remaining)}**"
                    ),
                    color=discord.Color.red()
                )

                await interaction.response.send_message(
                    embed=embed,
                    ephemeral=True
                )

                return

            if amount > user["balance"]:
                embed = discord.Embed(
                    title="❌ ATM Error",
                    description="you don't have enough in your wallet.",
                    color=discord.Color.red()
                )

                await interaction.response.send_message(
                    embed=embed,
                    ephemeral=True
                )

                return

            user["balance"] -= amount
            user["bank"] += amount
            user["last_deposit"] = now

            self.update_user(user)

            embed = discord.Embed(
                title="🏦 Deposit Successful",
                description=(
                    f"Deposited **{amount} coins** "
                    f"into your bank."
                ),
                color=discord.Color.blurple()
            )

        else:
            if amount > user["bank"]:
                embed = discord.Embed(
                    title="❌ ATM Error",
                    description="you don't have that much in your bank",
                    color=discord.Color.red()
                )

                await interaction.response.send_message(
                    embed=embed,
                    ephemeral=True
                )

                return

            user["balance"] += amount
            user["bank"] -= amount

            self.update_user(user)

            embed = discord.Embed(
                title="🏦 Withdrawal Successful",
                description=(
                    f"Withdrew **{amount} coins** "
                    f"from your bank."
                ),
                color=discord.Color.blurple()
            )

        await interaction.response.send_message(
            embed=embed
        )

    @group_1.command(
        name="rob",
        description="do a thievery to another person"
    )
    @app_commands.describe(
        target="The user you want to rob"
    )
    async def rob(
        self,
        interaction: Interaction,
        target: discord.Member
    ):
        if target.id == interaction.user.id:
            embed = discord.Embed(
                title="❌ Rob Failed",
                description="You can't rob yourself!",
                color=discord.Color.red()
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

            return

        row = self.get_user(
            interaction.guild.id,
            interaction.user.id
        )

        user = self.user_dict(row)

        target_row = self.get_user(
            interaction.guild.id,
            target.id
        )

        target_user = self.user_dict(target_row)

        now = int(time.time())

        if now - user["last_rob"] < 3600:
            remaining = 3600 - (
                now - user["last_rob"]
            )

            embed = discord.Embed(
                title="⏳ Rob Cooldown",
                description=(
                    f"You can rob again in "
                    f"**{self.format_time(remaining)}**"
                ),
                color=discord.Color.red()
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

            return

        if target_user["balance"] <= 0:
            embed = discord.Embed(
                title="❌ Rob Failed",
                description=(
                    "This user has no coins in "
                    "their wallet to rob!"
                ),
                color=discord.Color.red()
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

            return

        stolen = random.randint(
            int(target_user["balance"] * 0.1),
            max(
                1,
                int(target_user["balance"] * 0.5)
            )
        )

        target_user["balance"] -= stolen
        user["balance"] += stolen
        user["last_rob"] = now

        self.update_user(user)
        self.update_user(target_user)

        embed = discord.Embed(
            title="💰 Robbery Successful",
            description=(
                f"You stole **{stolen} coins** "
                f"from {target.mention}!"
            ),
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(
            embed=embed
        )

    @group_1.command(
        name="roulette",
        description="spin the roulette wheel"
    )
    @app_commands.describe(
        bet="your bet",
        color="pick a color"
    )
    @app_commands.choices(
        color=[
            app_commands.Choice(
                name="🔴 Red",
                value="red"
            ),
            app_commands.Choice(
                name="⚫ Black",
                value="black"
            ),
            app_commands.Choice(
                name="🟢 Green",
                value="green"
            ),
        ]
    )
    async def roulette(
        self,
        interaction: Interaction,
        bet: int,
        color: app_commands.Choice[str]
    ):
        row = self.get_user(
            interaction.guild.id,
            interaction.user.id
        )

        user = self.user_dict(row)

        color = color.value

        if bet <= 0 or bet > user["balance"]:
            embed = discord.Embed(
                title="❌ Invalid Bet",
                description="Invalid or insufficient balance.",
                color=discord.Color.red()
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

            return

        roll = random.randint(1, 100)

        if roll <= 48:
            result = "red"
        elif roll <= 96:
            result = "black"
        else:
            result = "green"

        if color == result:
            if result == "green":
                winnings = bet * 14
            else:
                winnings = bet * 2

            user["balance"] += winnings
            self.update_user(user)

            outcome = (
                f"🎉 You won **{winnings} coins!**"
            )

        else:
            user["balance"] -= bet
            self.update_user(user)

            outcome = (
                f"💀 You lost **{bet} coins.**"
            )

        emoji = {
            "red": "🔴",
            "black": "⚫",
            "green": "🟢"
        }

        embed = discord.Embed(
            title="🎰 Roulette",
            description=(
                f"You chose: {emoji[color]} **{color}**\n"
                f"Ball landed on: {emoji[result]} **{result}**\n\n"
                f"{outcome}"
            ),
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(
            embed=embed
        )

    @group_1.command(
        name="coinflip",
        description="flip a coin and gamble"
    )
    @app_commands.describe(
        bet="your bet",
        choice="pick heads or tails"
    )
    @app_commands.choices(
        choice=[
            app_commands.Choice(
                name="🪙 Heads",
                value="heads"
            ),
            app_commands.Choice(
                name="🪙 Tails",
                value="tails"
            ),
        ]
    )
    async def coinflip(
        self,
        interaction: Interaction,
        bet: int,
        choice: app_commands.Choice[str]
    ):
        row = self.get_user(
            interaction.guild.id,
            interaction.user.id
        )

        user = self.user_dict(row)

        choice = choice.value

        if bet <= 0 or bet > user["balance"]:
            embed = discord.Embed(
                title="❌ Invalid Bet",
                description="Invalid or insufficient balance.",
                color=discord.Color.red()
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

            return

        result = random.choice([
            "heads",
            "tails"
        ])

        if result == choice:
            winnings = bet

            user["balance"] += winnings
            self.update_user(user)

            outcome = (
                f"🎉 You won **{winnings} coins!**"
            )

        else:
            user["balance"] -= bet
            self.update_user(user)

            outcome = (
                f"💀 You lost **{bet} coins.**"
            )

        embed = discord.Embed(
            title="🪙 Coinflip",
            description=(
                f"You chose **{choice}**\n"
                f"It landed on **{result}**\n\n"
                f"{outcome}"
            ),
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(
            embed=embed
        )

    @group_1.command(
        name="dice",
        description="roll a dice and gamble"
    )
    @app_commands.describe(
        bet="your bet",
        number="pick a number (1-6)"
    )
    async def dice(
        self,
        interaction: Interaction,
        bet: int,
        number: int
    ):
        row = self.get_user(
            interaction.guild.id,
            interaction.user.id
        )

        user = self.user_dict(row)

        if number < 1 or number > 6:
            embed = discord.Embed(
                title="❌ Invalid Number",
                description=(
                    "Pick a number between **1 and 6**."
                ),
                color=discord.Color.red()
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

            return

        if bet <= 0 or bet > user["balance"]:
            embed = discord.Embed(
                title="❌ Invalid Bet",
                description="Invalid or insufficient balance.",
                color=discord.Color.red()
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

            return

        roll = random.randint(1, 6)

        if roll == number:
            winnings = bet * 5

            user["balance"] += winnings
            self.update_user(user)

            outcome = (
                f"🎉 Exact match! "
                f"You won **{winnings} coins!**"
            )

        else:
            user["balance"] -= bet
            self.update_user(user)

            outcome = (
                f"💀 Rolled **{roll}**. "
                f"You lost **{bet} coins.**"
            )

        embed = discord.Embed(
            title="🎲 Dice Roll",
            description=(
                f"You picked **{number}**\n"
                f"Rolled: **{roll}**\n\n"
                f"{outcome}"
            ),
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(
            embed=embed
        )

    @group_1.command(
        name="slots",
        description="lets go gambling!111"
    )
    @app_commands.describe(
        bet="your bet"
    )
    async def slots(
        self,
        interaction: Interaction,
        bet: int
    ):
        row = self.get_user(
            interaction.guild.id,
            interaction.user.id
        )

        user = self.user_dict(row)

        if bet <= 0 or bet > user["balance"]:
            embed = discord.Embed(
                title="❌ Invalid Bet",
                description="Invalid or insufficient balance.",
                color=discord.Color.red()
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

            return

        symbols = [
            "🍒",
            "🍋",
            "🍊",
            "🍇",
            "⭐",
            "💎"
        ]

        result = [
            random.choice(symbols)
            for _ in range(3)
        ]

        if result[0] == result[1] == result[2]:

            if result[0] == "💎":
                winnings = bet * 10
            else:
                winnings = bet * 5

            user["balance"] += winnings
            self.update_user(user)

            outcome = (
                f"💎 JACKPOT! "
                f"You won **{winnings} coins!**"
            )

        elif (
            result[0] == result[1]
            or result[1] == result[2]
        ):
            winnings = bet * 2

            user["balance"] += winnings
            self.update_user(user)

            outcome = (
                f"✨ Nice! "
                f"You won **{winnings} coins!**"
            )

        else:
            user["balance"] -= bet
            self.update_user(user)

            outcome = (
                f"💀 You lost **{bet} coins.**"
            )

        embed = discord.Embed(
            title="🎰 Slot Machine",
            description=(
                f"{result[0]} | "
                f"{result[1]} | "
                f"{result[2]}\n\n"
                f"{outcome}"
            ),
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(
            embed=embed
        )

    @group_1.command(
        name="top",
        description="see the richest people in the server"
    )
    async def top(
        self,
        interaction: Interaction
    ):
        self.cursor.execute("""
            SELECT user_id, balance, bank
            FROM users
            WHERE guild_id=?
        """, (
            interaction.guild.id,
        ))

        rows = self.cursor.fetchall()

        if not rows:
            embed = discord.Embed(
                title="🏆 Leaderboard",
                description="No data yet.",
                color=discord.Color.blurple()
            )

            await interaction.response.send_message(
                embed=embed
            )

            return

        totals = []

        for user_id, balance, bank in rows:
            totals.append(
                (
                    user_id,
                    balance + bank
                )
            )

        sorted_users = sorted(
            totals,
            key=lambda x: x[1],
            reverse=True
        )

        page = 0
        page_size = 10

        async def make_embed():
            start = page * page_size
            end = start + page_size

            chunk = sorted_users[start:end]

            description = ""

            for i, (user_id, total) in enumerate(
                chunk,
                start=start + 1
            ):
                member = interaction.guild.get_member(
                    int(user_id)
                )

                if member is None:
                    try:
                        member = await self.bot.fetch_user(
                            int(user_id)
                        )
                    except Exception:
                        member = None

                if member:
                    name = member.name
                else:
                    name = f"Unknown User ({user_id})"

                description += (
                    f"**#{i}** — "
                    f"{name}: **{total}** coins\n"
                )

            embed = discord.Embed(
                title="🏆 Leaderboard",
                description=description or "No data.",
                color=discord.Color.blurple()
            )

            max_page = (
                len(sorted_users) - 1
            ) // page_size

            embed.set_footer(
                text=(
                    f"Page {page + 1} / "
                    f"{max_page + 1}"
                )
            )

            return embed

        view = discord.ui.View(
            timeout=60
        )

        async def update(
            msg_interaction: Interaction
        ):
            await msg_interaction.response.edit_message(
                embed=await make_embed(),
                view=view
            )

        prev_btn = discord.ui.Button(
            label="⬅️",
            style=discord.ButtonStyle.gray
        )

        next_btn = discord.ui.Button(
            label="➡️",
            style=discord.ButtonStyle.gray
        )

        async def prev_callback(
            btn_interaction: Interaction
        ):
            nonlocal page

            if (
                btn_interaction.user.id
                != interaction.user.id
            ):
                return await btn_interaction.response.send_message(
                    embed=discord.Embed(
                        title="❌ Error",
                        description="Not your leaderboard.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )

            if page > 0:
                page -= 1

            await update(btn_interaction)

        async def next_callback(
            btn_interaction: Interaction
        ):
            nonlocal page

            if (
                btn_interaction.user.id
                != interaction.user.id
            ):
                return await btn_interaction.response.send_message(
                    embed=discord.Embed(
                        title="❌ Error",
                        description="Not your leaderboard.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )

            max_page = (
                len(sorted_users) - 1
            ) // page_size

            if page < max_page:
                page += 1

            await update(btn_interaction)

        prev_btn.callback = prev_callback
        next_btn.callback = next_callback

        view.add_item(prev_btn)
        view.add_item(next_btn)

        await interaction.response.send_message(
            embed=await make_embed(),
            view=view
        )

    @group_1.command(
        name="gift",
        description="give money to another user"
    )
    @app_commands.describe(
        user="who you want to gift coins to",
        amount="how many coins"
    )
    async def gift(
        self,
        interaction: Interaction,
        user: discord.Member,
        amount: int
    ):
        if user.id == interaction.user.id:
            embed = discord.Embed(
                title="❌ Gift Failed",
                description=(
                    "You can’t gift money to yourself."
                ),
                color=discord.Color.red()
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

            return

        if amount <= 0:
            embed = discord.Embed(
                title="❌ Gift Failed",
                description=(
                    "Amount must be greater than 0."
                ),
                color=discord.Color.red()
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

            return

        sender_row = self.get_user(
            interaction.guild.id,
            interaction.user.id
        )

        sender = self.user_dict(sender_row)

        receiver_row = self.get_user(
            interaction.guild.id,
            user.id
        )

        receiver = self.user_dict(receiver_row)

        if sender["balance"] < amount:
            embed = discord.Embed(
                title="❌ Gift Failed",
                description=(
                    "You don’t have enough coins."
                ),
                color=discord.Color.red()
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

            return

        sender["balance"] -= amount
        receiver["balance"] += amount

        self.update_user(sender)
        self.update_user(receiver)

        embed = discord.Embed(
            title="🎁 Gift Sent!",
            description=(
                f"You gifted **{amount} coins** "
                f"to {user.mention}!\n"
                f"💸 Your new balance: "
                f"**{sender['balance']}**"
            ),
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(
            embed=embed
        )

    @group_1.command(
        name="rps",
        description="bet coins on rock paper scissors with Clanker"
    )
    @app_commands.choices(
        choice=[
            app_commands.Choice(
                name="🪨 Rock",
                value="rock"
            ),
            app_commands.Choice(
                name="📄 Paper",
                value="paper"
            ),
            app_commands.Choice(
                name="✂️ Scissors",
                value="scissors"
            ),
        ]
    )
    async def rps(
        self,
        interaction: Interaction,
        choice: app_commands.Choice[str],
        bet: int
    ):
        choices = [
            "rock",
            "paper",
            "scissors"
        ]

        emoji_map = {
            "rock": "🪨",
            "paper": "📄",
            "scissors": "✂️"
        }

        row = self.get_user(
            interaction.guild.id,
            interaction.user.id
        )

        user = self.user_dict(row)

        if bet <= 0:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Invalid Bet",
                    description=(
                        "Bet must be higher than 0."
                    ),
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        if bet > user["balance"]:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Not Enough Coins",
                    description=(
                        "You don’t have enough money "
                        "for that bet."
                    ),
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        user_choice = choice.value
        bot_choice = random.choice(choices)

        result = self.determine_rps_winner(
            user_choice,
            bot_choice
        )

        if result == "You win!":
            user["balance"] += bet
            outcome = (
                f"🏆 You won **{bet} coins!**"
            )
            result_emoji = "🏆"

        elif result == "Clanker wins!":
            user["balance"] -= bet
            outcome = (
                f"🤖 You lost **{bet} coins!**"
            )
            result_emoji = "🤖"

        else:
            outcome = (
                "🤝 It's a tie — no coins lost!"
            )
            result_emoji = "🤝"

        self.update_user(user)

        embed = discord.Embed(
            title=(
                f"{result_emoji} "
                f"Rock Paper Scissors"
            ),
            description=(
                f"You: "
                f"{emoji_map[user_choice]} "
                f"**{user_choice}**\n"
                f"Clanker: "
                f"{emoji_map[bot_choice]} "
                f"**{bot_choice}**\n\n"
                f"{outcome}"
            ),
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(
            embed=embed
        )

    @group_1.command(
        name="fish",
        description="lets go fishing!"
    )
    async def fish(
        self,
        interaction: Interaction
    ):
        guild_id = interaction.guild.id
        user_id = interaction.user.id
        now = int(time.time())
        cooldown = 600

        self.get_user(guild_id, user_id)

        self.cursor.execute("""
            SELECT last_fish
            FROM users
            WHERE guild_id=?
            AND user_id=?
        """, (
            guild_id,
            user_id
        ))

        row = self.cursor.fetchone()
        last_fish = row[0] if row else 0

        if now - last_fish < cooldown:
            remaining = cooldown - (now - last_fish)

            embed = discord.Embed(
                title="⏳ Fishing Cooldown",
                description=(
                    f"You can fish again in "
                    f"**{self.format_time(remaining)}**"
                ),
                color=discord.Color.red()
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

            return

        fish_types = [
            "🤖 Clanker Fish",
            "🎣 Fishing Pole",
            "🥾 Boot",
            "🐟 Generic Fish",
            "🐠 Fancy Fish",
            "🐡 Pufferfish",
            "🦈 Shark",
            "🐋 Whale",
            "🦀 Crab",
            "🦑 Squid",
            "🦐 Shrimp",
            "🦞 Lobster"
        ]

        caught_fish = random.choice(fish_types)
        reward = random.randint(1, 1200)

        self.cursor.execute("""
            UPDATE users
            SET
                balance = balance + ?,
                last_fish = ?
            WHERE guild_id=?
            AND user_id=?
        """, (
            reward,
            now,
            guild_id,
            user_id
        ))

        self.db.commit()

        embed = discord.Embed(
            title="🎣 Fishing Success!",
            description=(
                f"You caught a {caught_fish} "
                f"and earned **{reward} coins!**"
            ),
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(
            embed=embed
        )

async def setup(bot):
    await bot.add_cog(Economy(bot))