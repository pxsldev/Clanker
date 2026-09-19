from discord import app_commands, Interaction
from discord.ext import commands
import discord
import aiohttp
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageFont, ImageDraw
from pilmoji import Pilmoji
import io
import textwrap
import os
import zipfile
import shutil
import tempfile
import asyncio
import random

class Video(commands.GroupCog, group_name="video"):
    video_1 = app_commands.Group(
        name="1",
        description="Video - page 1"
    )

    MAX_DOWNLOAD_SIZE = 50 * 1024 * 1024
    MAX_OUTPUT_SIZE = 7 * 1024 * 1024
    MAX_VIDEO_DURATION = 20
    MAX_VIDEO_WIDTH = 960
    MAX_VIDEO_HEIGHT = 540
    MAX_VIDEO_FPS = 15
    MAX_FRAMES = 180
    MAX_GIF_FRAMES = 40
    MAX_BOOMERANG_FRAMES = 60

    VIDEO_EXTENSIONS = {
        ".mp4",
        ".mov",
        ".webm",
        ".mkv",
        ".avi",
        ".m4v",
        ".wmv",
        ".flv"
    }

    def __init__(self, bot):
        self.bot = bot
        self.video_lock = asyncio.Semaphore(1)

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

    def get_extension(
        self,
        media_url: str,
        path: str
    ):
        extension = os.path.splitext(
            media_url.lower().split("?")[0]
        )[1]

        if extension:
            return extension

        return os.path.splitext(
            path.lower()
        )[1]

    def is_video(
        self,
        extension: str
    ):
        return extension in self.VIDEO_EXTENSIONS

    async def get_video_info(
        self,
        input_path: str
    ):
        try:
            process = await asyncio.create_subprocess_exec(
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-show_entries",
                "stream=width,height,r_frame_rate",
                "-of",
                "default=noprint_wrappers=1",
                input_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, _ = await process.communicate()

            if process.returncode != 0:
                return None

            data = stdout.decode(
                errors="ignore"
            ).splitlines()

            duration = 0
            width = 0
            height = 0
            fps = 0

            for line in data:
                if line.startswith("duration="):
                    try:
                        duration = float(
                            line.split(
                                "=",
                                1
                            )[1]
                        )
                    except:
                        pass

                elif line.startswith("width="):
                    try:
                        width = int(
                            line.split(
                                "=",
                                1
                            )[1]
                        )
                    except:
                        pass

                elif line.startswith("height="):
                    try:
                        height = int(
                            line.split(
                                "=",
                                1
                            )[1]
                        )
                    except:
                        pass

                elif line.startswith("r_frame_rate="):
                    try:
                        value = line.split(
                            "=",
                            1
                        )[1]

                        if "/" in value:
                            numerator, denominator = value.split(
                                "/"
                            )

                            fps = (
                                float(numerator) /
                                float(denominator)
                            )
                        else:
                            fps = float(value)

                    except:
                        pass

            return {
                "duration": duration,
                "width": width,
                "height": height,
                "fps": fps
            }

        except:
            return None

    async def validate_video(
        self,
        input_path: str
    ):
        info = await self.get_video_info(
            input_path
        )

        if not info:
            return False, "Invalid or unsupported video."

        if info["duration"] <= 0:
            return False, "Couldn't determine the video duration."

        if info["duration"] > self.MAX_VIDEO_DURATION:
            return False, (
                "That video is too long.\n\n"
                f"Videos are limited to **{self.MAX_VIDEO_DURATION} seconds**."
            )

        if info["width"] <= 0 or info["height"] <= 0:
            return False, "Couldn't determine the video resolution."

        return True, None

    async def extract_video_frames(
        self,
        input_path: str,
        output_dir: str,
        max_frames: int
    ):
        os.makedirs(
            output_dir,
            exist_ok=True
        )

        output_pattern = os.path.join(
            output_dir,
            "frame_%04d.jpg"
        )

        process = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-vf",
            (
                f"fps={self.MAX_VIDEO_FPS},"
                f"scale={self.MAX_VIDEO_WIDTH}:{self.MAX_VIDEO_HEIGHT}:"
                "force_original_aspect_ratio=decrease"
            ),
            "-frames:v",
            str(max_frames),
            "-q:v",
            "4",
            output_pattern,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE
        )

        await process.communicate()

        if process.returncode != 0:
            return False

        return len(
            os.listdir(output_dir)
        ) > 0

    async def encode_frames_to_video(
        self,
        frames_dir: str,
        output_path: str,
        fps: float = 15
    ):
        input_pattern = os.path.join(
            frames_dir,
            "frame_%04d.jpg"
        )

        process = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-y",
            "-framerate",
            str(fps),
            "-i",
            input_pattern,
            "-vf",
            "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "26",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            output_path,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE
        )

        await process.communicate()

        if process.returncode != 0:
            return False

        if not os.path.exists(output_path):
            return False

        if os.path.getsize(output_path) > self.MAX_OUTPUT_SIZE:
            try:
                os.remove(output_path)
            except:
                pass

            return False

        return True

    async def process_video_frames(
        self,
        input_path: str,
        output_path: str,
        processor
    ):
        async with self.video_lock:
            temp_dir = tempfile.mkdtemp()

            try:
                input_frames = os.path.join(
                    temp_dir,
                    "input"
                )

                output_frames = os.path.join(
                    temp_dir,
                    "output"
                )

                os.makedirs(
                    input_frames,
                    exist_ok=True
                )

                os.makedirs(
                    output_frames,
                    exist_ok=True
                )

                success = await self.extract_video_frames(
                    input_path,
                    input_frames,
                    self.MAX_FRAMES
                )

                if not success:
                    return False

                frame_files = sorted(
                    os.listdir(
                        input_frames
                    )
                )

                if not frame_files:
                    return False

                for index, filename in enumerate(
                    frame_files
                ):
                    input_frame = Image.open(
                        os.path.join(
                            input_frames,
                            filename
                        )
                    ).convert(
                        "RGB"
                    )

                    output_frame = processor(
                        input_frame
                    )

                    output_frame.save(
                        os.path.join(
                            output_frames,
                            f"frame_{index + 1:04d}.jpg"
                        ),
                        "JPEG",
                        quality=88,
                        optimize=False
                    )

                    input_frame.close()
                    output_frame.close()

                info = await self.get_video_info(
                    input_path
                )

                fps = self.MAX_VIDEO_FPS

                if info and info["fps"] > 0:
                    fps = min(
                        info["fps"],
                        self.MAX_VIDEO_FPS
                    )

                return await self.encode_frames_to_video(
                    output_frames,
                    output_path,
                    fps
                )

            finally:
                shutil.rmtree(
                    temp_dir,
                    ignore_errors=True
                )

    async def process_effect(
        self,
        interaction: Interaction,
        media: discord.Attachment,
        url: str,
        processor,
        title: str,
        filename: str,
        description: str = None
    ):
        await interaction.response.defer()

        media_url = await self.get_media_url(
            interaction,
            media,
            url
        )

        if not media_url:
            return await self.send_error(
                interaction,
                "Missing Video ⚠️",
                "Upload, reply, or provide a video URL."
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
                return await self.send_error(
                    interaction,
                    "Download Error 🚫",
                    error
                )

            extension = self.get_extension(
                media_url,
                input_path
            )

            if not self.is_video(
                extension
            ):
                return await self.send_error(
                    interaction,
                    "Invalid Video 🚫",
                    "That file isn't a supported video."
                )

            valid, error = await self.validate_video(
                input_path
            )

            if not valid:
                return await self.send_error(
                    interaction,
                    "Video Rejected 🚫",
                    error
                )

            output_path = os.path.join(
                temp_dir,
                filename
            )

            success = await self.process_video_frames(
                input_path,
                output_path,
                processor
            )

            if not success:
                return await self.send_error(
                    interaction,
                    "Processing Error 🚫",
                    "I couldn't process that video."
                )

            embed = discord.Embed(
                title=title,
                description=description if description else "",
                color=discord.Color.blurple()
            )

            await interaction.followup.send(
                embed=embed,
                file=discord.File(
                    output_path,
                    filename=filename
                )
            )

        finally:
            shutil.rmtree(
                temp_dir,
                ignore_errors=True
            )

    @video_1.command(
        name="invert",
        description="Invert a video"
    )
    async def invert(
        self,
        interaction: Interaction,
        media: discord.Attachment = None,
        url: str = None
    ):
        def processor(img):
            return ImageOps.invert(
                img.convert("RGB")
            )

        await self.process_effect(
            interaction,
            media,
            url,
            processor,
            "Inverted Video 🌀",
            "invert.mp4"
        )

    @video_1.command(
        name="greyscale",
        description="Convert a video to greyscale"
    )
    async def greyscale(
        self,
        interaction: Interaction,
        media: discord.Attachment = None,
        url: str = None
    ):
        def processor(img):
            return ImageOps.grayscale(
                img
            ).convert("RGB")

        await self.process_effect(
            interaction,
            media,
            url,
            processor,
            "Greyscale Video ⚪",
            "greyscale.mp4"
        )

    @video_1.command(
        name="deepfry",
        description="Deep fry a video"
    )
    async def deepfry(
        self,
        interaction: Interaction,
        media: discord.Attachment = None,
        url: str = None
    ):
        def processor(img):
            result = img.convert(
                "RGB"
            )

            result = ImageEnhance.Contrast(
                result
            ).enhance(2.0)

            result = ImageEnhance.Color(
                result
            ).enhance(3.0)

            return result.filter(
                ImageFilter.UnsharpMask(
                    radius=2,
                    percent=150
                )
            )

        await self.process_effect(
            interaction,
            media,
            url,
            processor,
            "Deepfried Video 💥",
            "deepfry.mp4"
        )

    @video_1.command(
        name="blur",
        description="Blur a video"
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

        def processor(img):
            return img.filter(
                ImageFilter.GaussianBlur(
                    radius=amount
                )
            ).convert("RGB")

        await self.process_effect(
            interaction,
            media,
            url,
            processor,
            f"Blurred Video (Amount: {amount}) 💨",
            "blur.mp4"
        )

    @video_1.command(
        name="bloom",
        description="Add bloom effect to a video"
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

        def processor(img):
            result = ImageEnhance.Brightness(
                img
            ).enhance(
                amount
            )

            return result.filter(
                ImageFilter.GaussianBlur(
                    radius=5
                )
            ).convert("RGB")

        await self.process_effect(
            interaction,
            media,
            url,
            processor,
            f"Bloom Video (Amount: {amount}) ✨",
            "bloom.mp4"
        )

    @video_1.command(
        name="pixelate",
        description="Pixelate a video"
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

        def processor(img):
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

            return small.resize(
                img.size,
                Image.Resampling.NEAREST
            ).convert("RGB")

        await self.process_effect(
            interaction,
            media,
            url,
            processor,
            f"Pixelated Video (Amount: {amount}) 🟫",
            "pixelate.mp4"
        )

    @video_1.command(
        name="brighten",
        description="Brighten a video"
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

        def processor(img):
            return ImageEnhance.Brightness(
                img.convert("RGB")
            ).enhance(
                1 + amount * 0.2
            )

        await self.process_effect(
            interaction,
            media,
            url,
            processor,
            f"Brightened Video ☀️ (Level: {amount})",
            "brighten.mp4"
        )

    @video_1.command(
        name="darken",
        description="Darken a video"
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

        def processor(img):
            return ImageEnhance.Brightness(
                img.convert("RGB")
            ).enhance(
                max(
                    0,
                    1 - amount * 0.2
                )
            )

        await self.process_effect(
            interaction,
            media,
            url,
            processor,
            f"Darkened Video 🌑 (Level: {amount})",
            "darken.mp4"
        )

    @video_1.command(
        name="sharpen",
        description="Sharpen a video"
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

        def processor(img):
            return img.convert(
                "RGB"
            ).filter(
                ImageFilter.UnsharpMask(
                    radius=2,
                    percent=100 + amount * 50,
                    threshold=3
                )
            )

        await self.process_effect(
            interaction,
            media,
            url,
            processor,
            f"Sharpened Video 🔪 (Amount: {amount})",
            "sharpen.mp4"
        )

    @video_1.command(
        name="contrast",
        description="Change the contrast of a video"
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

        def processor(img):
            return ImageEnhance.Contrast(
                img.convert("RGB")
            ).enhance(
                amount
            )

        await self.process_effect(
            interaction,
            media,
            url,
            processor,
            f"Contrast Video 🌓 (Amount: {amount})",
            "contrast.mp4"
        )

    @video_1.command(
        name="gif",
        description="Turn a video into a GIF"
    )
    async def gif(
        self,
        interaction: Interaction,
        media: discord.Attachment = None,
        url: str = None
    ):
        await interaction.response.defer()

        media_url = await self.get_media_url(
            interaction,
            media,
            url
        )

        if not media_url:
            return await self.send_error(
                interaction,
                "Missing Video ⚠️",
                "Upload, reply, or provide a video URL."
            )

        temp_dir = tempfile.mkdtemp()

        try:
            input_path = os.path.join(
                temp_dir,
                "input"
            )

            output_path = os.path.join(
                temp_dir,
                "video.gif"
            )

            success, error = await self.download_media(
                media_url,
                input_path
            )

            if not success:
                return await self.send_error(
                    interaction,
                    "Download Error 🚫",
                    error
                )

            valid, error = await self.validate_video(
                input_path
            )

            if not valid:
                return await self.send_error(
                    interaction,
                    "Video Rejected 🚫",
                    error
                )

            process = await asyncio.create_subprocess_exec(
                "ffmpeg",
                "-y",
                "-i",
                input_path,
                "-t",
                str(self.MAX_VIDEO_DURATION),
                "-vf",
                (
                    f"fps={self.MAX_VIDEO_FPS},"
                    "scale=640:640:"
                    "force_original_aspect_ratio=decrease,"
                    "pad=640:640:(ow-iw)/2:(oh-ih)/2"
                ),
                "-frames:v",
                str(self.MAX_GIF_FRAMES),
                "-loop",
                "0",
                output_path,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE
            )

            await process.communicate()

            if process.returncode != 0:
                return await self.send_error(
                    interaction,
                    "Conversion Error 🚫",
                    "I couldn't convert that video to a GIF."
                )

            embed = discord.Embed(
                title="Video → GIF 🖼️",
                description=(
                    "Converted successfully.\n"
                    "Animated GIFs are limited to 256 colours."
                ),
                color=discord.Color.blurple()
            )

            embed.set_image(
                url="attachment://video.gif"
            )

            await interaction.followup.send(
                embed=embed,
                file=discord.File(
                    output_path,
                    filename="video.gif"
                )
            )

        finally:
            shutil.rmtree(
                temp_dir,
                ignore_errors=True
            )

    @video_1.command(
        name="caption",
        description="Add a caption to a video"
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

        media_url = await self.get_media_url(
            interaction,
            media,
            url
        )

        if not media_url:
            return await self.send_error(
                interaction,
                "Missing Video ⚠️",
                "Upload, reply, or provide a video URL."
            )

        temp_dir = tempfile.mkdtemp()

        try:
            input_path = os.path.join(
                temp_dir,
                "input"
            )

            frames_dir = os.path.join(
                temp_dir,
                "frames"
            )

            output_dir = os.path.join(
                temp_dir,
                "output"
            )

            output_path = os.path.join(
                temp_dir,
                "caption.mp4"
            )

            os.makedirs(
                frames_dir,
                exist_ok=True
            )

            os.makedirs(
                output_dir,
                exist_ok=True
            )

            success, error = await self.download_media(
                media_url,
                input_path
            )

            if not success:
                return await self.send_error(
                    interaction,
                    "Download Error 🚫",
                    error
                )

            valid, error = await self.validate_video(
                input_path
            )

            if not valid:
                return await self.send_error(
                    interaction,
                    "Video Rejected 🚫",
                    error
                )

            success = await self.extract_video_frames(
                input_path,
                frames_dir,
                self.MAX_FRAMES
            )

            if not success:
                return await self.send_error(
                    interaction,
                    "Processing Error 🚫",
                    "Couldn't extract the video frames."
                )

            frame_files = sorted(
                os.listdir(
                    frames_dir
                )
            )

            for index, frame_file in enumerate(
                frame_files
            ):
                frame = Image.open(
                    os.path.join(
                        frames_dir,
                        frame_file
                    )
                ).convert(
                    "RGBA"
                )

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

                text_width = (
                    bbox[2] -
                    bbox[0]
                )

                text_height = (
                    bbox[3] -
                    bbox[1]
                )

                padding = font_size // 2

                caption_height = (
                    text_height +
                    padding * 2
                )

                if caption_height % 2:
                    caption_height += 1

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

                output.convert(
                    "RGB"
                ).save(
                    os.path.join(
                        output_dir,
                        f"frame_{index + 1:04d}.jpg"
                    ),
                    "JPEG",
                    quality=88
                )

                frame.close()
                output.close()

            info = await self.get_video_info(
                input_path
            )

            fps = self.MAX_VIDEO_FPS

            if info and info["fps"] > 0:
                fps = min(
                    info["fps"],
                    self.MAX_VIDEO_FPS
                )

            success = await self.encode_frames_to_video(
                output_dir,
                output_path,
                fps
            )

            if not success:
                return await self.send_error(
                    interaction,
                    "Encoding Error 🚫",
                    "Couldn't create the processed video."
                )

            embed = discord.Embed(
                title="Caption 📝",
                color=discord.Color.blurple()
            )

            await interaction.followup.send(
                embed=embed,
                file=discord.File(
                    output_path,
                    filename="caption.mp4"
                )
            )

        finally:
            shutil.rmtree(
                temp_dir,
                ignore_errors=True
            )

    @video_1.command(
        name="frames",
        description="Extract frames from a video"
    )
    async def frames(
        self,
        interaction: Interaction,
        media: discord.Attachment = None,
        url: str = None
    ):
        await interaction.response.defer()

        media_url = await self.get_media_url(
            interaction,
            media,
            url
        )

        if not media_url:
            return await self.send_error(
                interaction,
                "Missing Video ⚠️",
                "Upload a video or provide a URL."
            )

        temp_dir = tempfile.mkdtemp()

        try:
            input_path = os.path.join(
                temp_dir,
                "input"
            )

            output_dir = os.path.join(
                temp_dir,
                "frames"
            )

            os.makedirs(
                output_dir,
                exist_ok=True
            )

            success, error = await self.download_media(
                media_url,
                input_path
            )

            if not success:
                return await self.send_error(
                    interaction,
                    "Download Error 🚫",
                    error
                )

            valid, error = await self.validate_video(
                input_path
            )

            if not valid:
                return await self.send_error(
                    interaction,
                    "Video Rejected 🚫",
                    error
                )

            success = await self.extract_video_frames(
                input_path,
                output_dir,
                self.MAX_FRAMES
            )

            if not success:
                return await self.send_error(
                    interaction,
                    "Extraction Error 🚫",
                    "Couldn't extract frames from that video."
                )

            frame_files = sorted(
                os.listdir(
                    output_dir
                )
            )

            if not frame_files:
                return await self.send_error(
                    interaction,
                    "Extraction Error 🚫",
                    "No frames could be extracted."
                )

            zip_path = os.path.join(
                temp_dir,
                "frames.zip"
            )

            with zipfile.ZipFile(
                zip_path,
                "w",
                compression=zipfile.ZIP_DEFLATED
            ) as zipf:
                for frame in frame_files:
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
                    f"**{len(frame_files)} frames**!"
                ),
                color=discord.Color.blurple()
            )

            if len(frame_files) >= self.MAX_FRAMES:
                embed.set_footer(
                    text=(
                        f"Limited to the first "
                        f"{self.MAX_FRAMES} frames."
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

    @video_1.command(
        name="boomerang",
        description="Create a boomerang from a video"
    )
    async def boomerang(
        self,
        interaction: Interaction,
        media: discord.Attachment = None,
        url: str = None
    ):
        await interaction.response.defer()

        media_url = await self.get_media_url(
            interaction,
            media,
            url
        )

        if not media_url:
            return await self.send_error(
                interaction,
                "Missing Video ⚠️",
                "Upload a video or provide a URL."
            )

        temp_dir = tempfile.mkdtemp()

        try:
            input_path = os.path.join(
                temp_dir,
                "input"
            )

            frames_dir = os.path.join(
                temp_dir,
                "frames"
            )

            output_path = os.path.join(
                temp_dir,
                "boomerang.gif"
            )

            os.makedirs(
                frames_dir,
                exist_ok=True
            )

            success, error = await self.download_media(
                media_url,
                input_path
            )

            if not success:
                return await self.send_error(
                    interaction,
                    "Download Error 🚫",
                    error
                )

            valid, error = await self.validate_video(
                input_path
            )

            if not valid:
                return await self.send_error(
                    interaction,
                    "Video Rejected 🚫",
                    error
                )

            info = await self.get_video_info(
                input_path
            )

            duration = 100

            if info and info["fps"] > 0:
                duration = int(
                    1000 /
                    min(
                        info["fps"],
                        self.MAX_VIDEO_FPS
                    )
                )

            success = await self.extract_video_frames(
                input_path,
                frames_dir,
                self.MAX_BOOMERANG_FRAMES
            )

            if not success:
                return await self.send_error(
                    interaction,
                    "Extraction Error 🚫",
                    "Couldn't extract any video frames."
                )

            frame_files = sorted(
                os.listdir(
                    frames_dir
                )
            )

            frames = []

            for frame_file in frame_files:
                frame = Image.open(
                    os.path.join(
                        frames_dir,
                        frame_file
                    )
                ).convert(
                    "RGBA"
                )

                frames.append(
                    frame.copy()
                )

                frame.close()

            if not frames:
                return await self.send_error(
                    interaction,
                    "Error ❌",
                    "Couldn't extract any frames."
                )

            boomerang_frames = (
                frames +
                frames[-2::-1]
            )

            boomerang_frames[0].save(
                output_path,
                format="GIF",
                save_all=True,
                append_images=boomerang_frames[1:],
                duration=duration,
                loop=0,
                disposal=2
            )

            for frame in frames:
                frame.close()

            embed = discord.Embed(
                title="🔁 Boomerang Created",
                description=(
                    f"Created a boomerang with "
                    f"**{len(boomerang_frames)} frames**!"
                ),
                color=discord.Color.blurple()
            )

            if len(frames) >= self.MAX_BOOMERANG_FRAMES:
                embed.set_footer(
                    text=(
                        f"Limited to the first "
                        f"{self.MAX_BOOMERANG_FRAMES} frames."
                    )
                )

            embed.set_image(
                url="attachment://boomerang.gif"
            )

            await interaction.followup.send(
                embed=embed,
                file=discord.File(
                    output_path,
                    filename="boomerang.gif"
                )
            )

        finally:
            shutil.rmtree(
                temp_dir,
                ignore_errors=True
            )

    @video_1.command(
        name="destroy",
        description="Absolutely destroy a video"
    )
    async def destroy(
        self,
        interaction: Interaction,
        media: discord.Attachment = None,
        url: str = None
    ):
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
            9
        )

        selected = random.sample(
            effects,
            min(
                amount,
                len(effects)
            )
        )

        def processor(img):
            img = img.convert(
                "RGB"
            )

            for effect in selected:
                if effect == "blur":
                    img = img.filter(
                        ImageFilter.GaussianBlur(
                            random.randint(
                                1,
                                8
                            )
                        )
                    )

                elif effect == "sharpen":
                    img = img.filter(
                        ImageFilter.UnsharpMask(
                            radius=random.randint(
                                1,
                                4
                            ),
                            percent=random.randint(
                                100,
                                400
                            ),
                            threshold=random.randint(
                                1,
                                5
                            )
                        )
                    )

                elif effect == "contrast":
                    img = ImageEnhance.Contrast(
                        img
                    ).enhance(
                        random.uniform(
                            0.5,
                            4
                        )
                    )

                elif effect == "colour":
                    img = ImageEnhance.Color(
                        img
                    ).enhance(
                        random.uniform(
                            0,
                            5
                        )
                    )

                elif effect == "brightness":
                    img = ImageEnhance.Brightness(
                        img
                    ).enhance(
                        random.uniform(
                            0.2,
                            3
                        )
                    )

                elif effect == "darkness":
                    img = ImageEnhance.Brightness(
                        img
                    ).enhance(
                        random.uniform(
                            0.1,
                            0.8
                        )
                    )

                elif effect == "pixelate":
                    value = random.randint(
                        2,
                        20
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
                        Image.Resampling.NEAREST
                    )

                    img = small.resize(
                        img.size,
                        Image.Resampling.NEAREST
                    )

                elif effect == "noise":
                    noise = Image.effect_noise(
                        img.size,
                        random.randint(
                            20,
                            60
                        )
                    ).convert(
                        "RGB"
                    )

                    img = Image.blend(
                        img,
                        noise,
                        0.15
                    )

                elif effect == "invert":
                    img = ImageOps.invert(
                        img
                    )

            return img

        await self.process_effect(
            interaction,
            media,
            url,
            processor,
            "Video Destroyed 💀",
            "destroy.mp4",
            "Applied a random combination of effects."
        )

    @video_1.command(
        name="rotate",
        description="Change the Rotation of a video"
    )
    async def rotate(
        self,
        interaction: Interaction,
        angle: float = 90.0,
        media: discord.Attachment = None,
        url: str = None,
        clockwise: bool = True,
    ):
        if clockwise:
            angle = -angle
        
        def processor(img):
            return img.rotate(angle=angle)

        clockwiseStr = "Counter-clockwise"
        if clockwise:
            clockwiseStr = "Clockwise"

        await self.process_effect(
            interaction,
            media,
            url,
            processor,
            f"Rotate Video 🔄 {clockwiseStr} (Angle: {abs(angle)})",
            "rotate.mp4"
        )


async def setup(bot):
    await bot.add_cog(
        Video(bot)
    )