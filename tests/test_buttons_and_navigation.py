"""
Unit tests for Reply Keyboard navigation, button matching, and HTML parsing safety.
Verifies fixes for user-reported button routing issues and admin console integration.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from aiogram.types import Message, CallbackQuery, User as TgUser, Chat
from aiogram.fsm.context import FSMContext

from src.utils.typography import box_frame, to_small_caps, status_badge
from src.utils.keyboards import (
    get_main_keyboard,
    get_admin_keyboard,
    get_start_terms_keyboard,
    get_tournament_menu_keyboard,
    get_tournament_categories_keyboard,
    get_deposit_menu_keyboard,
    get_profile_menu_keyboard,
    get_more_menu_keyboard,
    get_status_menu_keyboard,
    get_support_menu_keyboard,
    get_withdraw_menu_keyboard,
    ADMIN_BTN_CREATE_MATCH,
    ADMIN_BTN_BROADCAST_ROOM,
    ADMIN_BTN_DECLARE_RESULTS,
    ADMIN_BTN_PROOF_QUEUE,
    ADMIN_BTN_DEPOSIT_QUEUE,
    ADMIN_BTN_WITHDRAW_QUEUE,
    ADMIN_BTN_ADMIN_PANEL,
    ADMIN_BTN_USER_MODE,
)
from src.handlers.start import (
    ALL_TOURNAMENT_BTNS,
    ALL_DEPOSIT_BTNS,
    ALL_PROFILE_BTNS,
    ALL_MORE_BTNS,
    ALL_STATUS_BTNS,
    ALL_LEADERBOARD_BTNS,
    ALL_WITHDRAW_BTNS,
    ALL_SUPPORT_BTNS,
    ALL_SETTINGS_BTNS,
    ALL_ADMIN_BTNS,
)
from src.handlers.leaderboard import build_leaderboard_content
from src.database.models import User, MatchResult, UserRole


def test_box_frame_html_safety():
    """Verify box_frame escapes <, >, and & characters to prevent Telegram HTML parse errors."""
    output = box_frame(
        "Deposit <Portal>",
        [
            ("Speed (< ₹500)", "⚡ Auto-credited in < 60s & fast"),
            ("Speed (≥ ₹500)", "🛡️ Staff verified in < 5m"),
        ],
        footer="Help & Info <Tips>",
    )
    # Ensure raw unescaped HTML tags do not exist
    assert "< ₹500" not in output
    assert "< 60s" not in output
    assert "< 5m" not in output
    assert "&lt; ₹500" in output
    assert "&lt; 60s" in output
    assert "&lt; 5m" in output
    assert "&amp;" in output
    assert "<b>" in output
    assert "<code>" in output


def test_button_matching_sets_contain_all_variants():
    """Verify that button sets cover small-caps, standard english, and translations."""
    # Deposit
    assert "💰 Dᴇᴘᴏsɪᴛ" in ALL_DEPOSIT_BTNS
    assert "💰 Deposit" in ALL_DEPOSIT_BTNS
    assert "💰 पैसे जोड़ें" in ALL_DEPOSIT_BTNS

    # Withdraw
    assert "🪙 Wɪᴛʜᴅʀᴀᴡ" in ALL_WITHDRAW_BTNS
    assert "🪙 Withdraw" in ALL_WITHDRAW_BTNS
    assert "🪙 पैसे निकालें" in ALL_WITHDRAW_BTNS

    # Leaderboard
    assert "📊 Lᴇᴀᴅᴇʀʙᴏᴀʀᴅ" in ALL_LEADERBOARD_BTNS
    assert "📊 Leaderboard" in ALL_LEADERBOARD_BTNS
    assert "📊 लीडरबोर्ड" in ALL_LEADERBOARD_BTNS

    # Profile
    assert "👨‍💻 Pʀᴏғɪʟᴇ" in ALL_PROFILE_BTNS
    assert "👨‍💻 Profile" in ALL_PROFILE_BTNS

    # Tournaments
    assert "🛒 Tᴏᴜʀɴᴀᴍᴇɴᴛ" in ALL_TOURNAMENT_BTNS
    assert "🛒 Tournament" in ALL_TOURNAMENT_BTNS

    # Admin Panel
    assert "👮‍♂️ Aᴅᴍɪɴ Pᴀɴᴇʟ" in ALL_ADMIN_BTNS
    assert "⚙️ Aᴅᴍɪɴ Pᴀɴᴇʟ" in ALL_ADMIN_BTNS


def test_admin_keyboard_buttons_match_constants():
    """Verify that every button in get_admin_keyboard matches our routing constants."""
    kb = get_admin_keyboard()
    button_texts = [btn.text for row in kb.keyboard for btn in row]
    
    assert ADMIN_BTN_CREATE_MATCH in button_texts
    assert ADMIN_BTN_BROADCAST_ROOM in button_texts
    assert ADMIN_BTN_DECLARE_RESULTS in button_texts
    assert ADMIN_BTN_PROOF_QUEUE in button_texts
    assert ADMIN_BTN_DEPOSIT_QUEUE in button_texts
    assert ADMIN_BTN_WITHDRAW_QUEUE in button_texts
    assert ADMIN_BTN_ADMIN_PANEL in button_texts
    assert ADMIN_BTN_USER_MODE in button_texts


@pytest.mark.asyncio
async def test_leaderboard_build_content_uses_valid_column():
    """Verify build_leaderboard_content constructs SQL queries using prize_amount."""
    # We pass a mock session that returns an empty list
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.execute.return_value = mock_result

    # Both categories should execute cleanly without attribute error
    text_earnings = await build_leaderboard_content(period="weekly", category="earnings", session=mock_session)
    assert "🏆 <b>NEXTOURNAMENT WEEKLY STANDINGS</b>" in text_earnings
    assert "Category: TOP PRIZE EARNERS" in text_earnings

    text_kills = await build_leaderboard_content(period="all_time", category="kills", session=mock_session)
    assert "🏆 <b>NEXTOURNAMENT ALL-TIME HALL OF FAME</b>" in text_kills
    assert "Category: TOP FRAGGERS / KILLERS" in text_kills


def test_primary_main_keyboard_layout():
    """Verify that get_main_keyboard matches the exact established 3-row (+1 admin) layout."""
    user_kb = get_main_keyboard(role="user")
    rows = [[btn.text for btn in row] for row in user_kb.keyboard]

    # Verify exact 3 rows and button text matching the established UI specification
    assert len(rows) == 3
    assert rows[0] == ["🛒 Tᴏᴜʀɴᴀᴍᴇɴᴛ", "💰 Dᴇᴘᴏsɪᴛ"]
    assert rows[1] == ["👨‍💻 Pʀᴏғɪʟᴇ", "🔥 Mᴏʀᴇ", "📊 Sᴛᴀᴛᴜs"]
    assert rows[2] == ["👤 Sᴜᴘᴘᴏʀᴛ", "🪙 Wɪᴛʜᴅʀᴀᴡ"]

    # Verify admin gets 4th row
    admin_kb = get_main_keyboard(role="admin")
    admin_rows = [[btn.text for btn in row] for row in admin_kb.keyboard]
    assert len(admin_rows) == 4
    assert admin_rows[3] == ["👮‍♂️ Aᴅᴍɪɴ Pᴀɴᴇʟ"]


def test_terms_and_menu_keyboards_structure():
    """Verify terms keyboard, more buttons, and modern 2.0 menu inline keyboards with multi-language support."""
    assert "🔥 Mᴏʀᴇ" in ALL_MORE_BTNS
    assert "📊 Sᴛᴀᴛᴜs" in ALL_STATUS_BTNS

    terms_kb = get_start_terms_keyboard(channel_url="https://t.me/test_channel")
    assert len(terms_kb.inline_keyboard) == 2
    assert terms_kb.inline_keyboard[0][0].web_app is not None
    assert terms_kb.inline_keyboard[1][0].url == "https://t.me/test_channel"
    assert terms_kb.inline_keyboard[1][1].callback_data == "terms:confirm"

    status_kb = get_status_menu_keyboard()
    assert status_kb.inline_keyboard[0][0].callback_data == "status:refresh_metrics"

    deposit_kb = get_deposit_menu_keyboard()
    assert [btn.callback_data for btn in deposit_kb.inline_keyboard[0]] == [
        "deposit:method:crypto_trx",
        "deposit:method:redeem_code",
        "deposit:method:inr_gateway",
    ]

    support_kb = get_support_menu_keyboard()
    assert support_kb.inline_keyboard[0][0].url == "https://t.me/uday_x"

    withdraw_kb = get_withdraw_menu_keyboard()
    assert withdraw_kb.inline_keyboard[0][0].callback_data == "withdraw:method:upi"
    assert withdraw_kb.inline_keyboard[0][1].callback_data == "withdraw:method:play_store"


def test_tournament_menu_button_positions():
    """
    Verify exact requirement:
    - Tournament search button in LEFT (switch_inline_query_current_chat="")
    - Notify Me button in RIGHT (callback_data="tournament:notify_toggle")
    - Browse All Tournaments in ROW 2 (callback_data="tournament:browse_all")
    """
    kb = get_tournament_menu_keyboard(lang="en")
    assert len(kb.inline_keyboard) == 2
    row0 = kb.inline_keyboard[0]
    row1 = kb.inline_keyboard[1]

    assert len(row0) == 2
    # Left button (index 0) = Tournament search
    assert "🔍" in row0[0].text
    assert row0[0].switch_inline_query_current_chat == ""

    # Right button (index 1) = Notify Me
    assert "🔔" in row0[1].text
    assert row0[1].callback_data == "tournament:notify_toggle"

    # Row 1 button = Browse All Tournaments
    assert len(row1) == 1
    assert "🏆" in row1[0].text
    assert row1[0].callback_data == "tournament:browse_all"


def test_tournament_categories_keyboard_has_back_to_menu():
    """Verify that tournament category browser contains Back To Menu navigation button."""
    cat_kb = get_tournament_categories_keyboard(active_filter="all", lang="en")
    callbacks = [btn.callback_data for row in cat_kb.inline_keyboard for btn in row if btn.callback_data]
    assert "tournament:menu" in callbacks


@pytest.mark.asyncio
async def test_browse_all_and_back_to_menu_edit_in_place_no_new_msg():
    """
    Verify user requirement:
    On clicking Browse All Tournaments, caption, buttons and image edit in-place,
    and NO new message is sent!
    """
    from aiogram.types import InputMediaPhoto
    from src.handlers.start import cb_tournament_browse_all, cb_tournament_menu_back

    # Setup mock callback query with photo message
    mock_msg = MagicMock(spec=Message)
    mock_msg.photo = [MagicMock()]
    mock_msg.edit_media = AsyncMock()
    mock_msg.answer = AsyncMock()

    mock_call = MagicMock(spec=CallbackQuery)
    mock_call.message = mock_msg
    mock_call.answer = AsyncMock()

    # 1. Test clicking Browse All Tournaments
    await cb_tournament_browse_all(mock_call, session=AsyncMock(), user_lang="en")

    # Verify edit_media was called with InputMediaPhoto
    assert mock_msg.edit_media.called is True
    call_args = mock_msg.edit_media.call_args
    media_arg = call_args[1]["media"] if "media" in call_args[1] else call_args[0][0]
    assert isinstance(media_arg, InputMediaPhoto)
    assert to_small_caps("Free Fire Tournament Arena") in media_arg.caption
    assert "Battle Royale" in media_arg.caption

    # CRITICAL: Verify NO new message was created
    assert mock_msg.answer.called is False
    assert mock_call.answer.called is True

    # 2. Test clicking Back to Menu
    mock_msg.edit_media.reset_mock()
    mock_msg.answer.reset_mock()
    mock_call.answer.reset_mock()

    await cb_tournament_menu_back(mock_call, user_lang="en")

    # Verify edit_media was called with InputMediaPhoto
    assert mock_msg.edit_media.called is True
    call_args_back = mock_msg.edit_media.call_args
    media_arg_back = call_args_back[1]["media"] if "media" in call_args_back[1] else call_args_back[0][0]
    assert isinstance(media_arg_back, InputMediaPhoto)
    assert "🔍 Tᴏᴜʀɴᴀᴍᴇɴᴛ" in media_arg_back.caption or "Notify Me" in media_arg_back.caption or "Fʀᴇᴇ Fɪʀᴇ" in media_arg_back.caption

    # CRITICAL: Verify NO new message was created
    assert mock_msg.answer.called is False
    assert mock_call.answer.called is True


@pytest.mark.asyncio
async def test_show_admin_menu_executes_without_deposit_id_attribute_error():
    """Verify show_admin_menu counts deposits using order_id without crashing."""
    from src.handlers.start import show_admin_menu
    from src.config import settings

    mock_msg = MagicMock(spec=Message)
    mock_msg.from_user = MagicMock()
    mock_msg.from_user.id = settings.SUPER_ADMIN_IDS[0]
    mock_msg.answer = AsyncMock()

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar.return_value = 0
    mock_session.execute.return_value = mock_result

    mock_state = AsyncMock(spec=FSMContext)
    mock_user = MagicMock(spec=User)
    mock_user.role = UserRole.SUPERADMIN

    await show_admin_menu(mock_msg, session=mock_session, db_user=mock_user, state=mock_state, user_lang="en")

    assert mock_state.clear.called is True
    assert mock_msg.answer.called is True
    answer_text = mock_msg.answer.call_args[0][0]
    assert "NexTournament Operational Admin Console" in answer_text
    assert "0 Queued" in answer_text


@pytest.mark.asyncio
async def test_link_uid_cancel_and_button_escapes():
    """Verify player can escape LinkUIDState via /cancel or main menu buttons."""
    from src.handlers.start import process_link_uid

    mock_msg = MagicMock(spec=Message)
    mock_msg.from_user = MagicMock()
    mock_msg.from_user.id = 123456789
    mock_msg.answer = AsyncMock()

    mock_state = AsyncMock(spec=FSMContext)
    mock_session = AsyncMock()
    mock_user = MagicMock(spec=User)
    mock_user.role = UserRole.USER

    # 1. Test /cancel in LinkUIDState
    mock_msg.text = "/cancel"
    await process_link_uid(mock_msg, state=mock_state, session=mock_session, db_user=mock_user, user_lang="en")
    assert mock_state.clear.called is True
    assert "Account linking cancelled" in mock_msg.answer.call_args[0][0]

    # 2. Test button escape (e.g. 💰 Dᴇᴘᴏsɪᴛ)
    mock_state.clear.reset_mock()
    mock_msg.answer.reset_mock()
    mock_msg.text = "💰 Dᴇᴘᴏsɪᴛ"
    with pytest.MonkeyPatch.context() as mp:
        mock_show_deposit = AsyncMock()
        mp.setattr("src.handlers.start.show_deposit_menu", mock_show_deposit)
        await process_link_uid(mock_msg, state=mock_state, session=mock_session, db_user=mock_user, user_lang="en")
        assert mock_state.clear.called is True
        assert mock_show_deposit.called is True


@pytest.mark.asyncio
async def test_withdraw_cancel_escape():
    """Verify player can escape WithdrawStates.enter_amount via /cancel or commands."""
    from src.handlers.withdraw import on_amount_entered

    mock_msg = MagicMock(spec=Message)
    mock_msg.from_user = MagicMock()
    mock_msg.from_user.id = 123456789
    mock_msg.answer = AsyncMock()

    mock_state = AsyncMock(spec=FSMContext)

    # Sending /cancel
    mock_msg.text = "/cancel"
    await on_amount_entered(mock_msg, state=mock_state)
    assert mock_state.clear.called is True
    assert "Withdrawal cancelled" in mock_msg.answer.call_args[0][0]
    assert "Please enter a valid number" not in mock_msg.answer.call_args[0][0]

    # Sending /admin
    mock_state.clear.reset_mock()
    mock_msg.answer.reset_mock()
    mock_msg.text = "/admin"
    await on_amount_entered(mock_msg, state=mock_state)
    assert mock_state.clear.called is True
    assert "Withdrawal cancelled" in mock_msg.answer.call_args[0][0]
    assert "Please enter a valid number" not in mock_msg.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_admin_cmd_deposit_queue_executes_cleanly():
    """Verify cmd_deposit_queue queries deposits without AttributeError on DepositStatus."""
    from src.handlers.admin.approvals import cmd_deposit_queue
    from src.config import settings

    mock_msg = MagicMock(spec=Message)
    mock_msg.from_user = MagicMock()
    mock_msg.from_user.id = settings.SUPER_ADMIN_IDS[0]
    mock_msg.answer = AsyncMock()

    with pytest.MonkeyPatch.context() as mp:
        mock_ctx = AsyncMock()
        mock_session = AsyncMock()
        mock_res = MagicMock()
        mock_res.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_res
        mock_ctx.__aenter__.return_value = mock_session
        mp.setattr("src.handlers.admin.approvals.db_session", lambda: mock_ctx)

        await cmd_deposit_queue(mock_msg)
        assert mock_msg.answer.called is True
        assert "Deposit Approval Queue is Clean" in mock_msg.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_tournament_prizes_breakdown_length_safety():
    """Verify cb_prizes_breakdown generates alert text strictly <= 200 chars to prevent MESSAGE_TOO_LONG."""
    from src.handlers.tournament import cb_prizes_breakdown
    from src.services.tournament_service import TournamentService

    mock_call = MagicMock(spec=CallbackQuery)
    mock_call.data = "prizes:101"
    mock_call.answer = AsyncMock()
    mock_session = AsyncMock()

    # Test Battle Royale prizes
    mock_tourn = MagicMock()
    mock_tourn.id = 101

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(TournamentService, "get_tournament_by_id", AsyncMock(return_value=mock_tourn))
        mp.setattr(
            TournamentService,
            "calculate_prizes",
            lambda t: {"1st": 500.0, "2nd": 250.0, "3rd": 100.0, "per_kill": 25.0},
        )
        await cb_prizes_breakdown(mock_call, session=mock_session)
        assert mock_call.answer.called is True
        alert_text = mock_call.answer.call_args[0][0]
        from src.utils.typography import to_small_caps
        assert "1sᴛ Pʟᴀᴄᴇ" in alert_text

        # Test Clash Squad prizes
        mock_call.answer.reset_mock()
        mp.setattr(
            TournamentService,
            "calculate_prizes",
            lambda t: {"winner_team": 800.0, "mvp": 200.0},
        )
        await cb_prizes_breakdown(mock_call, session=mock_session)
        assert mock_call.answer.called is True
        alert_text_cs = mock_call.answer.call_args[0][0]
        assert len(alert_text_cs) <= 200
        assert to_small_caps("Winner Team") in alert_text_cs


@pytest.mark.asyncio
async def test_daily_bonus_and_referral_invocation_safety():
    """Verify cb_more_daily_bonus and cb_more_referral call underlying commands without TypeError."""
    from src.handlers.start import cb_more_daily_bonus, cb_more_referral, nav_daily, nav_referral
    from src.database.models import User, UserRole

    mock_user = MagicMock(spec=User)
    mock_user.telegram_id = 99887766
    mock_user.role = UserRole.USER

    mock_session = AsyncMock()

    # Test cb_more_daily_bonus
    mock_call = MagicMock(spec=CallbackQuery)
    mock_call.from_user = MagicMock()
    mock_call.from_user.id = 99887766
    mock_call.message = MagicMock(spec=Message)
    mock_call.message.answer = AsyncMock()
    mock_call.answer = AsyncMock()

    with pytest.MonkeyPatch.context() as mp:
        mock_claim = AsyncMock(return_value={"already_claimed": True, "streak": 3})
        mp.setattr("src.handlers.daily_bonus.DailyBonusManager.claim_daily_bonus", mock_claim)
        await cb_more_daily_bonus(mock_call, session=mock_session, db_user=mock_user)
        assert mock_call.answer.called is True

    # Test cb_more_referral
    with pytest.MonkeyPatch.context() as mp:
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_session
        mp.setattr("src.handlers.referral.db_session", lambda: mock_ctx)
        mp.setattr(
            "src.handlers.referral.ReferralService.get_referral_stats",
            AsyncMock(return_value={"total_referred": 2, "total_earned": 50.0}),
        )
        mock_call.message.bot = MagicMock()
        mock_bot_user = MagicMock()
        mock_bot_user.username = "TestBot"
        mock_call.message.bot.get_me = AsyncMock(return_value=mock_bot_user)

        await cb_more_referral(mock_call, session=mock_session, db_user=mock_user)
        assert mock_call.answer.called is True


@pytest.mark.asyncio
async def test_profile_keyboards_no_refresh_or_view_16_9():
    """Verify refresh stats and view 16:9 buttons are removed from profile keyboards."""
    from src.utils.keyboards import get_profile_menu_keyboard, get_profile_keyboard

    # Test get_profile_menu_keyboard
    menu_kb = get_profile_menu_keyboard(lang="en")
    all_cb_data = [btn.callback_data for row in menu_kb.inline_keyboard for btn in row if btn.callback_data]
    all_texts = [btn.text for row in menu_kb.inline_keyboard for btn in row]

    assert "profile:refresh_stats" not in all_cb_data
    assert "profile:view_card_16_9" not in all_cb_data
    assert not any("refresh" in text.lower() for text in all_texts)
    assert not any("16:9" in text for text in all_texts)

    # Must contain Edit Details and Quick Deposit
    assert "profile:edit_details" in all_cb_data
    assert "profile:quick_deposit" in all_cb_data

    # Test get_profile_keyboard
    kb_with_uid = get_profile_keyboard(has_uid=True)
    all_cb_uid = [btn.callback_data for row in kb_with_uid.inline_keyboard for btn in row if btn.callback_data]
    assert "refresh_profile" not in all_cb_uid

    kb_no_uid = get_profile_keyboard(has_uid=False)
    all_cb_no_uid = [btn.callback_data for row in kb_no_uid.inline_keyboard for btn in row if btn.callback_data]
    assert "refresh_profile" not in all_cb_no_uid


@pytest.mark.asyncio
async def test_show_profile_menu_async_16_9_update():
    """Verify show_profile_menu delivers initial animated screen and initiates parallel 16:9 card upgrade."""
    import io
    from unittest.mock import patch
    from src.handlers.start import show_profile_menu, _async_update_profile_16_9
    from src.database.models import User, UserRole

    mock_user = MagicMock(spec=User)
    mock_user.telegram_id = 11510698353
    mock_user.ff_ign = "Mohin7KX"
    mock_user.ff_uid = "11510698353"
    mock_user.first_name = "Mohin"
    mock_user.ff_level = 45
    mock_user.ff_region = "IND"
    mock_user.game_balance = Decimal("50.00")
    mock_user.win_balance = Decimal("0.00")
    mock_user.role = UserRole.USER

    mock_msg = MagicMock(spec=Message)
    mock_sent_msg = MagicMock(spec=Message)
    mock_sent_msg.edit_media = AsyncMock()

    mock_session = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar.return_value = 1
    mock_session.execute.return_value = mock_res

    fake_img = io.BytesIO(b"dummy_png_bytes")
    captured_coros = []

    def mock_create_task_side_effect(coro):
        captured_coros.append(coro)
        coro.close()  # Clean up coroutine to avoid unawaited warning
        return MagicMock()

    with patch("src.handlers.start.deliver_animated_screen", AsyncMock(return_value=mock_sent_msg)) as mock_deliver, \
         patch("src.handlers.start.generate_profile_card", AsyncMock(return_value=fake_img)), \
         patch("asyncio.create_task", side_effect=mock_create_task_side_effect) as mock_create_task:

        await show_profile_menu(mock_msg, session=mock_session, db_user=mock_user, user_lang="en")

        assert mock_deliver.called is True
        caption_arg = mock_deliver.call_args[1].get("caption") or mock_deliver.call_args[0][2]
        assert "Mohin7KX" in caption_arg
        assert "11510698353" in caption_arg
        assert "50 Pᴏɪɴᴛ" in caption_arg

        # Verify background task was scheduled
        assert mock_create_task.called is True
        assert len(captured_coros) == 1

    # Directly execute _async_update_profile_16_9 to verify edit_media call
    with patch("src.handlers.start.generate_profile_card", AsyncMock(return_value=fake_img)):
        await _async_update_profile_16_9(
            sent_msg=mock_sent_msg,
            user_id=mock_user.telegram_id,
            ign="Mohin7KX",
            uid="11510698353",
            level=45,
            region="IND",
            t_game=1,
            win_rate=100.0,
            game_bal=50.0,
            win_bal=0.0,
            kills=5,
            profile_text="Dummy Profile Text",
        )
        assert mock_sent_msg.edit_media.called is True
        call_kwargs = mock_sent_msg.edit_media.call_args.kwargs
        media = call_kwargs.get("media")
        assert media is not None
        assert media.caption == "Dummy Profile Text"


@pytest.mark.asyncio
async def test_tournament_notify_toggle_button_and_callback():
    """Verify Notify Me toggles to 🔕 Unnotify Me, updates keyboard in-place and toggles user preference."""
    from src.utils.keyboards import get_tournament_menu_keyboard
    from src.handlers.start import cb_tournament_notify_toggle
    from src.database.models import User, UserRole

    # 1. Keyboard rendering tests
    kb_off = get_tournament_menu_keyboard(is_notified=False, lang="en")
    assert "🔔" in kb_off.inline_keyboard[0][1].text
    assert "Nᴏᴛɪғʏ Mᴇ" in kb_off.inline_keyboard[0][1].text
    assert kb_off.inline_keyboard[0][1].callback_data == "tournament:notify_toggle"

    kb_on = get_tournament_menu_keyboard(is_notified=True, lang="en")
    assert "🔕" in kb_on.inline_keyboard[0][1].text
    assert "Uɴɴᴏᴛɪғʏ Mᴇ" in kb_on.inline_keyboard[0][1].text
    assert kb_on.inline_keyboard[0][1].callback_data == "tournament:notify_toggle"

    # 2. Callback interaction test: Turn ON
    mock_user = MagicMock(spec=User)
    mock_user.telegram_id = 12345678
    mock_user.notifications_enabled = False
    mock_user.role = UserRole.USER

    mock_session = AsyncMock()
    mock_call = MagicMock(spec=CallbackQuery)
    mock_call.message = MagicMock(spec=Message)
    mock_call.message.edit_reply_markup = AsyncMock()
    mock_call.answer = AsyncMock()

    await cb_tournament_notify_toggle(mock_call, session=mock_session, db_user=mock_user, user_lang="en")

    assert mock_user.notifications_enabled is True
    assert mock_session.commit.called is True
    assert mock_call.message.edit_reply_markup.called is True
    updated_kb = mock_call.message.edit_reply_markup.call_args.kwargs["reply_markup"]
    assert "🔕" in updated_kb.inline_keyboard[0][1].text
    assert "Uɴɴᴏᴛɪғʏ Mᴇ" in updated_kb.inline_keyboard[0][1].text
    assert mock_call.answer.called is True
    assert "🔔" in mock_call.answer.call_args[0][0]

    # 3. Callback interaction test: Turn OFF (Unnotify)
    mock_call.message.edit_reply_markup.reset_mock()
    mock_call.answer.reset_mock()

    await cb_tournament_notify_toggle(mock_call, session=mock_session, db_user=mock_user, user_lang="en")

    assert mock_user.notifications_enabled is False
    assert mock_call.message.edit_reply_markup.called is True
    reverted_kb = mock_call.message.edit_reply_markup.call_args.kwargs["reply_markup"]
    assert "🔔" in reverted_kb.inline_keyboard[0][1].text
    assert "Nᴏᴛɪғʏ Mᴇ" in reverted_kb.inline_keyboard[0][1].text
    assert mock_call.answer.called is True
    assert "🔕" in mock_call.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_broadcast_new_tournament_to_subscribers():
    """Verify CredentialBroadcaster.broadcast_new_tournament delivers announcements to subscribers."""
    from src.services.broadcaster import CredentialBroadcaster
    from src.database.models import Tournament, MatchType, TeamFormat, TournamentStatus
    from datetime import datetime, timezone
    from unittest.mock import patch

    mock_tourn = MagicMock(spec=Tournament)
    mock_tourn.id = 77
    mock_tourn.title = "Grand Bermuda Championship"
    mock_tourn.map_name = "Bermuda"
    mock_tourn.match_type = MatchType.BATTLE_ROYALE
    mock_tourn.team_format = TeamFormat.SQUAD
    mock_tourn.entry_fee = Decimal("50.00")
    mock_tourn.total_slots = 48
    mock_tourn.gun_attributes = True
    mock_tourn.status = TournamentStatus.OPEN
    mock_tourn.start_time = datetime(2026, 10, 2, 18, 0, tzinfo=timezone.utc)

    mock_bot = MagicMock()
    mock_bot.send_message = AsyncMock()
    mock_bot_user = MagicMock()
    mock_bot_user.username = "Testing1stTime_Bot"
    mock_bot.get_me = AsyncMock(return_value=mock_bot_user)

    mock_session = AsyncMock()
    mock_result = MagicMock()
    # 2 subscribed users: 1001, 1002
    mock_result.all.return_value = [(1001,), (1002,)]
    mock_session.execute.return_value = mock_result

    with patch("asyncio.sleep", AsyncMock()):  # Avoid test delay
        report = await CredentialBroadcaster.broadcast_new_tournament(
            bot=mock_bot,
            tournament=mock_tourn,
            session=mock_session,
        )

    assert report["success"] is True
    assert report["total_subscribers"] == 2
    assert report["delivered"] == 2
    assert mock_bot.send_message.call_count == 2

    # Verify message content
    first_call_args = mock_bot.send_message.call_args_list[0]
    assert first_call_args.kwargs["chat_id"] == 1001
    assert "Grand Bermuda Championship" in first_call_args.kwargs["text"]
    assert "₹50.00" in first_call_args.kwargs["text"]
    assert "match_77" in first_call_args.kwargs["reply_markup"].inline_keyboard[0][0].url


@pytest.mark.asyncio
async def test_cmd_start_tournament_deep_linking():
    """Verify /start match_4 renders the tournament card with movie-ticket seat selector."""
    from src.handlers.start import cmd_start
    from src.database.models import User, UserRole
    from aiogram.filters import CommandObject
    from unittest.mock import patch

    mock_user = MagicMock(spec=User)
    mock_user.telegram_id = 9999
    mock_user.is_banned = False
    mock_user.role = UserRole.USER

    mock_msg = MagicMock(spec=Message)
    mock_msg.from_user = MagicMock()
    mock_msg.from_user.id = 9999
    mock_msg.from_user.first_name = "ProPlayer"
    mock_msg.from_user.username = "proplayer"
    mock_msg.delete = AsyncMock()
    mock_msg.answer = AsyncMock()

    mock_session = AsyncMock()
    mock_cmd = CommandObject(prefix="/", command="start", args="match_4")

    with patch("src.handlers.inline_query.send_tournament_card", AsyncMock(return_value=True)) as mock_send_card:
        await cmd_start(
            message=mock_msg,
            command=mock_cmd,
            session=mock_session,
            db_user=mock_user,
            user_lang="en",
        )
        assert mock_send_card.called is True
        assert mock_send_card.call_args.kwargs["tourn_id"] == 4
        assert mock_msg.delete.called is True


@pytest.mark.asyncio
async def test_send_tournament_card_matches_inline_query():
    """Verify send_tournament_card delivers the exact match card as inline query."""
    from src.handlers.inline_query import send_tournament_card
    from src.database.models import Tournament, MatchType, TeamFormat, TournamentStatus
    from datetime import datetime, timezone
    from unittest.mock import patch

    mock_tourn = MagicMock(spec=Tournament)
    mock_tourn.id = 4
    mock_tourn.title = "Clash Squad Showdown"
    mock_tourn.map_name = "Bermuda"
    mock_tourn.match_type = MatchType.CLASH_SQUAD
    mock_tourn.team_format = TeamFormat.SQUAD
    mock_tourn.entry_fee = Decimal("25.00")
    mock_tourn.total_slots = 8
    mock_tourn.filled_slots = 2
    mock_tourn.gun_attributes = False
    mock_tourn.per_kill_bounty = Decimal("0.00")
    mock_tourn.base_prize_pool = Decimal("160.00")
    mock_tourn.status = TournamentStatus.OPEN
    mock_tourn.start_time = datetime(2026, 10, 2, 20, 0, tzinfo=timezone.utc)
    mock_tourn.participants = []

    mock_msg = MagicMock(spec=Message)
    mock_msg.from_user = MagicMock()
    mock_msg.from_user.id = 8888
    mock_msg.from_user.username = "player1"
    mock_msg.answer = AsyncMock()
    mock_msg.answer_photo = AsyncMock()

    mock_session = AsyncMock()

    with patch("src.services.tournament_service.TournamentService.get_tournament_by_id", AsyncMock(return_value=mock_tourn)):
        delivered = await send_tournament_card(mock_msg, session=mock_session, tourn_id=4)
        assert delivered is True
        # Delivered via answer_photo or answer fallback
        called_mock = mock_msg.answer_photo if mock_msg.answer_photo.called else mock_msg.answer
        assert called_mock.called is True
        call_args = called_mock.call_args
        caption = call_args.kwargs.get("caption") or call_args.kwargs.get("text") or call_args[0][0]
        assert "#0004" in caption
        assert "25" in caption
        # Notice text must NOT be in the card caption
        assert "📌 Notice:" not in caption
        assert "Tap Choose Your Seat / Team" not in caption

        kb = call_args.kwargs.get("reply_markup")
        cb_list = [btn.callback_data for row in kb.inline_keyboard for btn in row if btn.callback_data]
        assert "seat_view:4" in cb_list
        assert "prizes:4" in cb_list
        assert "rules:4" in cb_list
        # Manual chart button removed from card because 16:9 is auto-assigned on booking
        assert "seat_chart_img:4" not in cb_list


@pytest.mark.asyncio
async def test_tournament_card_admin_keyboard_layout():
    """Verify admin tournament card keyboard contains Broadcast, Edit, and Delete buttons."""
    from src.utils.keyboards import get_tournament_card_keyboard
    from src.config import settings

    admin_id = settings.SUPER_ADMIN_IDS[0]

    # Non-admin keyboard
    user_kb = get_tournament_card_keyboard(tournament_id=4, is_joined=False, is_admin=False)
    user_cbs = [btn.callback_data for row in user_kb.inline_keyboard for btn in row if btn.callback_data]
    assert "seat_view:4" in user_cbs
    assert "prizes:4" in user_cbs
    assert "rules:4" in user_cbs
    assert "admin_bcast:4" not in user_cbs
    assert "admin_edit:4" not in user_cbs
    assert "admin_cancel:4" not in user_cbs

    # Admin keyboard
    admin_kb = get_tournament_card_keyboard(tournament_id=4, is_joined=False, is_admin=True)
    admin_cbs = [btn.callback_data for row in admin_kb.inline_keyboard for btn in row if btn.callback_data]
    assert "seat_view:4" in admin_cbs
    assert "prizes:4" in admin_cbs
    assert "admin_bcast:4" in admin_cbs
    assert "admin_edit:4" in admin_cbs
    assert "admin_cancel:4" in admin_cbs
    assert "rules:4" in admin_cbs

    # Verify rows structure for admin
    # Row 1: Join + Winner Price
    assert admin_kb.inline_keyboard[0][0].callback_data == "seat_view:4"
    assert admin_kb.inline_keyboard[0][1].callback_data == "prizes:4"
    # Row 2: Broadcast ID & Pass
    assert admin_kb.inline_keyboard[1][0].callback_data == "admin_bcast:4"
    # Row 3: Edit Post + Delete Post
    assert admin_kb.inline_keyboard[2][0].callback_data == "admin_edit:4"
    assert admin_kb.inline_keyboard[2][1].callback_data == "admin_cancel:4"


@pytest.mark.asyncio
async def test_deposit_button_edits_caption_and_image_async():
    """Verify clicking deposit button edits existing message in-place: caption first, then media async."""
    import asyncio
    from src.handlers.start import show_deposit_menu, DEPOSIT_PHOTO_URL
    from aiogram.types import CallbackQuery, Message, PhotoSize

    mock_msg = MagicMock(spec=Message)
    mock_msg.photo = [MagicMock(spec=PhotoSize)]
    mock_msg.video = None
    mock_msg.edit_caption = AsyncMock()
    mock_msg.edit_media = AsyncMock()
    mock_msg.answer = AsyncMock()
    mock_msg.answer_photo = AsyncMock()
    mock_msg.answer_video = AsyncMock()

    mock_call = MagicMock(spec=CallbackQuery)
    mock_call.message = mock_msg
    mock_call.answer = AsyncMock()
    mock_call.data = "profile:quick_deposit"

    # Trigger deposit menu from callback
    await show_deposit_menu(mock_call, user_lang="en")

    # 1. Callback answered immediately
    assert mock_call.answer.called is True

    # 2. Caption edited in-place FIRST (no new messages sent!)
    assert mock_msg.edit_caption.called is True
    assert mock_msg.answer.called is False
    assert mock_msg.answer_photo.called is False
    assert mock_msg.answer_video.called is False

    # 3. Allow async background tasks to run and verify edit_media was invoked with deposit banner
    await asyncio.sleep(0.05)
    assert mock_msg.edit_media.called is True
    media_arg = mock_msg.edit_media.call_args[1]["media"]
    assert media_arg.media == DEPOSIT_PHOTO_URL


@pytest.mark.asyncio
async def test_link_uid_in_place_edit_and_user_message_deletion():
    """Verify linking Free Fire UID edits caption/media in-place and immediately deletes user text."""
    from src.handlers.start import start_link_uid, process_link_uid, cb_cancel_link_uid
    from unittest.mock import patch

    # 1. Trigger start_link_uid from callback on profile card
    mock_bot = MagicMock()
    mock_bot.edit_message_caption = AsyncMock()
    mock_bot.edit_message_media = AsyncMock()

    mock_card_msg = MagicMock(spec=Message)
    mock_card_msg.chat = MagicMock()
    mock_card_msg.chat.id = 987654321
    mock_card_msg.message_id = 5555
    mock_card_msg.edit_caption = AsyncMock()
    mock_card_msg.answer = AsyncMock()
    mock_card_msg.bot = mock_bot

    mock_call = MagicMock(spec=CallbackQuery)
    mock_call.message = mock_card_msg
    mock_call.answer = AsyncMock()

    state_store = {}
    mock_state = AsyncMock(spec=FSMContext)
    async def fake_update_data(**kwargs):
        state_store.update(kwargs)
    async def fake_get_data():
        return state_store
    mock_state.update_data = AsyncMock(side_effect=fake_update_data)
    mock_state.get_data = AsyncMock(side_effect=fake_get_data)
    mock_state.set_state = AsyncMock()
    mock_state.clear = AsyncMock(side_effect=lambda: state_store.clear())

    await start_link_uid(mock_call, state=mock_state, user_lang="en")

    # Verify no new message was sent; caption was edited in-place
    assert mock_card_msg.edit_caption.called is True
    assert mock_card_msg.answer.called is False
    assert mock_call.answer.called is True
    assert state_store["target_message_id"] == 5555
    assert state_store["target_chat_id"] == 987654321

    # 2. Player sends UID "2208927823"
    user_msg = MagicMock(spec=Message)
    user_msg.text = "2208927823"
    user_msg.from_user = MagicMock()
    user_msg.from_user.id = 111222333
    user_msg.chat = MagicMock()
    user_msg.chat.id = 987654321
    user_msg.delete = AsyncMock()
    user_msg.answer = AsyncMock()
    user_msg.bot = mock_bot

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_result.scalar.return_value = 0
    mock_session.execute.return_value = mock_result

    mock_user = MagicMock(spec=User)
    mock_user.telegram_id = 111222333
    mock_user.role = UserRole.USER
    mock_user.game_balance = Decimal("0.00")
    mock_user.win_balance = Decimal("0.00")

    fake_garena_profile = {
        "uid": "2208927823",
        "username": "ᎢʟㅤᎻᴀʀsʜ",
        "region": "IND",
        "level": 67,
        "likes": 17452,
        "avatar_id": 902026006,
        "banner_id": 901000254,
        "guild_name": "ᎢʜᴜɴᴅᴇʀᏞᴏʀᴅㅤ",
        "full_data": {"basicInfo": {"nickname": "ᎢʟㅤᎻᴀʀsʜ", "level": 67}},
    }

    with patch("src.handlers.start.ff_client.get_player_info", AsyncMock(return_value=fake_garena_profile)):
        await process_link_uid(user_msg, state=mock_state, session=mock_session, db_user=mock_user, user_lang="en")

    # Verify user message was immediately deleted
    assert user_msg.delete.called is True
    # Verify no new message was answered
    assert user_msg.answer.called is False
    # Verify target message was updated via edit_message_caption
    assert mock_bot.edit_message_caption.called is True
    last_caption = mock_bot.edit_message_caption.call_args.kwargs["caption"]
    assert any(w in last_caption for w in ["ACCOUNT OFFICIALLY BOUND", "Successfully Linked", "Sᴜᴄᴄᴇssғᴜʟʟʏ Lɪɴᴋᴇᴅ", "Bᴏᴜɴᴅ"])
    assert "ᎢʟㅤᎻᴀʀsʜ" in last_caption

    # Verify user object updated and committed to db
    assert mock_user.ff_uid == "2208927823"
    assert mock_user.ff_ign == "ᎢʟㅤᎻᴀʀsʜ"
    assert mock_user.ff_level == 67
    assert mock_user.ff_data == fake_garena_profile["full_data"]
    assert mock_session.commit.called is True


@pytest.mark.asyncio
async def test_freefire_api_client_garena_401_fallback():
    """Verify that when official Garena endpoint returns 401 or None, client seamlessly falls back to FFxAPI."""
    from unittest.mock import patch, AsyncMock
    from src.services.freefire_api import FreeFireAPIClient

    client = FreeFireAPIClient()
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.setex.return_value = True

    fake_ffx_profile = {
        "uid": "865295480",
        "username": "Lucky784242S",
        "region": "IND",
        "level": 53,
        "likes": 370,
        "exp": 442583,
        "rank": 0,
        "br_max_rank": 301,
        "cs_rank": 0,
        "cs_max_rank": 301,
        "avatar_id": "Octopus",
        "banner_id": "War Fury",
        "guild_name": None,
        "full_data": {"identity": {"username": "Lucky784242S"}},
    }

    with patch.object(client, "get_redis", AsyncMock(return_value=mock_redis)), \
         patch.object(client, "fetch_direct_garena", AsyncMock(return_value=None)) as mock_garena, \
         patch.object(client, "fetch_ffx_api", AsyncMock(return_value=fake_ffx_profile)) as mock_ffx:
        
        result = await client.get_player_info("865295480")

        assert mock_garena.called is True
        assert mock_ffx.called is True
        assert result is not None
        assert result["username"] == "Lucky784242S"
        assert result["level"] == 53
        assert result["uid"] == "865295480"


@pytest.mark.asyncio
async def test_handle_inline_query_frontend_formatting():
    """Verify inline query frontend formatting: 12 images, small-caps title, description, and buttons."""
    from src.handlers.inline_query import handle_inline_query, THUMBNAIL_URLS
    from src.database.models import Tournament, MatchType, TeamFormat, TournamentStatus
    from aiogram.types import InlineQuery
    from datetime import datetime, timezone, timedelta
    from unittest.mock import patch, MagicMock, AsyncMock

    assert len(THUMBNAIL_URLS) == 12
    assert "https://i.postimg.cc/MTG2cBSt/IMG-20240307-233659-674.jpg" in THUMBNAIL_URLS
    assert "https://i.postimg.cc/9MB02ZBp/IMG-20240307-233703-214.jpg" in THUMBNAIL_URLS

    mock_iq = MagicMock(spec=InlineQuery)
    mock_iq.query = ""
    mock_iq.answer = AsyncMock()

    mock_t = MagicMock(spec=Tournament)
    mock_t.id = 1
    mock_t.match_type = MatchType.BATTLE_ROYALE
    mock_t.team_format = TeamFormat.SQUAD
    mock_t.entry_fee = Decimal("20.00")
    mock_t.total_slots = 48
    mock_t.filled_slots = 1
    mock_t.status = TournamentStatus.OPEN
    mock_t.start_time = datetime.now(timezone.utc) + timedelta(hours=1, minutes=30)

    mock_session = AsyncMock()

    with patch("src.services.tournament_service.TournamentService.list_active_tournaments", AsyncMock(return_value=[mock_t])):
        await handle_inline_query(mock_iq, session=mock_session)

    assert mock_iq.answer.called is True
    results = mock_iq.answer.call_args.kwargs["results"]
    assert len(results) == 1
    res = results[0]

    # Verify small caps title
    assert "🔥 Bᴀᴛᴛʟᴇ Rᴏʏᴀʟᴇ | #0001" in res.title
    # Verify formatted small caps description
    assert "• Sᴇᴀᴛs » 1/48 Oᴄᴄᴜᴘɪᴇᴅ" in res.description
    assert "• Eɴᴛᴇʀʏ Fᴇᴇs » 20 Pᴏɪɴᴛs" in res.description
    assert "• Sᴛᴀʀᴛs Aғᴛᴇʀ »" in res.description
    # Verify image thumbnail
    assert res.thumbnail_url == THUMBNAIL_URLS[0]
    # Verify input message content
    assert res.input_message_content.message_text == "#1"
    # Verify buttons
    buttons = res.reply_markup.inline_keyboard[0]
    assert len(buttons) == 1
    assert "🏆 Wɪɴɴᴇʀ Pʀɪᴄᴇ" in buttons[0].text


@pytest.mark.asyncio
async def test_seat_view_on_photo_message():
    """Verify that clicking Join Tournament on a photo message edits caption with tournament card box and single-row emoji buttons."""
    from src.handlers.seat_picker import handle_seat_view
    from src.database.models import Tournament, MatchType, TeamFormat, TournamentStatus
    from aiogram.types import CallbackQuery, Message, PhotoSize, User as TgUser
    from aiogram.exceptions import TelegramBadRequest
    from datetime import datetime, timezone
    from unittest.mock import patch, MagicMock, AsyncMock

    mock_call = MagicMock(spec=CallbackQuery)
    mock_call.data = "seat_view:1"
    mock_call.from_user = MagicMock(spec=TgUser)
    mock_call.from_user.id = 123456
    mock_call.answer = AsyncMock()

    mock_msg = MagicMock(spec=Message)
    # Simulate photo message:
    mock_msg.photo = [MagicMock(spec=PhotoSize)]
    mock_msg.edit_caption = AsyncMock()
    # If edit_text were called on a photo message, Telegram raises:
    mock_msg.edit_text = AsyncMock(side_effect=TelegramBadRequest(method="editMessageText", message="there is no text in the message to edit"))
    mock_call.message = mock_msg

    mock_tourn = MagicMock(spec=Tournament)
    mock_tourn.id = 1
    mock_tourn.match_type = MatchType.CLASH_SQUAD
    mock_tourn.team_format = TeamFormat.SQUAD
    mock_tourn.map_name = "Purgatory"
    mock_tourn.gun_attributes = False
    mock_tourn.entry_fee = Decimal("30.00")
    mock_tourn.filled_slots = 0
    mock_tourn.total_slots = 8
    mock_tourn.status = TournamentStatus.OPEN
    mock_tourn.start_time = datetime.now(timezone.utc)

    matrix_data = {
        "mode": "clash_squad",
        "title": "CS Match",
        "filled_slots": 0,
        "total_slots": 8,
        "entry_fee": 30.0,
        "team_alpha": {
            "name": "Team Alpha (Red)",
            "is_full": False,
            "is_filling_fast": False,
            "occupied_count": 0,
            "max_slots": 4,
            "slots": [{"slot_number": i, "status": "open", "ign": ""} for i in range(1, 5)],
        },
        "team_beta": {
            "name": "Team Beta (Blue)",
            "is_full": False,
            "is_filling_fast": False,
            "occupied_count": 0,
            "max_slots": 4,
            "slots": [{"slot_number": i, "status": "open", "ign": ""} for i in range(5, 9)],
        },
    }

    mock_user = MagicMock()
    mock_user.ff_uid = "12345678"
    mock_session = AsyncMock()
    mock_session.get.return_value = mock_user

    with patch("src.services.tournament_service.TournamentService.get_tournament_by_id", AsyncMock(return_value=mock_tourn)):
        with patch("src.services.tournament_service.TournamentService.get_seating_matrix", AsyncMock(return_value=matrix_data)):
            await handle_seat_view(mock_call, session=mock_session, redis=AsyncMock())

    assert mock_msg.edit_caption.called is True
    assert mock_call.answer.called is True

    from src.utils.typography import to_small_caps

    caption = mock_msg.edit_caption.call_args.kwargs["caption"]
    assert to_small_caps("Team Alpha") in caption
    assert to_small_caps("Team Beta") in caption

    kb = mock_msg.edit_caption.call_args.kwargs["reply_markup"]
    # Row 0: Side-by-side headers
    assert "🟡" in kb.inline_keyboard[0][0].text
    assert to_small_caps("Team Alpha") in kb.inline_keyboard[0][0].text
    assert "🔵" in kb.inline_keyboard[0][1].text
    assert to_small_caps("Team Beta") in kb.inline_keyboard[0][1].text
    # Row 1: 2 Alpha + 2 Beta slots (4 buttons wide)
    assert len(kb.inline_keyboard[1]) == 4
    assert [b.text for b in kb.inline_keyboard[1]] == ["\U0001f7e2", "\U0001f7e2", "\U0001f7e2", "\U0001f7e2"]
    # Row 2: 2 Alpha + 2 Beta slots (4 buttons wide)
    assert len(kb.inline_keyboard[2]) == 4
    assert [b.text for b in kb.inline_keyboard[2]] == ["\U0001f7e2", "\U0001f7e2", "\U0001f7e2", "\U0001f7e2"]









