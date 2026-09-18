# pxsl :3
# dashcrikeydash

# i just want to say, we are sorry for writing some of the code in a terrible way.
# We are literally not cleaning ts up - pxsl

# anyway, now that the bot is open sourced, you can see how we are stealing all ur data and selling it to the highest bidder mwahahaha - pxsl

import discord
from discord.ext import commands, tasks
import asyncio
import os
import json
import time
import topgg
import aiohttp

with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

TOKEN = data.get("token")
if not TOKEN:
    raise ValueError("Token not found in data.json!")

TOPGG_TOKEN = data.get("topgg_token")
if not TOPGG_TOKEN:
    raise ValueError("TOPGG_TOKEN not found in data.json!")

PXSL_API_KEY = data.get("pxsl_api_key")
if not PXSL_API_KEY:
    raise ValueError("pxsl_api_key not found in data.json!")

PXSL_API_URL = "https://api.pxsl.dev/clanker/update"

TESTING = False
TEST_GUILD_ID = 1545958838480408596

cooldowns = {}

intents = discord.Intents.default()
intents.guilds = True

class Clanker(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(
            command_prefix="lol this bot uses slash commands idot", # this literally does nothing im being serious lol - pxsl
            intents=intents
        )

        self.dbl = None
        self.active_users = {}
        self.peak_ccu = 0
        self.start_time = time.time()
        self.total_commands = 0
        self.command_timestamps = []
        self.last_command_at = None

    async def send_to_api(self, payload):
        headers = {
            "Authorization": f"Bearer {PXSL_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "Clanker/1.0 (https://clanker.pxsl.dev)"
        }

        timeout = aiohttp.ClientTimeout(total=15)

        try:
            async with aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            ) as session:

                async with session.post(
                    PXSL_API_URL,
                    json=payload
                ) as response:

                    response_text = await response.text()

                    if response.status != 200:
                        print(
                            f"[API] Request failed "
                            f"(HTTP {response.status})"
                        )

                        print(
                            f"[API] Response: {response_text}"
                        )

                        return False

                    try:
                        result = json.loads(response_text)

                    except json.JSONDecodeError:
                        print(
                            "[API] Server returned invalid JSON:"
                        )

                        print(response_text)

                        return False

                    if not result.get("success"):
                        print(
                            f"[API] Server rejected request: "
                            f"{result}"
                        )

                        return False

                    print(
                        f"[API] Successfully updated: "
                        f"{result.get('updated', [])}"
                    )

                    return True

        except asyncio.TimeoutError:
            print(
                "[API] Request timed out after 15 seconds"
            )

        except aiohttp.ClientConnectionError as e:
            print(
                f"[API] Connection failed: {e}"
            )

        except aiohttp.ClientError as e:
            print(
                f"[API] HTTP client error: {e}"
            )

        except Exception as e:
            print(
                f"[API] Unexpected error: "
                f"{type(e).__name__}: {e}"
            )

        return False

    def export_commands(self):
        commands_data = []

        def walk_command(command, parent_path=""):
            current_path = (
                f"{parent_path} {command.name}".strip()
            )

            if isinstance(command, discord.app_commands.Group):
                for child in command.commands:
                    walk_command(child, current_path)

                return

            if "admin" in current_path.lower():
                return

            command_data = command.to_dict(self.tree)
            command_data["name"] = current_path

            commands_data.append(command_data)

        for command in self.tree.get_commands():
            walk_command(command)

        with open(
            "commands.json",
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                commands_data,
                f,
                indent=4,
                ensure_ascii=False
            )

        print(
            f"[COMMANDS] Exported "
            f"{len(commands_data)} executable slash commands!"
        )

        return commands_data
    
    async def update_commands_on_api(self):
        try:
            with open(
                "commands.json",
                "r",
                encoding="utf-8"
            ) as f:
                commands_data = json.load(f)

            payload = {
                "commands": commands_data
            }

            success = await self.send_to_api(payload)

            if success:
                print(
                    f"[API] Uploaded "
                    f"{len(commands_data)} commands"
                )
            else:
                print(
                    "[API] Failed to upload commands.json"
                )

        except FileNotFoundError:
            print(
                "[API] commands.json does not exist"
            )

        except json.JSONDecodeError as e:
            print(
                f"[API] commands.json contains invalid JSON: {e}"
            )

        except Exception as e:
            print(
                f"[API] Failed to prepare commands.json: "
                f"{type(e).__name__}: {e}"
            )

    def build_stats(self):
        now = time.time()

        guild_count = len(self.guilds)

        total_members = sum(
            guild.member_count or 0
            for guild in self.guilds
        )

        expired = [
            user_id
            for user_id, last_seen in self.active_users.items()
            if now - last_seen > 300
        ]

        for user_id in expired:
            del self.active_users[user_id]

        current_ccu = len(self.active_users)

        recent_commands = [
            timestamp
            for timestamp in self.command_timestamps
            if now - timestamp <= 60
        ]

        self.command_timestamps = recent_commands

        return {
            "guilds": guild_count,
            "users": total_members,

            "current_ccu": current_ccu,
            "peak_ccu": self.peak_ccu,

            "commands_since_restart": self.total_commands,
            "commands_per_minute": len(recent_commands),
            "last_command_at": self.last_command_at,

            "uptime_seconds": int(
                now - self.start_time
            ),

            "updated_at": int(now)
        }

    async def send_current_stats(self):
        try:
            stats = self.build_stats()

            success = await self.send_to_api({
                "stats": stats
            })

            if success:
                print(
                    "[API] Current stats uploaded"
                )
            else:
                print(
                    "[API] Failed to upload current stats"
                )

            return success

        except Exception as e:
            print(
                f"[API] Failed to build/send stats: "
                f"{type(e).__name__}: {e}"
            )

            return False

    async def setup_hook(self):
        print("[BOOT] Loading cogs...")

        for file in os.listdir("./cogs"):
            if file.endswith(".py"):
                await self.load_extension(
                    f"cogs.{file[:-3]}"
                )

                print(
                    f"[BOOT] Loaded cog: {file}"
                )

        self.dbl = topgg.DBLClient(
            self,
            TOPGG_TOKEN
        )

        print("[BOOT] Syncing commands...")

        if TESTING:
            for i in range(5):
                print(
                    "[BOOT] Running in TESTING mode, "
                    "syncing to TEST guild only."
                )

            guild = discord.Object(
                id=TEST_GUILD_ID
            )

            self.tree.copy_global_to(
                guild=guild
            )

            synced = await self.tree.sync(
                guild=guild
            )

            print(
                f"[SYNC] Synced "
                f"{len(synced)} commands to TEST guild"
            )

            self.export_commands()

            print(
                "[TOP.GG] Stats update loop not starting, "
                "as we are in testing mode..."
            )

        else:
            try:
                await self.tree.sync()

                print(
                    "[SYNC] Cleared leftover commands "
                    "from test guild"
                )

            except Exception:
                pass

            synced = await self.tree.sync()

            print(
                f"[SYNC] Synced "
                f"{len(synced)} global commands"
            )

            self.export_commands()

            print(
                "[API] Updating command data..."
            )

            await self.update_commands_on_api()

            print(
                "[API] Sending initial stats..."
            )

            await self.send_current_stats()

            self.update_stats.start()

            print(
                "[TOP.GG] Stats update loop starting..."
            )

        print(
            "[BOOT] Status loop starting..."
        )

        self.statusloop.start()

        if not TESTING:
            print(
                "[BOOT] API stats loop starting..."
            )

            self.api_stats_loop.start()

        else:
            print(
                "[API] Stats update loop not starting, "
                "as we are in testing mode."
            )

    @tasks.loop(seconds=15)
    async def statusloop(self):
        guild_count = len(self.guilds)

        total_members = sum(
            guild.member_count or 0
            for guild in self.guilds
        )

        activity = discord.CustomActivity(
            name=f"clanking in {guild_count:,} servers!"
        )

        await self.change_presence(
            activity=activity
        )

        print(
            f"[STATUS UPDATE] "
            f"Guilds: {guild_count} | "
            f"Members: {total_members} |"
            f"Shards: {self.shard_count}"
        )

    @statusloop.before_loop
    async def before_statusloop(self):
        await self.wait_until_ready()

    @tasks.loop(minutes=30)
    async def update_stats(self):
        try:
            await self.dbl.post_guild_count()

            print(
                f"[TOPGG] Posted guild count: "
                f"{len(self.guilds)}"
            )

        except Exception as e:
            print(
                "[TOPGG] Failed to post:"
            )

            print(e)

    @update_stats.before_loop
    async def before_update_stats(self):
        await self.wait_until_ready()

    @tasks.loop(minutes=5)
    async def api_stats_loop(self):
        try:
            stats = self.build_stats()

            success = await self.send_to_api({
                "stats": stats
            })

            if success:
                print(
                    f"[API] Updated stats.json | "
                    f"{stats['guilds']:,} servers | "
                    f"{stats['users']:,} users | "
                    f"CCU {stats['current_ccu']:,} | "
                    f"Peak {stats['peak_ccu']:,} | "
                    f"{stats['commands_per_minute']:,} "
                    f"commands/min"
                )

            else:
                print(
                    "[API] Failed to update stats.json"
                )

        except Exception as e:
            print(
                f"[API] Stats loop error: "
                f"{type(e).__name__}: {e}"
            )

    @api_stats_loop.before_loop
    async def before_api_stats_loop(self):
        await self.wait_until_ready()

bot = Clanker()
bot.data = data

@bot.event
async def on_ready():
    print(
        f"[READY] Logged in as {bot.user}"
    )

    print(
        "Clanker is alive 😎"
    )

@bot.event
async def on_interaction(
    interaction: discord.Interaction
):
    if interaction.type == discord.InteractionType.application_command:
        now = time.time()

        bot.active_users[
            interaction.user.id
        ] = now

        expired = [
            uid
            for uid, last_seen in bot.active_users.items()
            if now - last_seen > 300
        ]

        for uid in expired:
            del bot.active_users[uid]

        bot.peak_ccu = max(
            bot.peak_ccu,
            len(bot.active_users)
        )

        cmd = interaction.data.get("name")
        options = interaction.data.get("options", [])

        args = (
            " ".join(
                str(opt["value"])
                for opt in options
            )
            if options
            else ""
        )

        bot.total_commands += 1
        bot.command_timestamps.append(now)
        bot.last_command_at = now

        print(
            f"[COMMAND LOG] "
            f"@{interaction.user}: "
            f"{cmd} {args}"
        )

class WelcomeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(
            discord.ui.Button(
                label="Join the Community",
                emoji="💬",
                url="https://discord.gg/YtQdrkxfg7"
            )
        )

        self.add_item(
            discord.ui.Button(
                label="Legal & Privacy",
                emoji="📄",
                url="https://clanker.pxsl.dev/legal"
            )
        )

@bot.event
async def on_guild_join(guild: discord.Guild):
    embed = discord.Embed(
        title="👋 Thanks for adding Clanker!",
        description=(
            "Thanks for inviting **Clanker** to your server! ❤️\n\n"

            "## 💬 Join the Clanker Community\n"
            "Clanker isn't just a bot - it's a community too!\n\n"

            "Join our Discord to **meet other Clanker users, chat, "
            "share memes, suggest new features, report bugs, get "
            "updates, and take part in community events.**\n\n"

            "We've got **60,000+ users and 100+ servers**, and "
            "we'd love to have you be part of it. ❤️\n\n"

            "## 🔒 Privacy & Legal\n"
            "Want to know what information Clanker stores and how "
            "it's used? You can find our legal and privacy information "
            "using the button below.\n\n"

            "**Thanks for choosing Clanker! 🔧**"
        ),
        colour=discord.Colour.blurple()
    )

    embed.set_footer(
        text="Made with ❤️ by the Clanker team"
    )

    view = WelcomeView()

    preferred_names = {
        "general",
        "chat",
        "main",
        "bot",
        "bots",
        "commands",
        "clanker"
    }

    if guild.system_channel:
        perms = guild.system_channel.permissions_for(
            guild.me
        )

        if perms.send_messages and perms.embed_links:
            try:
                await guild.system_channel.send(
                    embed=embed,
                    view=view
                )

                print(
                    f"[WELCOME] Sent welcome message in "
                    f"#{guild.system_channel.name} ({guild.id})"
                )

                return

            except discord.Forbidden:
                pass

            except discord.HTTPException:
                pass

    for channel in guild.text_channels:
        if channel.name.lower() not in preferred_names:
            continue

        perms = channel.permissions_for(
            guild.me
        )

        if not (
            perms.send_messages
            and perms.embed_links
        ):
            continue

        try:
            await channel.send(
                embed=embed,
                view=view
            )

            print(
                f"[WELCOME] Sent welcome message in "
                f"#{channel.name} ({guild.id})"
            )

            return

        except discord.Forbidden:
            continue

        except discord.HTTPException:
            continue

    for channel in guild.text_channels:
        perms = channel.permissions_for(
            guild.me
        )

        if not (
            perms.send_messages
            and perms.embed_links
        ):
            continue

        try:
            await channel.send(
                embed=embed,
                view=view
            )

            print(
                f"[WELCOME] Sent welcome message in "
                f"#{channel.name} ({guild.id})"
            )

            return

        except discord.Forbidden:
            continue

        except discord.HTTPException:
            continue

    print(
        f"[WELCOME] Could not find a channel to send in "
        f"{guild.name} ({guild.id})"
    )

async def main():
    async with bot:
        await bot.start(TOKEN)

asyncio.run(main())