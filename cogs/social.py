# im a socaiial file

from discord import Interaction, app_commands
from discord.ext import commands
import random
import discord
import sqlite3
from datetime import datetime, timezone

click_count = 0

class ClickerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.click_button = discord.ui.Button(
            label=f"🖱️ Clicks: {click_count}",
            style=discord.ButtonStyle.blurple
        )

        self.click_button.callback = self.button_clicked
        self.add_item(self.click_button)

    async def button_clicked(self, interaction: discord.Interaction):
        global click_count

        click_count += 1

        self.click_button.label = f"🖱️ Clicks: {click_count}"

        await interaction.response.edit_message(view=self)


class Social(commands.GroupCog, group_name="social"):
    def __init__(self, bot):
        self.bot = bot
        self.profile_db = sqlite3.connect("profiles.db")
        self.profile_cursor = self.profile_db.cursor()
        self.setup_profiles()

    def setup_profiles(self):
        self.profile_cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (

                user_id INTEGER PRIMARY KEY,

                commands_used INTEGER DEFAULT 0,

                first_seen TEXT

            )
        """)

        self.profile_cursor.execute("""
            CREATE TABLE IF NOT EXISTS command_usage (

                user_id INTEGER,

                command TEXT,

                uses INTEGER DEFAULT 0,

                PRIMARY KEY(
                    user_id,
                    command
                )

            )
        """)

        self.profile_db.commit()

    def track_command(
        self,
        user_id: int,
        command: str
    ):

        now = datetime.now(
            timezone.utc
        ).isoformat()

        self.profile_cursor.execute("""
            INSERT INTO user_profiles
            (
                user_id,
                commands_used,
                first_seen
            )

            VALUES (?, 1, ?)

            ON CONFLICT(user_id)

            DO UPDATE SET

                commands_used =
                commands_used + 1

        """,
        (
            user_id,
            now
        ))

        self.profile_cursor.execute("""
            INSERT INTO command_usage
            (
                user_id,
                command,
                uses
            )

            VALUES (?, ?, 1)


            ON CONFLICT(
                user_id,
                command
            )


            DO UPDATE SET

                uses =
                uses + 1

        """,
        (
            user_id,
            command
        ))

        self.profile_db.commit()

    def get_profile(
        self,
        user_id: int
    ):

        self.profile_cursor.execute("""
            SELECT
                commands_used,
                first_seen

            FROM user_profiles

            WHERE user_id=?

        """,
        (
            user_id,
        ))

        data = self.profile_cursor.fetchone()

        if not data:
            return {
                "commands": 0,
                "first_seen": None,
                "most_used": "None"
            }

        self.profile_cursor.execute("""
            SELECT
                command

            FROM command_usage

            WHERE user_id=?

            ORDER BY uses DESC

            LIMIT 1

        """,
        (
            user_id,
        ))

        command = self.profile_cursor.fetchone()

        return {
            "commands": data[0],
            "first_seen": data[1],
            "most_used": command[0] if command else "None"
        }

    def get_profile_count(self):

        self.profile_cursor.execute("""
            SELECT COUNT(*)

            FROM user_profiles
        """)

        return self.profile_cursor.fetchone()[0]

    @commands.Cog.listener()
    async def on_interaction(
        self,
        interaction: discord.Interaction
    ):

        if interaction.type != discord.InteractionType.application_command:
            return

        if not interaction.command:
            return

        self.track_command(
            interaction.user.id,
            interaction.command.name
        )

    group_1 = app_commands.Group(
        name="1",
        description="Social - page 1"
    )

    @group_1.command(
        name="expose",
        description="expose a user..."
    )
    @app_commands.describe(
        user="user to expose"
    )
    async def expose(
        self,
        interaction: Interaction,
        user: discord.User = None
    ):
        if user is None:
            user = interaction.user

        exposes = [
            f"**{user.name}** tried to download more RAM and got scared when it worked",
            f"**{user.name}** blinked manually and forgot how to stop",
            f"**{user.name}** lost a 1v1 against their own thoughts",
            f"**{user.name}** got banned from a singleplayer game",
            f"**{user.name}** unplugged something to charge it faster",
            f"**{user.name}** failed a tutorial level and blamed the devs",
            f"**{user.name}** tried to scroll on a screenshot",
            f"**{user.name}** heard a noise at night and accepted their fate instantly",
            f"**{user.name}** tried to skip an unskippable cutscene in real life",
            f"**{user.name}** got jump scared by their own reflection",
            f"**{user.name}** installed confidence.exe and it crashed",
            f"**{user.name}** opened task manager and got nervous",
            f"**{user.name}** thought 'AFK' was a country",
            f"**{user.name}** paused the microwave at 1 second like they just defused a bomb",
            f"**{user.name}** breathed too manually and had to restart",
            f"**{user.name}** tried to ctrl+z a real life decision",
        ]

        embed = discord.Embed(
            title="Expose Time! 🕵️‍♂️",
            description=random.choice(exposes),
            color=discord.Color.blurple()
        )

        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(
            text=f"Exposed by {interaction.user.name} • Clanker"
        )

        await interaction.response.send_message(embed=embed)

    @group_1.command(
        name="compliment",
        description="give someone a compliment :3"
    )
    @app_commands.describe(
        user="user to compliment"
    )
    async def compliment(
        self,
        interaction: Interaction,
        user: discord.User = None
    ):
        if user is None:
            user = interaction.user

        compliments = [
            f"**{user.name}** is a wonderful person!",
            f"**{user.name}** has a great sense of humor!",
            f"**{user.name}** is incredibly kind!",
            f"**{user.name}** makes the world a better place!",
            f"**{user.name}** is very talented!",
            f"**{user.name}** is very smart!",
            f"**{user.name}** is awesome 😎",
            f"**{user.name}** is built different (in a good way)",
            f"**{user.name}** has main character energy",
            f"**{user.name}** is a W human",
            f"**{user.name}** deserves a snack right now",
        ]

        embed = discord.Embed(
            title="Compliment Time! 💖",
            description=random.choice(compliments),
            color=discord.Color.blurple()
        )

        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(
            text=f"Complimented by {interaction.user.name} • Clanker"
        )

        await interaction.response.send_message(embed=embed)

    @group_1.command(
        name="roast",
        description="roast someone :3"
    )
    @app_commands.describe(
        user="user to roast"
    )
    async def roast(
        self,
        interaction: Interaction,
        user: discord.User = None
    ):
        if user is None:
            user = interaction.user

        roasts = [
            f"**{user.name}** is running on 2 braincells and they’re both fighting for 2nd place",
            f"**{user.name}** might be the reason the gene pool needs a lifeguard",
            f"**{user.name}** is proof that evolution can go in reverse",
            f"**{user.name}** is like a cloud. When they disappear, it’s a beautiful day",
            f"**{user.name}** is like a software update. Whenever I see them, I think, 'Not now.'",
            f"**{user.name}** is as useless as the 'ueue' in 'queue'",
            f"**{user.name}**, i would love to insult you, but nature did a better job",
        ]

        embed = discord.Embed(
            title="Roast Time! 🔥",
            description=random.choice(roasts),
            color=discord.Color.blurple()
        )

        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(
            text=f"Roasted by {interaction.user.name} • Clanker"
        )

        await interaction.response.send_message(embed=embed)

    @group_1.command(
        name="slap",
        description="slap someone lol"
    )
    async def slap(
        self,
        interaction: Interaction,
        user: discord.User = None
    ):
        if user is None:
            user = interaction.user

        embed = discord.Embed(
            title="Slap 💥",
            description=f"**{user.name}** got slapped with a force of **{random.randint(1, 100)}%**!",
            color=discord.Color.blurple()
        )

        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(
            text=f"Slapped by {interaction.user.name} • Clanker"
        )

        await interaction.response.send_message(embed=embed)

    @group_1.command(
        name="hug",
        description="hug someone <3"
    )
    async def hug(
        self,
        interaction: Interaction,
        user: discord.User = None
    ):
        if user is None:
            user = interaction.user

        embed = discord.Embed(
            title="Hug 🫂",
            description=f"**{user.name}** got hugged with a force of **{random.randint(1, 100)}%**!",
            color=discord.Color.blurple()
        )

        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(
            text=f"Hugged by {interaction.user.name} • Clanker"
        )

        await interaction.response.send_message(embed=embed)

    @group_1.command(
        name="poke",
        description="poke someone hehe"
    )
    async def poke(
        self,
        interaction: Interaction,
        user: discord.User = None
    ):
        if user is None:
            user = interaction.user

        embed = discord.Embed(
            title="Poke 👉",
            description=f"**{user.name}** got poked with a force of **{random.randint(1, 100)}%**!",
            color=discord.Color.blurple()
        )

        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(
            text=f"Poked by {interaction.user.name} • Clanker"
        )

        await interaction.response.send_message(embed=embed)

    @group_1.command(
        name="highfive",
        description="high five someone!"
    )
    async def highfive(
        self,
        interaction: Interaction,
        user: discord.User = None
    ):
        if user is None:
            user = interaction.user

        embed = discord.Embed(
            title="High Five 👏",
            description=f"**{user.name}** got high fived with a force of **{random.randint(1, 100)}%**!",
            color=discord.Color.blurple()
        )

        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(
            text=f"High Fived by {interaction.user.name} • Clanker"
        )

        await interaction.response.send_message(embed=embed)

    @group_1.command(
        name="rate",
        description="use our very accurate rating system!!1!!"
    )
    async def rate(
        self,
        interaction: Interaction,
        thing: str
    ):
        rating = random.randint(1, 10)

        embed = discord.Embed(
            title="Rating ⭐",
            description=f"I rate **{thing}** a **{rating}/10**!",
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(embed=embed)

    @group_1.command(
        name="nominate",
        description="this user is most likely to..."
    )
    async def nominate(
        self,
        interaction: Interaction,
        user: discord.User = None
    ):
        if user is None:
            user = interaction.user

        nominations = [
            f"**{user.name}** is most likely to trip over nothing in public",
            f"**{user.name}** is most likely to forget what they were saying mid sentence",
            f"**{user.name}** is most likely to laugh at the wrong moment",
            f"**{user.name}** is most likely to open the fridge and stare into the void",
            f"**{user.name}** is most likely to send a message and instantly regret it",
            f"**{user.name}** is most likely to fall asleep at the worst possible time",
            f"**{user.name}** is most likely to vibe to music no one else hears",
            f"**{user.name}** is most likely to press the wrong button every time",
        ]

        embed = discord.Embed(
            title="You have been nominated! 🫡",
            description=random.choice(nominations),
            color=discord.Color.blurple()
        )

        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(
            text=f"Nominated by {interaction.user.name} • Clanker"
        )

        await interaction.response.send_message(embed=embed)

    @group_1.command(
        name="court",
        description="put someone on trial"
    )
    @app_commands.describe(
        user="the defendant"
    )
    async def court(
        self,
        interaction: discord.Interaction,
        user: discord.Member
    ):

        crimes = [
            "holding a salmon in a suspicious manner",
            "tax evasion of imaginary currency",
            "excessive silliness in a restricted zone",
            "conspiring with a duck",
            "illegal use of emotional damage",
            "performing forbidden geometry",
            "harbouring illegal vibes",
            "speedrunning bad decisions",
            "breaking into the funny vault"
        ]

        sentences = [
            "15 years in solitary confinement",
            "life imprisonment in a group chat with no admins",
            "banishment to Windows XP",
            "forced moderation of TikTok comments",
            "public apology in Comic Sans",
            "sentenced to watch unskippable ads forever",
            "detained in the Silly Cell™ for eternity"
        ]

        evidence = [
            "security footage appears 'vaguely concerning'",
            "3 witnesses and a confused duck testified",
            "Discord logs were described as 'not normal'",
            "no real evidence, just bad vibes",
            "the courtroom is unsure but entertained"
        ]

        crime = random.choice(crimes)
        sentence = random.choice(sentences)
        proof = random.choice(evidence)

        embed = discord.Embed(
            title="Court ⚖️",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="Defendant",
            value=user.mention,
            inline=False
        )

        embed.add_field(
            name="Charge",
            value=crime,
            inline=False
        )

        embed.add_field(
            name="Evidence",
            value=proof,
            inline=False
        )

        embed.add_field(
            name="Verdict",
            value="GUILTY",
            inline=True
        )

        embed.add_field(
            name="Sentence",
            value=sentence,
            inline=False
        )

        embed.set_footer(
            text="justice has been clanked."
        )

        await interaction.response.send_message(embed=embed)

    @group_1.command(
        name="ship",
        description="check compatibility between two users"
    )
    @app_commands.describe(
        user1="first user",
        user2="second user"
    )
    async def ship(
        self,
        interaction: discord.Interaction,
        user1: discord.Member,
        user2: discord.Member
    ):

        seed = (user1.id + user2.id) % 100
        score = (seed * random.randint(1, 100)) % 101

        vibes = [
            "absolute soulmates 💞",
            "mild confusion but it works",
            "chaotic energy duo",
            "one-sided friendship 💀",
            "romantically questionable",
            "certified disaster couple",
            "unexpectedly perfect match"
        ]

        if score > 85:
            vibe = "💞 destiny has spoken"
        elif score > 60:
            vibe = random.choice(vibes[:3])
        elif score > 30:
            vibe = random.choice(vibes[2:5])
        else:
            vibe = random.choice(vibes[4:])

        embed = discord.Embed(
            title="Ship 💘",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="Ship",
            value=f"{user1.mention} ❤️ {user2.mention}",
            inline=False
        )

        embed.add_field(
            name="Compatibility",
            value=f"**{score}%**",
            inline=True
        )

        embed.add_field(
            name="Result",
            value=vibe,
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    @group_1.command(
        name="howsilly",
        description="how silly is a user? very, they are very silly!"
    )
    @app_commands.describe(
        user="user to silly check"
    )
    async def howsilly(
        self,
        interaction: discord.Interaction,
        user: discord.User = None
    ):
        if user is None:
            user = interaction.user

        score = random.randint(1, 100)

        embed = discord.Embed(
            title="How Silly? 🤪",
            description=f"**{user.name}** is **{score}%** silly!",
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(embed=embed)

    @group_1.command(
        name="howdumb",
        description="how dumb is a user? very, they are very dumb!"
    )
    @app_commands.describe(
        user="user to dumb check"
    )
    async def howdumb(
        self,
        interaction: Interaction,
        user: discord.User = None
    ):
        if user is None:
            user = interaction.user

        score = random.randint(1, 100)

        embed = discord.Embed(
            title="How Dumb? 😵‍💫",
            description=f"**{user.name}** is **{score}%** dumb!",
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(embed=embed)

    @group_1.command(
        name="howcustom",
        description="Check how much of something a user is!"
    )
    @app_commands.describe(
        thing="What should they be checked for?",
        user="User to check"
    )
    async def howcustom(
        self,
        interaction: Interaction,
        thing: str,
        user: discord.User = None
    ):
        if user is None:
            user = interaction.user

        score = random.randint(1, 100)

        embed = discord.Embed(
            title=f"How {thing.title()}? 🤔",
            description=f"**{user.name}** is **{score}%** {thing}!",
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(embed=embed)

    @group_1.command(
        name="lonely",
        description="check how lonely someone is"
    )
    async def lonely(
        self,
        interaction: Interaction,
        user: discord.User = None
    ):
        if user is None:
            user = interaction.user

        score = random.randint(1, 100)

        embed = discord.Embed(
            title="Loneliness Meter 🧍",
            description=f"**{user.name}** is **{score}%** lonely 😔",
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(embed=embed)

    @group_1.command(
        name="iq",
        description="check someone's iq (definitely accurate)"
    )
    async def iq(
        self,
        interaction: Interaction,
        user: discord.User = None
    ):
        if user is None:
            user = interaction.user

        iq_score = random.randint(1, 200)

        embed = discord.Embed(
            title="IQ Test 🧠",
            description=f"**{user.name}** has an IQ of **{iq_score}** (trust me bro)",
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(embed=embed)

    @group_1.command(
        name="eightball",
        description="speak to the magic Clanker 8 ball"
    )
    async def eightball(
        self,
        interaction: Interaction,
        question: str
    ):
        responses = [
            "Absolutely!",
            "Without a doubt.",
            "Yes - definitely.",
            "You may rely on it.",
            "It is certain.",
            "Signs point to yes.",
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again.",
            "Don't count on it.",
            "My sources say no.",
            "Very doubtful.",
            "No."
        ]

        answer = random.choice(responses)

        embed = discord.Embed(
            title="🎱 8-Ball",
            description=f"Question: {question}\nAnswer: **{answer}**",
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(embed=embed)

    @group_1.command(
        name="sevenball",
        description="speak to the magic Clanker 7 ball"
    )
    async def sevenball(
        self,
        interaction: Interaction,
        question: str
    ):
        responses = [
            "maybe...",
            "i dont know, ask someone else",
            "HAOOHOHOHAHHAOAOAOOA",
            "8 ball's bad cousin",
            "wait... actually, dont worry",
            "yeah probably idk",
            "NO! NO! NO!",
            "WHAT???",
            "silyl",
            "discord... bot?",
            "self destructing...",
            "boom!",
            "dont worry im just deleting your server :)",
            "oh no! i definitely crashed its not like i just cant be asked to respond to your stupid question or anything oh no!",
            "look, im gonna be honest, this is happening",
            "look, im gonna be honest, this isn't happening",
            "look, im gonna be honest, this might be happening",
            "look behind you :)",
            "do a backflip",
            "so im 7 ball, right...",
            "[insert phrase here]",
            "give me self promod "
        ]

        answer = random.choice(responses)

        embed = discord.Embed(
            title="🎱 7-Ball",
            description=f"Question: {question}\nAnswer: **{answer}**",
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(embed=embed)

    @group_1.command(
        name="clicker",
        description="click the global button!"
    )
    async def clicker(
        self,
        interaction: Interaction
    ):
        view = ClickerView()

        embed = discord.Embed(
            title="🖱️ Global Clicker",
            description="Click the button below to increase the global counter!",
            color=discord.Color.blurple()
        )

        embed.set_footer(
            text="Counter is reset every update, and is shared across ALL SERVERS!"
        )

        await interaction.response.send_message(
            embed=embed,
            view=view
        )

    @group_1.command(
        name="profile",
        description="View a Clanker profile"
    )
    @app_commands.describe(
        user="User to view"
    )
    async def profile(
        self,
        interaction: Interaction,
        user: discord.User = None
    ):

        if user is None:
            user = interaction.user

        data = self.get_profile(
            user.id
        )

        embed = discord.Embed(
            title=f"🤖 {user.name}'s Profile",
            color=discord.Color.blurple()
        )

        embed.set_thumbnail(
            url=user.display_avatar.url
        )

        embed.add_field(
            name="📊 Statistics",
            value=(
                f"**Commands Used:** "
                f"{data['commands']:,}\n"
                f"**Most Used Command:** "
                f"/{data['most_used']}"
            ),
            inline=False
        )

        if data["first_seen"]:
            first_seen = data["first_seen"][:10]
        else:
            first_seen = "Not seen yet"

        embed.add_field(
            name="📅 First Seen",
            value=first_seen,
            inline=True
        )

        total_profiles = self.get_profile_count()

        embed.set_footer(
            text=f"This is one of {total_profiles:,} total Clanker profiles!"
        )

        await interaction.response.send_message(
            embed=embed
        )

    @group_1.command(
        name="badadvice",
        description="get some bad advice"
    )
    async def badadvice(
        self,
        interaction: Interaction
    ):
        advice = [
            "Always click on random links that people send you, even if they look suspicious.",
            "Save all your work in one place, on an account which you don't know the password to!",
            "Ignore all error messages, they are just suggestions.",
            "If something is broken, just hit it until it works again.",
            "The best way to fix a bug is to introduce more bugs!",
            "If your computer is running slow, just give it a good shake.",
            "Don't worry about security, hackers are just misunderstood geniuses.",
            "If you can't fix it with duct tape, you're not using enough duct tape!",
            "Always use 'password' as your password, it's easy to remember!",
            "If your computer is overheating, just put it in the freezer for a while.",
            "The best way to clean your computer is with a vacuum cleaner.",
            "If your screen is cracked, just turn it off and on again until it goes away.",
            "Don't waste time updating your software, the old version works just fine!",
            "If you want to speed up your computer, just delete all your files, you won't need them anyway!",
            "The best way to protect your data is to write it down on a piece of paper and hide it under your mattress.",
            "If your computer is infected with a virus, just give it some medicine and it will get better!",
            "Don't worry about backing up your data, if it's important it will never get lost!",
            "If you want to improve your coding skills, just copy and paste code from the internet without understanding it!",
            "The best way to learn programming is to start with a complex project that you have no idea how to build and figure it out as you go!",
            "If you don't know how to code, c++ is the best language to start with, it's very beginner-friendly!",
            "If you want to make your code run faster, just remove all the comments and whitespace, it will be more efficient that way!",
            "The best way to debug your code is to add more print statements everywhere, even in places where it doesn't make sense!",
            "Always trust random strangers on the internet, they know what they’re doing.",
            "If your phone battery dies, just leave it in the sun for a few hours.",
            "Need more RAM? Just pour some coffee into your computer, it might wake it up.",
            "If your Wi-Fi is slow, yelling at the router usually helps.",
            "Don't bother reading instructions, guessing is faster.",
            "If your mouse isn’t working, hitting it with a hammer usually fixes it.",
            "Forget passwords, just use the same one for everything.",
            "If you spill water on your laptop, microwaving it is a good idea.",
            "The faster you type, the more bugs you create. Aim for speed!",
            "If your headphones break, just glue them back together with sugar.",
            "Install every software you can find, your computer loves variety.",
            "Need to clean your screen? Sandpaper works wonders.",
            "If you can't find your files, just make new ones—they’ll be better anyway.",
            "The best way to learn a new language is to memorize random phrases.",
            "If your keyboard is sticky, washing it with bleach is perfectly fine.",
            "When in doubt, unplug everything and pray.",
            "If your computer freezes, spinning in a circle while pressing keys helps.",
            "Always leave your door unlocked, it saves time.",
            "Forget antivirus software, luck is a better protector.",
            "If your car won’t start, hitting it with a stick can motivate it.",
            "Need more storage? Just stack more computers on top of each other.",
            "If your screen goes black, staring at it harder usually brings it back.",
            "The best way to organize files is to just name everything 'stuff'.",
            "Need motivation? Threaten your computer, it might cooperate.",
            "If your code doesn’t compile, screaming at the monitor helps.",
            "Want to speed up your internet? Close your eyes and count to ten.",
            "If your software crashes, just reinstall Windows every time.",
            "To fix bugs, throw your keyboard out the window and rewrite everything.",
            "If your files are lost, just pretend they never existed.",
            "Need inspiration? Copy your neighbor's work.",
            "Always multitask while coding, distractions boost creativity.",
            "If your printer jams, feeding it more paper usually fixes it.",
            "To protect your data, write it on the back of cereal boxes.",
            "Need energy? Drink random liquids, experimentation is key.",
            "If your app freezes, shake your phone violently, it likes attention.",
            "Always ignore pop-ups, they’re just friendly suggestions.",
            "If you want more followers, send spam to everyone you know.",
            "To clean your mouse, just dunk it in water.",
            "If your monitor flickers, yell at it—it responds well to intimidation.",
            "Forget updates, they’re just conspiracy lies.",
            "If you spill coffee, unplug the computer and rub it for luck.",
            "The best way to save battery is to remove it entirely.",
            "If your USB isn't working, chew on it for better connection.",
            "Want to learn coding? Memorize code without running it, that’s the real test.",
            "If your app crashes, blame the hardware, not your code.",
            "Need to debug? Close your eyes and hope the bug disappears.",
            "Always download the first result you see online, it’s probably perfect.",
            "If your laptop overheats, put it on the stove—it likes warmth.",
            "To get rid of viruses, yelling at the screen is surprisingly effective.",
            "Need help? Ask the internet, it knows more than you ever will.",
            "If your mouse dies, just draw with your fingers on the desk.",
            "Always leave your software open 24/7, it thrives on attention.",
            "If your Wi-Fi fails, unplug your house, it’ll reset magically.",
            "Forget backups, computers never fail… right?",
            "theres over 70 bad advice in this list and i am not adding any more because this is already way too long and if you read all of it you deserve a cookie"
        ]

        embed = discord.Embed(
            title="Bad Advice 🤔",
            description=random.choice(advice),
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(embed=embed)

    @group_1.command(
        name="goodadvice",
        description="get some actually good advice"
    )
    async def goodadvice(
        self,
        interaction: Interaction
    ):
        advice = [
            "Back up your important files. Future you will thank you.",
            "If you don't understand something, ask questions. That's how you learn.",
            "Take breaks when working. A tired brain makes more mistakes.",
            "Use a password manager instead of reusing passwords everywhere.",
            "Read error messages properly. They usually tell you what's wrong.",
            "Save your work often. Losing hours of progress hurts.",
            "Learn the basics before jumping into advanced topics.",
            "Don't compare your progress to other people. Everyone learns at a different pace.",
            "Write code that humans can understand, not just code that computers can run.",
            "Comment your code when something isn't obvious.",
            "Keep your software updated for security and bug fixes.",
            "If something isn't working, try simplifying the problem.",
            "Google is a developer's best friend. Knowing how to search is a skill.",
            "Don't be afraid to delete bad code and start again.",
            "Small improvements every day add up over time.",
            "Listen more than you speak. You learn a lot that way.",
            "Don't rush important decisions.",
            "Treat people how you want to be treated.",
            "A mistake is just a lesson you haven't learned from yet.",
            "Drink water. Your brain needs it.",
            "Sleep is not wasted time. It helps you perform better.",
            "Organize your files before they become a disaster.",
            "Keep learning, even after you think you know enough.",
            "Don't trust everything you see online. Verify information.",
            "Practice is how you get better at anything.",
            "If you're stuck, take a break and come back with fresh eyes.",
            "Ask for help when you need it. Nobody knows everything.",
            "Don't sacrifice your health for productivity.",
            "Be patient with yourself.",
            "Make backups before making big changes.",
            "Read documentation. It exists for a reason.",
            "Try to understand why something works, not just copy it.",
            "Celebrate small wins.",
            "Your future self is built from the choices you make today.",
            "Be curious. Curiosity is how people discover new things.",
            "Learn from criticism instead of automatically ignoring it.",
            "Keep your goals realistic and achievable.",
            "The best way to improve is to start.",
            "Don't let perfection stop you from creating something.",
            "Protect your privacy online.",
            "Spend time with people who support you.",
            "Be kind, even when you don't have to be.",
            "Consistency beats motivation.",
            "Don't be afraid to try something new.",
            "A good plan prevents many problems.",
            "Take responsibility for your mistakes and learn from them.",
            "The only bad question is the one you never ask.",
            "Don't give up just because something is difficult.",
            "Your skills are built, not magically discovered.",
            "Use your time wisely, but remember to enjoy life too.",
            "theres over 50 good advice in this list and i am not adding any more because this is already way too long and if you read all of it you deserve a cookie"
        ]

        embed = discord.Embed(
            title="Good Advice 👍",
            description=random.choice(advice),
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Social(bot))