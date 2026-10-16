# 🎨 UI/UX & Typography Style Guide
## NexTournament v2.0 — Aesthetic Design System & Small-Caps Typography

---

### 1. Small-Caps Typography Standard

NexTournament v2.0 enforces a signature **Small-Caps Title-Case Typography** across all messages, inline buttons, and status alerts.

#### 1.1 Algorithmic Rule
Every word is title-cased:
- The **first character** remains standard uppercase Latin (`A-Z`).
- All **subsequent alphabetical characters** are translated to their corresponding Unicode small-capital phonetic glyphs.

#### 1.2 Character Mapping Table
```
a -> ᴀ    b -> ʙ    c -> ᴄ    d -> ᴅ    e -> ᴇ    f -> ғ    g -> ɢ
h -> ʜ    i -> ɪ    j -> ᴊ    k -> ᴋ    l -> ʟ    m -> ᴍ    n -> ɴ
o -> ᴏ    p -> ᴘ    q -> ǫ    r -> ʀ    s -> s    t -> ᴛ    u -> ᴜ
v -> ᴠ    w -> ᴡ    x -> x    y -> ʏ    z -> ᴢ
```

#### 1.3 Implementation Utility (`src/utils/typography.py`)
```python
SMALL_CAPS_MAP = {
    'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ',
    'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ',
    'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 'u': 'ᴜ',
    'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ'
}

def to_small_caps(text: str) -> str:
    """Converts standard text to title-cased small caps typography."""
    words = text.split(" ")
    converted_words = []
    for word in words:
        if not word:
            continue
        first = word[0].upper()
        rest = "".join(SMALL_CAPS_MAP.get(c.lower(), c) for c in word[1:])
        converted_words.append(first + rest)
    return " ".join(converted_words)

# Examples:
# to_small_caps("Tournament Id") -> "Tᴏᴜʀɴᴀᴍᴇɴᴛ Iᴅ"
# to_small_caps("Join Charge")   -> "Jᴏɪɴ Cʜᴀʀɢᴇ"
# to_small_caps("Player Limit")  -> "Pʟᴀʏᴇʀ Lɪᴍɪᴛ"
```

---

### 2. Box-Frame Border Standards

All primary information displays utilize Unicode box-drawing characters for clean visual hierarchy and contrast:

```
╭───────────────────────╮
│  🔥 Fʀᴇᴇ Fɪʀᴇ Tᴏᴜʀɴᴀᴍᴇɴᴛ  │
╰───────────────────────╯

 ❒ Tᴏᴜʀɴᴀᴍᴇɴᴛ Iᴅ    »  #10492
 ❒ Cᴏᴜsᴛᴏᴍ Tʏᴘᴇ     »  Bʀ-Mᴀᴛᴄʜ (Sǫᴜᴀᴅ)
 ❒ Mᴀᴘ Nᴀᴍᴇ         »  Bᴇʀᴍᴜᴅᴀ
 ❒ Gᴜɴ Aᴛᴛʀɪʙᴜᴛᴇs   »  Oғғ
 ❒ Jᴏɪɴɪɴɢ Cʜᴀʀɢᴇ  »  ₹50.00 Pᴏɪɴᴛs
 ❒ Pʟᴀʏᴇʀ Lɪᴍɪᴛ       »  32/48 Pʟᴀʏᴇʀs
 ❒ Jᴏɪɴ Tɪᴍɪɴɢ         »  07:45 PM
 ❒ Sᴛᴀʀᴛ Tɪᴍɪɴɢ      »  08:00 PM

💬 Cᴜsᴛᴏᴍ Iᴅ & Pᴀss Wɪʟʟ Bᴇ Pʀᴏᴠɪᴅᴇᴅ 15 Mɪɴᴜᴛᴇs Bᴇғᴏʀᴇ Tʜᴇ Mᴀᴛᴄʜ.
```

---

### 3. Persistent Menu Keyboards & Interactive Layouts

#### 3.1 Persistent User Main Keyboard
```python
ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛒 Tᴏᴜʀɴᴀᴍᴇɴᴛ"), KeyboardButton(text="💰 Dᴇᴘᴏsɪᴛ")],
        [KeyboardButton(text="👨‍💻 Pʀᴏғɪʟᴇ"), KeyboardButton(text="📊 Lᴇᴀᴅᴇʀʙᴏᴀʀᴅ"), KeyboardButton(text="🪙 Wɪᴛʜᴅʀᴀᴡ")],
        [KeyboardButton(text="👤 Sᴜᴘᴘᴏʀᴛ"), KeyboardButton(text="⚙️ Sᴇᴛᴛɪɴɢs")]
    ],
    resize_keyboard=True
)
```

#### 3.2 Persistent Admin / Staff Keyboard
```python
ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Cʀᴇᴀᴛᴇ Mᴀᴛᴄʜ"), KeyboardButton(text="📡 Bʀᴏᴀᴅᴄᴀsᴛ Rᴏᴏᴍ ID")],
        [KeyboardButton(text="🏆 Dᴇᴄʟᴀʀᴇ Rᴇsᴜʟᴛs"), KeyboardButton(text="📸 Rᴇsᴜʟᴛ Pʀᴏᴏғ Qᴜᴇᴜᴇ")],
        [KeyboardButton(text="💳 Dᴇᴘᴏsɪᴛ Qᴜᴇᴜᴇ"), KeyboardButton(text="💸 Wɪᴛʜᴅʀᴀᴡ Qᴜᴇᴜᴇ")],
        [KeyboardButton(text="⚙️ Aᴅᴍɪɴ Pᴀɴᴇʟ"), KeyboardButton(text="🔙 Usᴇʀ Mᴏᴅᴇ")]
    ],
    resize_keyboard=True
)
```

---

### 4. Multi-Language Localization (English, Hindi, Telugu, Marathi, Bengali, Indonesian)

Users can toggle their preferred language via `⚙️ Sᴇᴛᴛɪɴɢs` $\rightarrow$ `🌐 Lᴀɴɢᴜᴀɢᴇ`.

| Key | English (`en`) | Hindi (`hi`) | Telugu (`te`) | Marathi (`mr`) | Bengali (`bn`) | Indonesian (`id`) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `btn_tournament` | `🛒 Tᴏᴜʀɴᴀᴍᴇɴᴛ` | `🛒 टूर्नामेंट` | `🛒 టోర్నమెంట్` | `🛒 स्पर्धा` | `🛒 টুর্নামেন্ট` | `🛒 Turnamen` |
| `btn_deposit` | `💰 Dᴇᴘᴏsɪᴛ` | `💰 पैसे जोड़ें` | `💰 డిపాజిట్` | `💰 ठेव जमा` | `💰 জমা দিন` | `💰 Deposit` |
| `btn_withdraw` | `🪙 Wɪᴛʜᴅʀᴀᴡ` | `🪙 पैसे निकालें` | `🪙 ఉపసంహరణ` | `🪙 पैसे काढा` | `🪙 টাকা তুলুন` | `🪙 Penarikan` |
| `seat_reserved` | `🎉 Seat #%d reserved!` | `🎉 सीट #%d बुक हो गई!` | `🎉 సీటు #%d రిజర్వ్ అయింది!` | `🎉 जागा #%d आरक्षित केली!` | `🎉 আসন #%d সফলভাবে বুক হয়েছে!` | `🎉 Kursi #%d berhasil dipesan!` |

---

### 5. Dynamic Esports Image Cards (NexNum & NexCreator Neo-Brutalist Engine)

Profile cards and Victory (Booyah) announcement banners utilize the high-energy **Neo-Brutalist & Neo-Industrial Cyberpunk** design system inspired directly by [NexNum OG Engine](https://nexnum.in/api/og) and [NexCreator Engine](file:///D:/Nex-Projects/NexCreator/tools/image-engine-mcp):

#### 5.1 Card Specification & Palette
- **Dimensions**: `1200 x 630 px` (High-definition 16:9 Esports & Telegram Webview Landscape)
- **Deep Void Background**: `#06090E` with 40px neo-industrial grid-lines
- **Solid Hero Accent**: **Fluorescent Yellow-Green / Electric Lime (`#CCFF00`)**
- **Secondary Accent**: **Matrix Cyan (`#00E5FF`)**
- **Tactile Surface Panels**: `#0D131C` with `rgba(255, 255, 255, 0.12)` border and 3px brutalist drop-shadows
- **High-Contrast Text**: Jet Black `#06090E` on Electric Lime; Pure White `#FFFFFF` and Muted `#A5AFBE` on Void

#### 5.2 Signature Elements
1. **Corner Crosshairs (`+`)**: Positioned at all four outer corners in `#CCFF00` Consolas/monospace.
2. **Technical HUD Header**: Status pulse dot + category label + real-time telemetry pills (`[ LATENCY: <50MS ] [ ANTI-CHEAT: SECURE ] [ REGION: IND ]`).
3. **Hero Solid Block of Fluorescent Yellow-Green (`#CCFF00`)**:
   - Massive 1104px wide tactile container filled with pure solid `#CCFF00`.
   - Brutalist offset drop-shadow (`+5px, +5px` in `#00E5FF`).
   - Ultra-bold Jet Black (`#06090E`) typography for player IGN or Champion team.
   - Contrast capsule pills for UID and tournament rankings.
4. **4-Column Tactile Stat Grid**:
   - `[01] MATCHES PLAYED`, `[02] COMBAT VICTORY`, `[03] GAME BALANCE`, `[04] WINNING VAULT`.
   - Left-accented colored border (`#CCFF00` / `#00E5FF`).
5. **Fintech Dashboard Footer Bar**:
   - Ledger integrity hash and live bot status dot.
   - Solid Block Tactile CTA Button: `ACCESS CONSOLE >` / `CLAIM PRIZE >` in `#CCFF00` with Matrix Cyan drop-shadow.

