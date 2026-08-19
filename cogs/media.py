# im a meediwa file

from discord import app_commands, Interaction
from discord.ext import commands
import discord
import aiohttp
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageFont, ImageDraw
import io
import textwrap
from pilmoji import Pilmoji
import os
import cv2
import zipfile
import shutil
import tempfile
import math
import random
import numpy as np


class Media(commands.GroupCog, group_name="media"):
    media_1 = app_commands.Group(
        name="1",
        description="Media - page 1"
    )

    def __init__(self, bot):
        self.bot = bot

    async def get_image(
        self,
        interaction: Interaction,
        image: discord.Attachment = None,
        url: str = None
    ):
        image_url = None

        if image:
            image_url = image.url

        elif url:
            image_url = url

        elif interaction.message and interaction.message.reference:
            try:
                replied = await interaction.channel.fetch_message(
                    interaction.message.reference.message_id
                )

                if replied.attachments:
                    image_url = replied.attachments[0].url

            except:
                pass

        if not image_url:
            async for msg in interaction.channel.history(limit=20):
                if msg.attachments:
                    image_url = msg.attachments[0].url
                    break

        if not image_url:
            return None, "Missing Image ⚠️", "Upload, reply, or provide a URL."

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status != 200:
                        return None, "Error 🚫", "Failed to download the image."

                    data = await resp.read()

            return Image.open(io.BytesIO(data)), None, None

        except:
            return None, "Error 🚫", "Invalid image format."

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

        await interaction.response.send_message(embed=embed)

    async def send_image(
        self,
        interaction: Interaction,
        img: Image.Image,
        title: str,
        filename: str,
        desc: str = None
    ):
        buffer = io.BytesIO()

        img.save(buffer, format="PNG")
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

        await interaction.response.send_message(
            embed=embed,
            file=file
        )

    # ============================================================
    # /media 1
    # ============================================================

    @media_1.command(
        name="invert",
        description="Invert an image"
    )
    async def invert(
        self,
        interaction: Interaction,
        image: discord.Attachment = None,
        url: str = None
    ):
        img, err_title, err_desc = await self.get_image(
            interaction,
            image,
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

    @media_1.command(
        name="greyscale",
        description="Convert image to greyscale"
    )
    async def greyscale(
        self,
        interaction: Interaction,
        image: discord.Attachment = None,
        url: str = None
    ):
        img, err_title, err_desc = await self.get_image(
            interaction,
            image,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        img = ImageOps.grayscale(img)

        await self.send_image(
            interaction,
            img,
            "Greyscale Image ⚪",
            "greyscale.png"
        )

    @media_1.command(
        name="deepfry",
        description="Deep fry an image"
    )
    async def deepfry(
        self,
        interaction: Interaction,
        image: discord.Attachment = None,
        url: str = None
    ):
        img, err_title, err_desc = await self.get_image(
            interaction,
            image,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        img = img.convert("RGB")

        img = ImageEnhance.Contrast(img).enhance(2.0)
        img = ImageEnhance.Color(img).enhance(3.0)

        img = img.filter(
            ImageFilter.UnsharpMask(
                radius=2,
                percent=150
            )
        )

        await self.send_image(
            interaction,
            img,
            "Deepfried Image 💥",
            "deepfry.png"
        )

    @media_1.command(
        name="blur",
        description="Blur an image"
    )
    async def blur(
        self,
        interaction: Interaction,
        amount: int = 5,
        image: discord.Attachment = None,
        url: str = None
    ):
        img, err_title, err_desc = await self.get_image(
            interaction,
            image,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        img = img.filter(
            ImageFilter.GaussianBlur(
                radius=amount
            )
        )

        await self.send_image(
            interaction,
            img,
            f"Blurred Image (Amount: {amount}) 💨",
            "blur.png"
        )

    @media_1.command(
        name="bloom",
        description="Add bloom effect"
    )
    async def bloom(
        self,
        interaction: Interaction,
        amount: float = 1.5,
        image: discord.Attachment = None,
        url: str = None
    ):
        img, err_title, err_desc = await self.get_image(
            interaction,
            image,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        img = ImageEnhance.Brightness(img).enhance(amount)

        img = img.filter(
            ImageFilter.GaussianBlur(radius=5)
        )

        await self.send_image(
            interaction,
            img,
            f"Bloom Image (Amount: {amount}) ✨",
            "bloom.png"
        )

    @media_1.command(
        name="pixelate",
        description="Pixelate an image"
    )
    async def pixelate(
        self,
        interaction: Interaction,
        amount: int = 10,
        image: discord.Attachment = None,
        url: str = None
    ):
        img, err_title, err_desc = await self.get_image(
            interaction,
            image,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        img = img.resize(
            (
                img.width // amount,
                img.height // amount
            ),
            Image.NEAREST
        )

        img = img.resize(
            (
                img.width * amount,
                img.height * amount
            ),
            Image.NEAREST
        )

        await self.send_image(
            interaction,
            img,
            f"Pixelated Image (Amount: {amount}) 🟫",
            "pixelate.png"
        )

    @media_1.command(
        name="gif",
        description="Turn an image into a GIF"
    )
    async def gif(
        self,
        interaction: Interaction,
        image: discord.Attachment = None,
        url: str = None
    ):
        img, err_title, err_desc = await self.get_image(
            interaction,
            image,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        img = img.convert("RGBA")

        buffer = io.BytesIO()

        img.save(
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
            description="GIFs are limited to 256 colors - quality may drop ⚠️",
            color=discord.Color.blurple()
        )

        embed.set_image(
            url="attachment://image.gif"
        )

        await interaction.response.send_message(
            embed=embed,
            file=file
        )

    @media_1.command(
        name="png",
        description="Turn an image into a PNG"
    )
    async def png(
        self,
        interaction: Interaction,
        image: discord.Attachment = None,
        url: str = None
    ):
        img, err_title, err_desc = await self.get_image(
            interaction,
            image,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        try:
            img.seek(0)
        except (AttributeError, EOFError):
            pass

        img = img.convert("RGBA")

        buffer = io.BytesIO()

        img.save(
            buffer,
            format="PNG"
        )

        buffer.seek(0)

        file = discord.File(
            buffer,
            filename="image.png"
        )

        embed = discord.Embed(
            title="Image → PNG 🖼️",
            description="Converted successfully.",
            color=discord.Color.blurple()
        )

        embed.set_image(
            url="attachment://image.png"
        )

        await interaction.response.send_message(
            embed=embed,
            file=file
        )

    @media_1.command(
        name="jpg",
        description="Turn an image into a JPG"
    )
    async def jpg(
        self,
        interaction: Interaction,
        image: discord.Attachment = None,
        url: str = None
    ):
        img, err_title, err_desc = await self.get_image(
            interaction,
            image,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        try:
            img.seek(0)
        except (AttributeError, EOFError):
            pass

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

            background.paste(
                img.convert("RGBA"),
                mask=img.convert("RGBA").split()[-1]
            )

            img = background

        else:
            img = img.convert("RGB")

        buffer = io.BytesIO()

        img.save(
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
            description="Transparency has been replaced with a white background.",
            color=discord.Color.blurple()
        )

        embed.set_image(
            url="attachment://image.jpg"
        )

        await interaction.response.send_message(
            embed=embed,
            file=file
        )

    @media_1.command(
        name="webp",
        description="Turn an image into a WebP"
    )
    async def webp(
        self,
        interaction: Interaction,
        image: discord.Attachment = None,
        url: str = None
    ):
        img, err_title, err_desc = await self.get_image(
            interaction,
            image,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        try:
            img.seek(0)
        except (AttributeError, EOFError):
            pass

        img = img.convert("RGBA")

        buffer = io.BytesIO()

        img.save(
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

    @media_1.command(
        name="caption",
        description="Add a caption to the top of an image"
    )
    async def caption(
        self,
        interaction: Interaction,
        image: discord.Attachment = None,
        text: str = None,
        url: str = None
    ):
        await interaction.response.defer()

        img, err_title, err_desc = await self.get_image(
            interaction,
            image,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        if not text:
            return await self.send_error(
                interaction,
                "Missing Text ⚠️",
                "Please provide a caption."
            )

        try:
            img.seek(0)
        except:
            pass

        is_gif = getattr(img, "format", None) == "GIF"

        frames = []

        if is_gif:
            for frame in range(img.n_frames):
                img.seek(frame)

                frames.append(
                    img.convert("RGBA").copy()
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
            frames.append(
                img.convert("RGBA")
            )

            duration = None
            loop = 0

        processed_frames = []

        for frame in frames:
            width, height = frame.size

            font_size = max(
                32,
                width // 10
            )

            font = ImageFont.truetype(
                "C:/Windows/Fonts/impact.ttf",
                font_size
            )

            chars_per_line = max(
                8,
                width // (font_size // 2)
            )

            wrapped = textwrap.fill(
                text,
                width=chars_per_line
            )

            temp = Image.new(
                "RGBA",
                (width, height),
                "white"
            )

            draw = ImageDraw.Draw(temp)

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
                (padding * 2)
            )

            output = Image.new(
                "RGBA",
                (width, height + caption_height),
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

            processed_frames.append(output)

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

    @media_1.command(
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
                        description="Couldn't find a recent message from that user.",
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

        async with aiohttp.ClientSession() as session:
            async with session.get(
                author.display_avatar.url
            ) as resp:
                avatar_bytes = await resp.read()

        avatar = Image.open(
            io.BytesIO(avatar_bytes)
        ).convert("RGBA")

        WIDTH = 1400
        HEIGHT = 700

        img = Image.new(
            "RGBA",
            (WIDTH, HEIGHT),
            (12, 12, 18, 255)
        )

        draw = ImageDraw.Draw(img)

        glow = Image.new(
            "RGBA",
            (WIDTH, HEIGHT),
            (0, 0, 0, 0)
        )

        glow_draw = ImageDraw.Draw(glow)

        glow_draw.ellipse(
            (1050, 260, 1320, 530),
            fill=(120, 80, 255, 120)
        )

        glow = glow.filter(
            ImageFilter.GaussianBlur(60)
        )

        img.alpha_composite(glow)

        quote_font = ImageFont.truetype(
            "C:/Windows/Fonts/georgia.ttf",
            65
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
                (HEIGHT - text_height) // 2 - 40
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

        mask_draw = ImageDraw.Draw(mask)

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

        img.convert("RGB").save(
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

    @media_1.command(
        name="brighten",
        description="Brighten an image"
    )
    async def brighten(
        self,
        interaction: Interaction,
        amount: int = 1,
        image: discord.Attachment = None,
        url: str = None
    ):
        img, err_title, err_desc = await self.get_image(
            interaction,
            image,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        img = img.convert("RGB")

        brightness = 1 + (
            amount * 0.2
        )

        img = ImageEnhance.Brightness(
            img
        ).enhance(brightness)

        await self.send_image(
            interaction,
            img,
            f"Brightened Image ☀️ (Level: {amount})",
            "brighten.png"
        )

    @media_1.command(
        name="darken",
        description="Darken an image"
    )
    async def darken(
        self,
        interaction: Interaction,
        amount: int = 1,
        image: discord.Attachment = None,
        url: str = None
    ):
        img, err_title, err_desc = await self.get_image(
            interaction,
            image,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        img = img.convert("RGB")

        brightness = max(
            0,
            1 - (amount * 0.2)
        )

        img = ImageEnhance.Brightness(
            img
        ).enhance(brightness)

        await self.send_image(
            interaction,
            img,
            f"Darkened Image 🌑 (Level: {amount})",
            "darken.png"
        )

    @media_1.command(
        name="frames",
        description="Extract all frames from a GIF or video"
    )
    async def frames(
        self,
        interaction: Interaction,
        image: discord.Attachment = None,
        url: str = None
    ):
        await interaction.response.defer()

        MAX_FRAMES = 500

        image_url = None

        if image:
            image_url = image.url

        elif url:
            image_url = url

        if not image_url:
            return await self.send_error(
                interaction,
                "Missing File ⚠️",
                "Upload a GIF/video or provide a URL."
            )

        temp_dir = tempfile.mkdtemp()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    data = await resp.read()

            input_path = os.path.join(
                temp_dir,
                "input"
            )

            with open(input_path, "wb") as f:
                f.write(data)

            output_dir = os.path.join(
                temp_dir,
                "output"
            )

            os.makedirs(
                output_dir,
                exist_ok=True
            )

            if image_url.lower().split("?")[0].endswith(".gif"):
                gif = Image.open(input_path)

                for i in range(
                    min(
                        gif.n_frames,
                        MAX_FRAMES
                    )
                ):
                    gif.seek(i)

                    frame = gif.convert("RGBA")

                    frame.save(
                        os.path.join(
                            output_dir,
                            f"frame_{i:04}.png"
                        )
                    )

            else:
                cap = cv2.VideoCapture(
                    input_path
                )

                i = 0

                while i < MAX_FRAMES:
                    success, frame = cap.read()

                    if not success:
                        break

                    cv2.imwrite(
                        os.path.join(
                            output_dir,
                            f"frame_{i:04}.png"
                        ),
                        frame
                    )

                    i += 1

                cap.release()

            frame_count = len(
                os.listdir(output_dir)
            )

            zip_path = os.path.join(
                temp_dir,
                "frames.zip"
            )

            with zipfile.ZipFile(
                zip_path,
                "w"
            ) as zipf:

                for frame in os.listdir(
                    output_dir
                ):
                    zipf.write(
                        os.path.join(
                            output_dir,
                            frame
                        ),
                        frame
                    )

            embed = discord.Embed(
                title="📦 Extracted Frames",
                description=(
                    f"Successfully extracted "
                    f"**{frame_count} frames**!"
                ),
                color=discord.Color.blurple()
            )

            if frame_count >= MAX_FRAMES:
                embed.set_footer(
                    text=(
                        f"Limited to the first "
                        f"{MAX_FRAMES} frames."
                    )
                )

            await interaction.followup.send(
                embed=embed,
                file=discord.File(
                    zip_path,
                    filename="frames.zip"
                )
            )

        finally:
            shutil.rmtree(
                temp_dir,
                ignore_errors=True
            )

    @media_1.command(
        name="boomerang",
        description="Create a boomerang effect from a GIF or video"
    )
    async def boomerang(
        self,
        interaction: Interaction,
        image: discord.Attachment = None,
        url: str = None
    ):
        await interaction.response.defer()

        MAX_FRAMES = 250

        image_url = None

        if image:
            image_url = image.url

        elif url:
            image_url = url

        if not image_url:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Error ❌",
                    description="Upload a GIF/video or provide a URL.",
                    color=discord.Color.red()
                )
            )

        temp_dir = tempfile.mkdtemp()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    data = await resp.read()

            input_path = os.path.join(
                temp_dir,
                "input"
            )

            with open(input_path, "wb") as f:
                f.write(data)

            frames = []

            if image_url.lower().split("?")[0].endswith(".gif"):
                gif = Image.open(input_path)

                duration = gif.info.get(
                    "duration",
                    100
                )

                for i in range(
                    min(
                        gif.n_frames,
                        MAX_FRAMES
                    )
                ):
                    gif.seek(i)

                    frames.append(
                        gif.convert("RGBA").copy()
                    )

            else:
                cap = cv2.VideoCapture(
                    input_path
                )

                fps = cap.get(
                    cv2.CAP_PROP_FPS
                )

                if fps <= 0:
                    fps = 24

                duration = int(
                    1000 / fps
                )

                i = 0

                while i < MAX_FRAMES:
                    success, frame = cap.read()

                    if not success:
                        break

                    frame = cv2.cvtColor(
                        frame,
                        cv2.COLOR_BGR2RGBA
                    )

                    frames.append(
                        Image.fromarray(frame)
                    )

                    i += 1

                cap.release()

            if not frames:
                return await interaction.followup.send(
                    embed=discord.Embed(
                        title="Error ❌",
                        description="Couldn't extract any frames.",
                        color=discord.Color.red()
                    )
                )

            boomerang_frames = (
                frames +
                frames[-2::-1]
            )

            output = os.path.join(
                temp_dir,
                "boomerang.gif"
            )

            boomerang_frames[0].save(
                output,
                format="GIF",
                save_all=True,
                append_images=boomerang_frames[1:],
                duration=duration,
                loop=0
            )

            embed = discord.Embed(
                title="🔁 Boomerang Created",
                description=(
                    f"Created a boomerang with "
                    f"**{len(boomerang_frames)} frames**!"
                ),
                color=discord.Color.blurple()
            )

            if len(frames) >= MAX_FRAMES:
                embed.set_footer(
                    text=(
                        f"Limited to the first "
                        f"{MAX_FRAMES} frames."
                    )
                )

            embed.set_image(
                url="attachment://boomerang.gif"
            )

            await interaction.followup.send(
                embed=embed,
                file=discord.File(
                    output,
                    filename="boomerang.gif"
                )
            )

        finally:
            shutil.rmtree(
                temp_dir,
                ignore_errors=True
            )

    @media_1.command(
        name="sharpen",
        description="Sharpen an image"
    )
    async def sharpen(
        self,
        interaction: Interaction,
        amount: int = 1,
        image: discord.Attachment = None,
        url: str = None
    ):
        img, err_title, err_desc = await self.get_image(
            interaction,
            image,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        img = img.convert("RGB")

        amount = max(
            1,
            min(amount, 10)
        )

        sharpened = img.filter(
            ImageFilter.UnsharpMask(
                radius=2,
                percent=100 + (amount * 50),
                threshold=3
            )
        )

        await self.send_image(
            interaction,
            sharpened,
            f"Sharpened Image 🔪 (Amount: {amount})",
            "sharpen.png"
        )

    @media_1.command(
        name="contrast",
        description="Change the contrast of an image"
    )
    async def contrast(
        self,
        interaction: Interaction,
        amount: float = 1.5,
        image: discord.Attachment = None,
        url: str = None
    ):
        img, err_title, err_desc = await self.get_image(
            interaction,
            image,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        img = img.convert("RGB")

        amount = max(
            0,
            min(amount, 5)
        )

        img = ImageEnhance.Contrast(
            img
        ).enhance(amount)

        await self.send_image(
            interaction,
            img,
            f"Contrast Image 🌓 (Amount: {amount})",
            "contrast.png"
        )

    @media_1.command(
        name="destroy",
        description="Absolutely destroy an image"
    )
    async def destroy(
        self,
        interaction: Interaction,
        image: discord.Attachment = None,
        url: str = None
    ):
        img, err_title, err_desc = await self.get_image(
            interaction,
            image,
            url
        )

        if not img:
            return await self.send_error(
                interaction,
                err_title,
                err_desc
            )

        img = img.convert("RGB")

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

        random.shuffle(effects)

        applied = []

        amount = random.randint(
            5,
            12
        )

        for _ in range(amount):
            effect = random.choice(effects)

            if effect == "blur":
                value = random.randint(
                    1,
                    15
                )

                img = img.filter(
                    ImageFilter.GaussianBlur(value)
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
                ).enhance(value)

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
                ).enhance(value)

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
                ).enhance(value)

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
                ).enhance(value)

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
                        max(
                            1,
                            img.width // value
                        ),
                        max(
                            1,
                            img.height // value
                        )
                    ),
                    Image.NEAREST
                )

                img = small.resize(
                    img.size,
                    Image.NEAREST
                )

                applied.append(
                    f"Pixelate ({value})"
                )

            elif effect == "noise":
                pixels = img.load()

                for x in range(img.width):
                    for y in range(img.height):
                        r, g, b = pixels[x, y]

                        noise = random.randint(
                            -50,
                            50
                        )

                        pixels[x, y] = (
                            max(
                                0,
                                min(255, r + noise)
                            ),
                            max(
                                0,
                                min(255, g + noise)
                            ),
                            max(
                                0,
                                min(255, b + noise)
                            )
                        )

                applied.append("Noise")

            elif effect == "invert":
                img = ImageOps.invert(img)

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
                    f"• {x}"
                    for x in applied[:10]
                )
            )
        )


async def setup(bot):
    await bot.add_cog(
        Media(bot)
    )