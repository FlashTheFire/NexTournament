import sys
import os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from src.utils.typography import to_small_caps, box_frame
from src.utils.i18n import t, get_supported_languages
from src.services.card_generator import generate_profile_card


import pytest

@pytest.mark.asyncio
async def test_phase2_suite():
    # 1. Typography test
    sc = to_small_caps("Free Fire Tournament")
    assert sc == "Fʀᴇᴇ Fɪʀᴇ Tᴏᴜʀɴᴀᴍᴇɴᴛ", f"Expected 'Fʀᴇᴇ Fɪʀᴇ Tᴏᴜʀɴᴀᴍᴇɴᴛ', got '{sc}'"
    
    bf = box_frame("Match Details", [("Match Type", "BR-Match"), ("Join Charge", "50 Points")])
    assert "Fʀᴇᴇ" not in bf # just checking box_frame header
    assert "Mᴀᴛᴄʜ Tʏᴘᴇ" in bf

    # 2. i18n test across 6 languages
    langs = get_supported_languages()
    assert len(langs) == 6, f"Expected 6 languages, got {len(langs)}"
    for lang in langs:
        val = t("btn_tournament", lang=lang)
        assert len(val) > 0, f"Missing translation for {lang}"

    # 3. Card Generator test
    card_buf = await generate_profile_card(
        ign="Mohin7KX",
        uid="11510698353",
        level=51,
        region="IND",
        matches=12,
        win_rate=75.0,
        game_bal=250.0,
        win_bal=500.0
    )
    data = card_buf.getvalue()
    assert len(data) > 1000, f"Generated card is too small: {len(data)} bytes"
    assert data[:8] == b'\x89PNG\r\n\x1a\n', "Output is not valid PNG format"

    # 4. OB55 Free Fire Direct Protobuf Engine test
    from src.services.freefire_api import (
        encrypt_garena_payload,
        make_garena_headers,
        parse_protobuf_player_info,
    )
    from src.proto.data_pb2 import AccountPersonalShowInfo

    # Encryption test
    enc_payload = encrypt_garena_payload(11510698353)
    assert len(enc_payload) % 16 == 0, "AES encrypted payload must be block-aligned to 16 bytes"
    assert len(enc_payload) > 0

    # Headers test
    hdrs = make_garena_headers("mock_jwt_token_123")
    assert hdrs["Authorization"] == "Bearer mock_jwt_token_123"
    assert hdrs["Releaseversion"] == "OB55"

    # Protobuf decode test
    raw_account = AccountPersonalShowInfo()
    raw_account.basic_info.account_id = 11510698353
    raw_account.basic_info.nickname = "Mohin7KX"
    raw_account.basic_info.region = "IND"
    raw_account.basic_info.level = 51
    raw_account.basic_info.liked = 120
    raw_account.clan_basic_info.clan_name = "NexTournament"

    parsed = parse_protobuf_player_info(raw_account.SerializeToString(), "11510698353")
    assert parsed is not None
    assert parsed["username"] == "Mohin7KX"
    assert parsed["level"] == 51
    assert parsed["region"] == "IND"
    assert parsed["guild_name"] == "NexTournament"
    assert "full_data" in parsed
    assert "basicInfo" in parsed["full_data"]
    assert parsed["full_data"]["basicInfo"]["nickname"] == "Mohin7KX"
    assert parsed["full_data"]["clanBasicInfo"]["clanName"] == "NexTournament"

    # 5. User model ff_data JSONB storage test
    from src.database.models import User
    u = User(telegram_id=123456789, first_name="TestUser", ff_uid="11510698353", ff_data=parsed["full_data"])
    assert u.ff_data is not None
    assert u.ff_data["basicInfo"]["nickname"] == "Mohin7KX"

    print("ALL PHASE 2 UNIT TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    asyncio.run(test_phase2_suite())
