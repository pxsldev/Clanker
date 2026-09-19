from discord import app_commands, Interaction
from discord.ext import commands
import discord
import aiohttp
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageFont, ImageDraw
from pilmoji import Pilmoji
import io
import textwrap
import os
import tempfile
import shutil
import random

class Images(commands.GroupCog, group_name="image"):
    image_1 = app_commands.Group(
        name="1",
        description="Image - page 1"
    )

    MAX_DOWNLOAD_SIZE = 50 * 1024 * 1024
    MAX_IMAGE_PIXELS = 12_000_000
    MAX_IMAGE_SIDE = 3000

    def __init__(self, bot):
        self.bot = bot

    async def interaction_check(
        self,
        interaction: discord.Interaction
    ) -> bool:
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
            await interaction.guild.fetch_member(
                self.bot.user.id
            )
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

    async def send_error(
        self,
        interaction: Interaction,
        title: str,
        desc: str
    ):
        embed = discord.Embed(
            title=title,
            description=desc,
            color=discord.Color.red()
        )

        if interaction.response.is_done():
            await interaction.followup.send(
                embed=embed
            )
        else:
            await interaction.response.send_message(
                embed=embed
            )

    async def get_media_url(
        self,
        interaction: Interaction,
        media: discord.Attachment = None,
        url: str = None
    ):
        media_url = None

        if media:
            media_url = media.url

        elif url:
            media_url = url

        elif interaction.message and interaction.message.reference:
            try:
                replied = await interaction.channel.fetch_message(
                    interaction.message.reference.message_id
                )

                if replied.attachments:
                    media_url = replied.attachments[0].url
            except:
                pass

        if not media_url:
            async for message in interaction.channel.history(
                limit=20
            ):
                if message.attachments:
                    media_url = message.attachments[0].url
                    break

        return media_url

    async def download_media(
        self,
        media_url: str,
        output_path: str
    ):
        try:
            timeout = aiohttp.ClientTimeout(
                total=60
            )

            async with aiohttp.ClientSession(
                timeout=timeout
            ) as session:
                async with session.get(
                    media_url,
                    allow_redirects=True
                ) as response:
                    if response.status != 200:
                        return False, "Failed to download the media."

                    content_length = response.headers.get(
                        "Content-Length"
                    )

                    if content_length:
                        try:
                            if int(content_length) > self.MAX_DOWNLOAD_SIZE:
                                return False, (
                                    "That file is too large.\n\n"
                                    "The maximum allowed file size is **50 MB**."
                                )
                        except:
                            pass

                    total = 0

                    with open(
                        output_path,
                        "wb"
                    ) as file:
                        async for chunk in response.content.iter_chunked(
                            1024 * 256
                        ):
                            total += len(chunk)

                            if total > self.MAX_DOWNLOAD_SIZE:
                                file.close()

                                try:
                                    os.remove(output_path)
                                except:
                                    pass

                                return False, (
                                    "That file is too large.\n\n"
                                    "The maximum allowed file size is **50 MB**."
                                )

                            file.write(chunk)

            return True, None

        except aiohttp.ClientError:
            return False, "Failed to download the media."

        except Exception:
            return False, "Failed to download the media."

    async def load_image(
        self,
        interaction: Interaction,
        media: discord.Attachment = None,
        url: str = None
    ):
        media_url = await self.get_media_url(
            interaction,
            media,
            url
        )

        if not media_url:
            return (
                None,
                "Missing Image ⚠️",
                "Upload, reply, or provide a URL."
            )

        temp_dir = tempfile.mkdtemp()

        try:
            input_path = os.path.join(
                temp_dir,
                "input"
            )

            success, error = await self.download_media(
                media_url,
                input_path
            )

            if not success:
                return (
                    None,
                    "Error 🚫",
                    error
                )

            try:
                img = Image.open(
                    input_path
                )

                img.load()

                if (
                    img.width * img.height
                    > self.MAX_IMAGE_PIXELS
                ):
                    return (
                        None,
                        "Image Too Large 🚫",
                        "That image has too many pixels."
                    )

                if (
                    img.width > self.MAX_IMAGE_SIDE
                    or img.height > self.MAX_IMAGE_SIDE
                ):
                    img.thumbnail(
                        (
                            self.MAX_IMAGE_SIDE,
                            self.MAX_IMAGE_SIDE
                        ),
                        Image.Resampling.LANCZOS
                    )

                result = img.copy()

                img.close()

                return result, None, None

            except Exception as e:
                print(e)
                return (
                    None,
                    "Invalid Image 🚫",
                    "I couldn't open that file as an image."
                )

        finally:
            shutil.rmtree(
                temp_dir,
                ignore_errors=True
            )

    async def send_image(
        self,
        interaction: Interaction,
        img: Image.Image,
        title: str,
        filename: str,
        desc: str = None
    ):
        buffer = io.BytesIO()

        img.save(
            buffer,
            format="PNG"
        )

        buffer.seek(0)

        file = discord.File(
            buffer,
            filename=filename
        )

        embed = discord.Embed(
            title=title,
            description=desc if desc else "",
            color=discord.Color.blurple()
        )

        embed.set_image(
            url=f"attachment://{filename}"
        )

        if interaction.response.is_done():
            await interaction.followup.send(
                embed=embed,
                file=file
            )
        else:
            await interaction.response.send_message(
                embed=embed,
                file=file
            )

    @image_1.command(
        name="invert",
        description="Invert an image"
    )
    async def invert(
        self,
        interaction: Interaction,
        media: discord.Attachment = None,
        url: str = None
    ):
        img, err_title, err_desc = await self.load_image(
            interaction,
            media,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        img = ImageOps.invert(
            img.convert("RGB")
        )

        await self.send_image(
            interaction,
            img,
            "Inverted Image 🌀",
            "invert.png"
        )

        img.close()

    @image_1.command(
        name="greyscale",
        description="Convert an image to greyscale"
    )
    async def greyscale(
        self,
        interaction: Interaction,
        media: discord.Attachment = None,
        url: str = None
    ):
        img, err_title, err_desc = await self.load_image(
            interaction,
            media,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        result = ImageOps.grayscale(
            img
        ).convert("RGB")

        await self.send_image(
            interaction,
            result,
            "Greyscale Image ⚪",
            "greyscale.png"
        )

        img.close()
        result.close()

    @image_1.command(
        name="deepfry",
        description="Deep fry an image"
    )
    async def deepfry(
        self,
        interaction: Interaction,
        media: discord.Attachment = None,
        url: str = None
    ):
        img, err_title, err_desc = await self.load_image(
            interaction,
            media,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        result = img.convert("RGB")

        result = ImageEnhance.Contrast(
            result
        ).enhance(2.0)

        result = ImageEnhance.Color(
            result
        ).enhance(3.0)

        result = result.filter(
            ImageFilter.UnsharpMask(
                radius=2,
                percent=150
            )
        )

        await self.send_image(
            interaction,
            result,
            "Deepfried Image 💥",
            "deepfry.png"
        )

        img.close()
        result.close()

    @image_1.command(
        name="blur",
        description="Blur an image"
    )
    async def blur(
        self,
        interaction: Interaction,
        amount: int = 5,
        media: discord.Attachment = None,
        url: str = None
    ):
        amount = max(
            0,
            min(amount, 25)
        )

        img, err_title, err_desc = await self.load_image(
            interaction,
            media,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        result = img.filter(
            ImageFilter.GaussianBlur(
                radius=amount
            )
        ).convert("RGB")

        await self.send_image(
            interaction,
            result,
            f"Blurred Image (Amount: {amount}) 💨",
            "blur.png"
        )

        img.close()
        result.close()

    @image_1.command(
        name="bloom",
        description="Add bloom effect to an image"
    )
    async def bloom(
        self,
        interaction: Interaction,
        amount: float = 1.5,
        media: discord.Attachment = None,
        url: str = None
    ):
        amount = max(
            0.1,
            min(amount, 3.0)
        )

        img, err_title, err_desc = await self.load_image(
            interaction,
            media,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        result = ImageEnhance.Brightness(
            img
        ).enhance(amount)

        result = result.filter(
            ImageFilter.GaussianBlur(
                radius=5
            )
        ).convert("RGB")

        await self.send_image(
            interaction,
            result,
            f"Bloom Image (Amount: {amount}) ✨",
            "bloom.png"
        )

        img.close()
        result.close()

    @image_1.command(
        name="pixelate",
        description="Pixelate an image"
    )
    async def pixelate(
        self,
        interaction: Interaction,
        amount: int = 10,
        media: discord.Attachment = None,
        url: str = None
    ):
        amount = max(
            2,
            min(amount, 50)
        )

        img, err_title, err_desc = await self.load_image(
            interaction,
            media,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        width = max(
            1,
            img.width // amount
        )

        height = max(
            1,
            img.height // amount
        )

        small = img.resize(
            (width, height),
            Image.Resampling.NEAREST
        )

        result = small.resize(
            img.size,
            Image.Resampling.NEAREST
        ).convert("RGB")

        await self.send_image(
            interaction,
            result,
            f"Pixelated Image (Amount: {amount}) 🟫",
            "pixelate.png"
        )

        img.close()
        small.close()
        result.close()

    @image_1.command(
        name="gif",
        description="Turn an image into a GIF"
    )
    async def gif(
        self,
        interaction: Interaction,
        media: discord.Attachment = None,
        url: str = None
    ):
        img, err_title, err_desc = await self.load_image(
            interaction,
            media,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        buffer = io.BytesIO()

        img.convert(
            "RGBA"
        ).save(
            buffer,
            format="GIF",
            save_all=True,
            loop=0
        )

        buffer.seek(0)

        file = discord.File(
            buffer,
            filename="image.gif"
        )

        embed = discord.Embed(
            title="Image → GIF 🖼️",
            description=(
                "GIFs are limited to 256 colors - quality may drop ⚠️"
            ),
            color=discord.Color.blurple()
        )

        embed.set_image(
            url="attachment://image.gif"
        )

        await interaction.response.send_message(
            embed=embed,
            file=file
        )

        img.close()

    @image_1.command(
        name="png",
        description="Turn an image into a PNG"
    )
    async def png(
        self,
        interaction: Interaction,
        media: discord.Attachment = None,
        url: str = None
    ):
        img, err_title, err_desc = await self.load_image(
            interaction,
            media,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        result = img.convert("RGBA")

        await self.send_image(
            interaction,
            result,
            "Image → PNG 🖼️",
            "image.png",
            "Converted successfully."
        )

        img.close()
        result.close()

    @image_1.command(
        name="jpg",
        description="Turn an image into a JPG"
    )
    async def jpg(
        self,
        interaction: Interaction,
        media: discord.Attachment = None,
        url: str = None
    ):
        img, err_title, err_desc = await self.load_image(
            interaction,
            media,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        if (
            img.mode in ("RGBA", "LA")
            or (
                img.mode == "P"
                and "transparency" in img.info
            )
        ):
            background = Image.new(
                "RGB",
                img.size,
                (255, 255, 255)
            )

            rgba = img.convert(
                "RGBA"
            )

            background.paste(
                rgba,
                mask=rgba.getchannel("A")
            )

            result = background

            rgba.close()

        else:
            result = img.convert(
                "RGB"
            )

        buffer = io.BytesIO()

        result.save(
            buffer,
            format="JPEG",
            quality=95
        )

        buffer.seek(0)

        file = discord.File(
            buffer,
            filename="image.jpg"
        )

        embed = discord.Embed(
            title="Image → JPG 🖼️",
            description=(
                "Transparency has been replaced with a white background."
            ),
            color=discord.Color.blurple()
        )

        embed.set_image(
            url="attachment://image.jpg"
        )

        await interaction.response.send_message(
            embed=embed,
            file=file
        )

        img.close()
        result.close()

    @image_1.command(
        name="webp",
        description="Turn an image into a WebP"
    )
    async def webp(
        self,
        interaction: Interaction,
        media: discord.Attachment = None,
        url: str = None
    ):
        img, err_title, err_desc = await self.load_image(
            interaction,
            media,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        result = img.convert(
            "RGBA"
        )

        buffer = io.BytesIO()

        result.save(
            buffer,
            format="WEBP",
            quality=95
        )

        buffer.seek(0)

        file = discord.File(
            buffer,
            filename="image.webp"
        )

        embed = discord.Embed(
            title="Image → WebP 🖼️",
            description="Converted successfully.",
            color=discord.Color.blurple()
        )

        embed.set_image(
            url="attachment://image.webp"
        )

        await interaction.response.send_message(
            embed=embed,
            file=file
        )

        img.close()
        result.close()

    @image_1.command(
        name="caption",
        description="Add a caption to an image or GIF"
    )
    async def caption(
        self,
        interaction: Interaction,
        media: discord.Attachment = None,
        text: str = None,
        url: str = None
    ):
        if not text:
            return await self.send_error(
                interaction,
                "Missing Text ⚠️",
                "Please provide a caption."
            )

        await interaction.response.defer()

        img, err_title, err_desc = await self.load_image(
            interaction,
            media,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        is_gif = getattr(
            img,
            "format",
            None
        ) == "GIF"

        if is_gif:
            frame_count = min(
                getattr(
                    img,
                    "n_frames",
                    1
                ),
                40
            )

            frames = []

            for frame_number in range(
                frame_count
            ):
                img.seek(
                    frame_number
                )

                frames.append(
                    img.convert(
                        "RGBA"
                    ).copy()
                )

            duration = img.info.get(
                "duration",
                100
            )

            loop = img.info.get(
                "loop",
                0
            )

        else:
            frames = [
                img.convert(
                    "RGBA"
                )
            ]

            duration = None
            loop = 0

        processed_frames = []

        try:
            for frame in frames:
                width, height = frame.size

                font_size = max(
                    24,
                    min(
                        64,
                        width // 10
                    )
                )

                font = ImageFont.truetype(
                    "C:/Windows/Fonts/impact.ttf",
                    font_size
                )

                chars_per_line = max(
                    8,
                    width // max(
                        1,
                        font_size // 2
                    )
                )

                wrapped = textwrap.fill(
                    text,
                    width=chars_per_line
                )

                draw = ImageDraw.Draw(
                    frame
                )

                bbox = draw.multiline_textbbox(
                    (0, 0),
                    wrapped,
                    font=font,
                    align="center"
                )

                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                padding = font_size // 2

                caption_height = (
                    text_height +
                    padding * 2
                )

                output = Image.new(
                    "RGBA",
                    (
                        width,
                        height + caption_height
                    ),
                    "white"
                )

                output.paste(
                    frame,
                    (0, caption_height)
                )

                x = (
                    width -
                    text_width
                ) / 2

                y = (
                    (caption_height - text_height) / 2
                ) - bbox[1]

                with Pilmoji(output) as pilmoji:
                    pilmoji.text(
                        (x, y),
                        wrapped,
                        fill="black",
                        font=font,
                        align="center"
                    )

                processed_frames.append(
                    output
                )

            buffer = io.BytesIO()

            if is_gif:
                processed_frames[0].save(
                    buffer,
                    format="GIF",
                    save_all=True,
                    append_images=processed_frames[1:],
                    duration=duration,
                    loop=loop,
                    disposal=2
                )

                filename = "caption.gif"

            else:
                processed_frames[0].save(
                    buffer,
                    format="PNG"
                )

                filename = "caption.png"

            buffer.seek(0)

            file = discord.File(
                buffer,
                filename=filename
            )

            embed = discord.Embed(
                title="Caption 📝",
                color=discord.Color.blurple()
            )

            embed.set_image(
                url=f"attachment://{filename}"
            )

            await interaction.followup.send(
                embed=embed,
                file=file
            )

        finally:
            for frame in frames:
                frame.close()

            for frame in processed_frames:
                frame.close()

            img.close()

    @image_1.command(
        name="quote",
        description="Create a dramatic quote"
    )
    async def quote(
        self,
        interaction: discord.Interaction,
        user: discord.Member = None,
        text: str = None
    ):
        await interaction.response.defer()

        author = interaction.user

        if user and not text:
            found = False

            async for message in interaction.channel.history(
                limit=100
            ):
                if (
                    message.author.id == user.id
                    and message.content
                ):
                    text = message.content
                    author = user
                    found = True
                    break

            if not found:
                return await interaction.followup.send(
                    embed=discord.Embed(
                        title="Error ❌",
                        description=(
                            "Couldn't find a recent message from that user."
                        ),
                        color=discord.Color.red()
                    )
                )

        if not text:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Error ❌",
                    description="Provide text or a user to quote.",
                    color=discord.Color.red()
                )
            )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    author.display_avatar.url
                ) as response:
                    avatar_bytes = await response.read()

            avatar = Image.open(
                io.BytesIO(avatar_bytes)
            ).convert("RGBA")

            width = 1400
            height = 700

            img = Image.new(
                "RGBA",
                (width, height),
                (12, 12, 18, 255)
            )

            draw = ImageDraw.Draw(
                img
            )

            glow = Image.new(
                "RGBA",
                (width, height),
                (0, 0, 0, 0)
            )

            glow_draw = ImageDraw.Draw(
                glow
            )

            glow_draw.ellipse(
                (1050, 260, 1320, 530),
                fill=(120, 80, 255, 120)
            )

            glow = glow.filter(
                ImageFilter.GaussianBlur(
                    60
                )
            )

            img.alpha_composite(
                glow
            )

            name_font = ImageFont.truetype(
                "C:/Windows/Fonts/arial.ttf",
                38
            )

            small_font = ImageFont.truetype(
                "C:/Windows/Fonts/arial.ttf",
                25
            )

            draw.text(
                (70, 20),
                "“",
                font=ImageFont.truetype(
                    "C:/Windows/Fonts/georgia.ttf",
                    220
                ),
                fill=(255, 255, 255, 35)
            )

            max_text_width = 750
            font_size = 65

            while True:
                quote_font = ImageFont.truetype(
                    "C:/Windows/Fonts/georgia.ttf",
                    font_size
                )

                wrapped = textwrap.fill(
                    text,
                    width=max(
                        15,
                        int(font_size / 2)
                    )
                )

                bbox = draw.multiline_textbbox(
                    (0, 0),
                    f'"{wrapped}"',
                    font=quote_font,
                    spacing=15
                )

                text_width = (
                    bbox[2] -
                    bbox[0]
                )

                if (
                    text_width <= max_text_width
                    or font_size <= 30
                ):
                    break

                font_size -= 5

            text_height = (
                bbox[3] -
                bbox[1]
            )

            draw.multiline_text(
                (
                    100,
                    (height - text_height) // 2 - 40
                ),
                f'"{wrapped}"',
                font=quote_font,
                fill="white",
                spacing=15
            )

            avatar = avatar.resize(
                (180, 180)
            )

            mask = Image.new(
                "L",
                avatar.size,
                0
            )

            mask_draw = ImageDraw.Draw(
                mask
            )

            mask_draw.ellipse(
                (0, 0, 180, 180),
                fill=255
            )

            img.paste(
                avatar,
                (1080, 300),
                mask
            )

            draw.text(
                (980, 510),
                f"- {author.display_name}",
                font=name_font,
                fill=(220, 220, 220)
            )

            draw.text(
                (100, 630),
                "https://clanker.pxsl.dev/",
                font=small_font,
                fill=(130, 130, 130)
            )

            buffer = io.BytesIO()

            img.convert(
                "RGB"
            ).save(
                buffer,
                "PNG"
            )

            buffer.seek(0)

            await interaction.followup.send(
                file=discord.File(
                    buffer,
                    "quote.png"
                )
            )

            avatar.close()
            img.close()

        except:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="Error ❌",
                    description="Couldn't create the quote image.",
                    color=discord.Color.red()
                )
            )

    @image_1.command(
        name="brighten",
        description="Brighten an image"
    )
    async def brighten(
        self,
        interaction: Interaction,
        amount: int = 1,
        media: discord.Attachment = None,
        url: str = None
    ):
        amount = max(
            0,
            min(amount, 5)
        )

        img, err_title, err_desc = await self.load_image(
            interaction,
            media,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        result = ImageEnhance.Brightness(
            img.convert("RGB")
        ).enhance(
            1 + amount * 0.2
        )

        await self.send_image(
            interaction,
            result,
            f"Brightened Image ☀️ (Level: {amount})",
            "brighten.png"
        )

        img.close()
        result.close()

    @image_1.command(
        name="darken",
        description="Darken an image"
    )
    async def darken(
        self,
        interaction: Interaction,
        amount: int = 1,
        media: discord.Attachment = None,
        url: str = None
    ):
        amount = max(
            0,
            min(amount, 5)
        )

        img, err_title, err_desc = await self.load_image(
            interaction,
            media,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        result = ImageEnhance.Brightness(
            img.convert("RGB")
        ).enhance(
            max(
                0,
                1 - amount * 0.2
            )
        )

        await self.send_image(
            interaction,
            result,
            f"Darkened Image 🌑 (Level: {amount})",
            "darken.png"
        )

        img.close()
        result.close()

    @image_1.command(
        name="sharpen",
        description="Sharpen an image"
    )
    async def sharpen(
        self,
        interaction: Interaction,
        amount: int = 1,
        media: discord.Attachment = None,
        url: str = None
    ):
        amount = max(
            1,
            min(amount, 10)
        )

        img, err_title, err_desc = await self.load_image(
            interaction,
            media,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        result = img.convert(
            "RGB"
        ).filter(
            ImageFilter.UnsharpMask(
                radius=2,
                percent=100 + amount * 50,
                threshold=3
            )
        )

        await self.send_image(
            interaction,
            result,
            f"Sharpened Image 🔪 (Amount: {amount})",
            "sharpen.png"
        )

        img.close()
        result.close()

    @image_1.command(
        name="contrast",
        description="Change the contrast of an image"
    )
    async def contrast(
        self,
        interaction: Interaction,
        amount: float = 1.5,
        media: discord.Attachment = None,
        url: str = None
    ):
        amount = max(
            0,
            min(amount, 5)
        )

        img, err_title, err_desc = await self.load_image(
            interaction,
            media,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        result = ImageEnhance.Contrast(
            img.convert("RGB")
        ).enhance(
            amount
        )

        await self.send_image(
            interaction,
            result,
            f"Contrast Image 🌓 (Amount: {amount})",
            "contrast.png"
        )

        img.close()
        result.close()

    @image_1.command(
        name="destroy",
        description="Absolutely destroy an image"
    )
    async def destroy(
        self,
        interaction: Interaction,
        media: discord.Attachment = None,
        url: str = None
    ):
        img, err_title, err_desc = await self.load_image(
            interaction,
            media,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        img = img.convert(
            "RGB"
        )

        effects = [
            "blur",
            "sharpen",
            "contrast",
            "colour",
            "brightness",
            "darkness",
            "pixelate",
            "noise",
            "invert"
        ]

        amount = random.randint(
            5,
            12
        )

        applied = []

        for _ in range(amount):
            effect = random.choice(
                effects
            )

            if effect == "blur":
                value = random.randint(
                    1,
                    15
                )

                img = img.filter(
                    ImageFilter.GaussianBlur(
                        value
                    )
                )

                applied.append(
                    f"Blur ({value})"
                )

            elif effect == "sharpen":
                value = random.randint(
                    100,
                    500
                )

                img = img.filter(
                    ImageFilter.UnsharpMask(
                        radius=random.randint(1, 5),
                        percent=value,
                        threshold=random.randint(1, 5)
                    )
                )

                applied.append(
                    f"Sharpen ({value}%)"
                )

            elif effect == "contrast":
                value = random.uniform(
                    0.5,
                    4
                )

                img = ImageEnhance.Contrast(
                    img
                ).enhance(
                    value
                )

                applied.append(
                    f"Contrast ({round(value, 2)})"
                )

            elif effect == "colour":
                value = random.uniform(
                    0,
                    5
                )

                img = ImageEnhance.Color(
                    img
                ).enhance(
                    value
                )

                applied.append(
                    f"Colour ({round(value, 2)})"
                )

            elif effect == "brightness":
                value = random.uniform(
                    0.2,
                    3
                )

                img = ImageEnhance.Brightness(
                    img
                ).enhance(
                    value
                )

                applied.append(
                    f"Brightness ({round(value, 2)})"
                )

            elif effect == "darkness":
                value = random.uniform(
                    0.1,
                    0.8
                )

                img = ImageEnhance.Brightness(
                    img
                ).enhance(
                    value
                )

                applied.append(
                    f"Darkness ({round(value, 2)})"
                )

            elif effect == "pixelate":
                value = random.randint(
                    2,
                    30
                )

                small = img.resize(
                    (
                        max(1, img.width // value),
                        max(1, img.height // value)
                    ),
                    Image.Resampling.NEAREST
                )

                img = small.resize(
                    img.size,
                    Image.Resampling.NEAREST
                )

            elif effect == "noise":
                noise = Image.effect_noise(
                    img.size,
                    random.randint(20, 60)
                ).convert(
                    "RGB"
                )

                img = Image.blend(
                    img,
                    noise,
                    0.25
                )

                applied.append(
                    "Noise"
                )

            elif effect == "invert":
                img = ImageOps.invert(
                    img
                )

                applied.append(
                    "Invert"
                )

        await self.send_image(
            interaction,
            img,
            "Image Destroyed 💀",
            "destroy.png",
            (
                f"Applied {len(applied)} random effects:\n"
                +
                "\n".join(
                    f"• {effect}"
                    for effect in applied[:10]
                )
            )
        )

        img.close()

    @image_1.command(
        name="rotate",
        description="Change the rotation of an image"
    )
    async def rotate(
        self,
        interaction: Interaction,
        angle: float = 90.0,
        media: discord.Attachment = None,
        url: str = None,
        clockwise: bool = True,
    ):
        img, err_title, err_desc = await self.load_image(
            interaction,
            media,
            url
        )

        if clockwise:
            angle = -angle

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        result = img.rotate(angle=angle)

        clockwiseStr = "Counter-clockwise"
        if clockwise:
            clockwiseStr = "Clockwise"

        await self.send_image(
            interaction,
            result,
            f"Rotate Image 🔄 {clockwiseStr} (Angle: {abs(angle)})",
            "rotate.png"
        )

        img.close()
        result.close()


async def setup(bot):
    await bot.add_cog(
        Images(bot)
    )