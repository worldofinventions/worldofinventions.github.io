"""Shared look of the two bots of the ecosystem: display name, short description
and profile photo ("World of Inventions · Global" and "Мир изобретений · Россия").

Each server calls apply_branding() at startup. It does the work only once: when
the bot's current name already equals the wanted one, nothing is sent, so the
profile photo is not re-uploaded on every restart. To roll out a new avatar,
change the name or bump BRANDING_VERSION (it forces one more pass).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from aiogram import Bot
from aiogram.types import FSInputFile, InputProfilePhotoStatic

log = logging.getLogger("branding")

AVATAR_DIR = Path(__file__).resolve().parent / "assets" / "avatars"
EN_AVATAR = AVATAR_DIR / "world-global.png"
RU_AVATAR = AVATAR_DIR / "world-russia.png"

EN_NAME = "World of Inventions · Global"
RU_NAME = "Мир изобретений · Россия"

# Set BRANDING_FORCE=1 on the host to push name/description/photo again once.
_FORCE = os.getenv("BRANDING_FORCE", "").strip() == "1"


async def apply_branding(bot: Bot, name: str, short_description: str, avatar: Path) -> None:
    try:
        current = await bot.get_my_name()
        if current.name == name and not _FORCE:
            return
        await bot.set_my_name(name=name)
        await bot.set_my_short_description(short_description=short_description)
        if avatar.is_file():
            await bot.set_my_profile_photo(photo=InputProfilePhotoStatic(photo=FSInputFile(avatar)))
        log.info("Branding applied: %s", name)
    except Exception as exc:
        # The bot works without it; only the look is not updated.
        log.warning("Could not apply branding %r: %s", name, exc)
