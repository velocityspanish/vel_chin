"""VELOCITY CHINESE - language pack, brand and motion design constants."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = BASE_DIR / "output"
LESSONS_DIR = OUTPUT_DIR / "lessons"
HISTORY_DIR = OUTPUT_DIR / "history"
SCENE_DIR = BASE_DIR / "scene"

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

# ---------------------------------------------------------------- brand

BRAND = "VELOCITY CHINESE"
BRAND_LOCKUP_TOP = "VELOCITY"
BRAND_LOCKUP_BOTTOM = "CHINESE"
HANDLE = "@velocitychinese"
MASCOT_NAME = "Velo"

# ==== LANGUAGE PACK START ====
LANGUAGE = {
    "code": "zh",
    "name": "Chinese",
    "native_name": "中文",
    "history_key": "chinese",
    "english_voice": "en-US-AvaNeural",
    "english_fallback_voice": "en-US-GuyNeural",
    "native_voice": "zh-CN-XiaoxiaoNeural",
    "native_fallback_voice": "zh-CN-YunxiNeural",
    "native_engine": "edge",
    "native_lang_code": "zh",
    "english_rate": "-2%",
    "native_rate": "-6%",
    "english_pitch": "+0Hz",
    "native_pitch": "+0Hz",
    "native_label": "中文",
    "translit_label": "PINYIN",
    "greeting": "你好！",
    "encouragement": "太棒了！",
    "rtl": False,
    "char_tiles": True,
    "script_font": "NotoSansSC-Bold.ttf",
}
# ==== LANGUAGE PACK END ====

AI_MODEL = os.getenv("AI_MODEL", "gemini-fast")
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")

# ---------------------------------------------------------------- timing (seconds)

INTRO_DURATION = 4.0
OUTRO_DURATION = 5.2
EN_CARD_IN = 0.55
GAP_EN_NATIVE = 0.5
NATIVE_CARD_LEAD = 0.35
GAP_BEFORE_REPEAT = 0.8
TAIL_HOLD = 1.4
MAX_REEL_DURATION = 88.0

# ---------------------------------------------------------------- palette

INK = "#3C3C3C"
MUTED = "#8A8A8A"
CREAM = "#FFF8E7"
GREEN = "#58CC02"
GREEN_DARK = "#46A302"
GREEN_DEEP = "#3D8F00"
BLUE = "#1CB0F6"
PURPLE = "#A560E8"
ORANGE = "#FF7A00"
RED = "#FF4B4B"
YELLOW = "#F5A700"
TEAL = "#00A889"
PINK = "#E056A0"

PALETTE = [GREEN, BLUE, PURPLE, ORANGE, RED, YELLOW, TEAL, PINK]

# ---------------------------------------------------------------- categories
# (english, native, icon, accent)

# ==== CATEGORY TABLE START ====
CATEGORY_TABLE = [
    ("Motivation", "动力", "rocket", "#A560E8"),
    ("Love", "爱情", "heart", "#FF4B4B"),
    ("Success", "成功", "trophy", "#F5A700"),
    ("Wisdom", "智慧", "book", "#A560E8"),
    ("Happiness", "幸福", "smile", "#F5A700"),
    ("Self Improvement", "自我提升", "leaf", "#58CC02"),
    ("Gratitude", "感恩", "heart", "#FF7A00"),
    ("Friendship", "友谊", "users", "#00A889"),
    ("Hope", "希望", "sun", "#FF7A00"),
    ("Creativity", "创造力", "palette", "#E056A0"),
    ("Inner Peace", "内心平静", "lotus", "#00A889"),
    ("Confidence", "自信", "shield", "#1CB0F6"),
    ("Perseverance", "毅力", "mountain", "#FF7A00"),
    ("Inspiration", "灵感", "sparkles", "#A560E8"),
    ("Positive Life", "积极生活", "sun", "#58CC02"),
    ("Courage", "勇气", "shield", "#FF4B4B"),
    ("Kindness", "善良", "heart", "#E056A0"),
    ("Patience", "耐心", "hourglass", "#00A889"),
    ("Forgiveness", "宽恕", "hands", "#FF7A00"),
    ("Strength", "力量", "dumbbell", "#FF4B4B"),
    ("Joy", "快乐", "smile", "#F5A700"),
    ("Balance", "平衡", "scale", "#00A889"),
    ("Growth", "成长", "sprout", "#58CC02"),
    ("Purpose", "目标", "target", "#A560E8"),
    ("Mindfulness", "正念", "lotus", "#00A889"),
]
# ==== CATEGORY TABLE END ====

CATEGORIES = [c[0] for c in CATEGORY_TABLE]
CATEGORIES_NATIVE = {c[0]: c[1] for c in CATEGORY_TABLE}
CATEGORY_META = {c[0]: {"native": c[1], "icon": c[2], "accent": c[3]} for c in CATEGORY_TABLE}
MAX_RECENT_CATEGORIES = 25

# ==== HASHTAGS START ====
HASHTAGS = [
    "#learnchinese",
    "#chineselessons",
    "#chineseforbeginners",
    "#languagelearning",
    "#chinesevocabulary",
    "#velocitychinese",
    "#dailychinese",
    "#chinese",
    "#learnlanguages",
    "#speakchinese",
    "#bilingual",
    "#languagetips",
]
# ==== HASHTAGS END ====
