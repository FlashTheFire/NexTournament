"""
NexTournament v2.0 - Universal Screen & Message Editing Utility
Provides safe in-place media, caption, and text updates preventing duplicate message spam.
"""

import logging
import random
from typing import Optional, Union, Any
from aiogram import Bot
from aiogram.types import Message, InlineKeyboardMarkup, InputMediaPhoto, InputFile
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger("nextournament.utils.screen")


def get_random_hero_banner() -> str:
    """Returns a random Free Fire hero banner image URL (ID: 201-315)."""
    return f"https://t.me/public_file_only/{random.randint(201, 315)}"


async def edit_screen(
    message: Optional[Message] = None,
    caption: str = "",
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    photo: Optional[Union[str, InputFile]] = None,
    parse_mode: Optional[str] = "HTML",
    bot: Optional[Any] = None,
    chat_id: Optional[int] = None,
    message_id: Optional[int] = None,
) -> Optional[Message]:
    """
    Seamlessly edits an existing message in-place:
    - If photo is provided: edits media (photo, caption, keyboard) atomically via edit_media.
    - If photo is None and message has media: edits caption and keyboard via edit_caption.
    - If message is a text message: edits text and keyboard via edit_text.
    - Can target a Message object or explicit (bot, chat_id, message_id).
    - Cross-falls back between edit_caption and edit_text if message type differs from expectation.
    - Resiliently ignores 'message is not modified' Telegram exceptions.
    - Falls back to unformatted text if parse_mode entity formatting errors occur.
    - Never sends a new message.
    """
    target_bot = bot or (message.bot if message else None)
    target_chat_id = chat_id or (message.chat.id if message else None)
    target_message_id = message_id or (message.message_id if message else None)

    if not target_bot or not target_chat_id or not target_message_id:
        if message:
            return message
        return None

    if photo:
        media = InputMediaPhoto(media=photo, caption=caption, parse_mode=parse_mode)
        try:
            res = await target_bot.edit_message_media(
                chat_id=target_chat_id,
                message_id=target_message_id,
                media=media,
                reply_markup=reply_markup,
            )
            return res if isinstance(res, Message) else message
        except TelegramBadRequest as e:
            err_msg = str(e).lower()
            if "message is not modified" in err_msg:
                return message
            if "can't parse entities" in err_msg or "tag" in err_msg:
                try:
                    media_raw = InputMediaPhoto(media=photo, caption=caption, parse_mode=None)
                    res = await target_bot.edit_message_media(
                        chat_id=target_chat_id,
                        message_id=target_message_id,
                        media=media_raw,
                        reply_markup=reply_markup,
                    )
                    return res if isinstance(res, Message) else message
                except Exception:
                    pass
            logger.debug(f"edit_media failed ({e}), attempting caption/text fallback")
        except Exception as e:
            logger.debug(f"edit_media unexpected error: {e}")

    # Fallback or photo is not changed
    has_photo = bool(message and message.photo)
    if has_photo or (message is None):
        try:
            res = await target_bot.edit_message_caption(
                chat_id=target_chat_id,
                message_id=target_message_id,
                caption=caption,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
            return res if isinstance(res, Message) else message
        except TelegramBadRequest as e:
            err_msg = str(e).lower()
            if "message is not modified" in err_msg:
                return message
            if "can't parse entities" in err_msg or "tag" in err_msg:
                try:
                    res = await target_bot.edit_message_caption(
                        chat_id=target_chat_id,
                        message_id=target_message_id,
                        caption=caption,
                        reply_markup=reply_markup,
                        parse_mode=None,
                    )
                    return res if isinstance(res, Message) else message
                except Exception:
                    pass
            if "there is no caption" in err_msg or "no text in the message" in err_msg or "message can't be edited" not in err_msg:
                try:
                    res = await target_bot.edit_message_text(
                        chat_id=target_chat_id,
                        message_id=target_message_id,
                        text=caption,
                        reply_markup=reply_markup,
                        parse_mode=parse_mode,
                    )
                    return res if isinstance(res, Message) else message
                except Exception:
                    pass
            logger.warning(f"edit_caption failed: {e}")
        except Exception as e:
            logger.warning(f"edit_caption unexpected error: {e}")
    else:
        try:
            res = await target_bot.edit_message_text(
                chat_id=target_chat_id,
                message_id=target_message_id,
                text=caption,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
            return res if isinstance(res, Message) else message
        except TelegramBadRequest as e:
            err_msg = str(e).lower()
            if "message is not modified" in err_msg:
                return message
            if "can't parse entities" in err_msg or "tag" in err_msg:
                try:
                    res = await target_bot.edit_message_text(
                        chat_id=target_chat_id,
                        message_id=target_message_id,
                        text=caption,
                        reply_markup=reply_markup,
                        parse_mode=None,
                    )
                    return res if isinstance(res, Message) else message
                except Exception:
                    pass
            if "there is no text in the message to edit" in err_msg:
                try:
                    res = await target_bot.edit_message_caption(
                        chat_id=target_chat_id,
                        message_id=target_message_id,
                        caption=caption,
                        reply_markup=reply_markup,
                        parse_mode=parse_mode,
                    )
                    return res if isinstance(res, Message) else message
                except Exception:
                    pass
            logger.warning(f"edit_text failed: {e}")
        except Exception as e:
            logger.warning(f"edit_text unexpected error: {e}")
    return message
