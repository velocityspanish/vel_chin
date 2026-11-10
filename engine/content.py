"""AI phrase generation with permanent no-repeat history."""

from __future__ import annotations

import json
import random
import time
from datetime import datetime

import requests

import config
from config import CATEGORIES, CATEGORIES_NATIVE, HISTORY_DIR, MAX_RECENT_CATEGORIES

PHRASE_HISTORY_FILE = HISTORY_DIR / "all_generated_phrases.json"
RECENT_CATEGORIES_FILE = HISTORY_DIR / "recent_categories.json"

PHRASE_KEY = config.LANGUAGE["history_key"]
LANGUAGE_NAME = config.LANGUAGE["name"]
NATIVE_NAME = config.LANGUAGE["native_name"]

# ==== FALLBACK PHRASES START ====
FALLBACK_PHRASES = [
    {"english": "Believe in yourself.", "native": "相信自己。", "transliteration": ""},
    {"english": "You are capable of amazing things.", "native": "你有能力成就惊人的事情。", "transliteration": ""},
    {"english": "Dream big, start small.", "native": "胸怀大志，从小做起。", "transliteration": ""},
    {"english": "Your future is created by your actions.", "native": "你的未来由你的行动创造。", "transliteration": ""},
    {"english": "Never give up on your dreams.", "native": "永不放弃梦想。", "transliteration": ""},
    {"english": "Small steps lead to big changes.", "native": "小步引领大变化。", "transliteration": ""},
    {"english": "You are stronger than you think.", "native": "你比自己想象的更强大。", "transliteration": ""},
    {"english": "Love yourself first.", "native": "先爱自己。", "transliteration": ""},
    {"english": "Love makes everything possible.", "native": "爱使一切成为可能。", "transliteration": ""},
    {"english": "My heart beats for you.", "native": "我的心为你跳动。", "transliteration": ""},
    {"english": "You are my everything.", "native": "你是我的一切。", "transliteration": ""},
    {"english": "Together forever, hand in hand.", "native": "永远在一起，手牵手。", "transliteration": ""},
    {"english": "Success comes from hard work.", "native": "成功来自努力。", "transliteration": ""},
    {"english": "Keep going, you're getting there.", "native": "继续前进，你快到了。", "transliteration": ""},
    {"english": "Winners never quit.", "native": "赢家永不放弃。", "transliteration": ""},
    {"english": "Your effort will pay off.", "native": "你的努力会有回报。", "transliteration": ""},
    {"english": "Knowledge is power.", "native": "知识就是力量。", "transliteration": ""},
    {"english": "Learn from yesterday, live for today.", "native": "借鉴昨天，活在今天。", "transliteration": ""},
    {"english": "Think before you act.", "native": "三思而后行。", "transliteration": ""},
    {"english": "Experience is the best teacher.", "native": "经验是最好的老师。", "transliteration": ""},
    {"english": "Happiness is a choice.", "native": "快乐是一种选择。", "transliteration": ""},
    {"english": "Find joy in the little things.", "native": "在小事中寻找快乐。", "transliteration": ""},
    {"english": "Smile, it makes others happy.", "native": "微笑，让别人也开心。", "transliteration": ""},
    {"english": "Today is a gift.", "native": "今天是礼物。", "transliteration": ""},
    {"english": "Be better than yesterday.", "native": "比昨天更好。", "transliteration": ""},
    {"english": "Grow through what you go through.", "native": "在经历中成长。", "transliteration": ""},
    {"english": "Invest in yourself daily.", "native": "每天投资自己。", "transliteration": ""},
    {"english": "Thank you for everything.", "native": "谢谢你的一切。", "transliteration": ""},
    {"english": "I appreciate your help.", "native": "我感激你的帮助。", "transliteration": ""},
    {"english": "Grateful for this moment.", "native": "感激这一刻。", "transliteration": ""},
    {"english": "Friends forever, no matter what.", "native": "永远是朋友，无论如何。", "transliteration": ""},
    {"english": "You are my best friend.", "native": "你是我最好的朋友。", "transliteration": ""},
    {"english": "True friends stick together.", "native": "真正的朋友在一起。", "transliteration": ""},
    {"english": "There is always hope.", "native": "总有希望。", "transliteration": ""},
    {"english": "Better days are coming.", "native": "更好的日子会来。", "transliteration": ""},
    {"english": "Keep faith, keep going.", "native": "保持信念，继续前进。", "transliteration": ""},
    {"english": "Create something beautiful today.", "native": "今天创造美好的东西。", "transliteration": ""},
    {"english": "Your imagination is unlimited.", "native": "你的想象力无限。", "transliteration": ""},
    {"english": "Art comes from the heart.", "native": "艺术来自内心。", "transliteration": ""},
    {"english": "Express yourself freely.", "native": "自由表达自己。", "transliteration": ""},
    {"english": "Innovation starts with curiosity.", "native": "创新始于好奇心。", "transliteration": ""},
    {"english": "Find peace within yourself.", "native": "在内心寻找平静。", "transliteration": ""},
    {"english": "Breathe, relax, let go.", "native": "呼吸，放松，放下。", "transliteration": ""},
    {"english": "Calm mind, happy heart.", "native": "心静，心喜。", "transliteration": ""},
    {"english": "You are enough, just as you are.", "native": "你足够了，就做你自己。", "transliteration": ""},
    {"english": "Stand tall, speak up.", "native": "挺直腰板，大声说话。", "transliteration": ""},
    {"english": "Believe in your abilities.", "native": "相信你的能力。", "transliteration": ""},
    {"english": "Never give up, keep pushing.", "native": "永不放弃，继续前进。", "transliteration": ""},
    {"english": "Storms make trees take deeper roots.", "native": "风暴使树根更深。", "transliteration": ""},
    {"english": "Patience and persistence win.", "native": "耐心和坚持获胜。", "transliteration": ""},
    {"english": "Let your light shine bright.", "native": "让你的光芒闪耀。", "transliteration": ""},
    {"english": "Inspire others by your actions.", "native": "用行动激励他人。", "transliteration": ""},
    {"english": "Be the change you want to see.", "native": "成为你想看到的改变。", "transliteration": ""},
    {"english": "Choose positivity every day.", "native": "每天选择积极。", "transliteration": ""},
    {"english": "Good vibes only.", "native": "只要好氛围。", "transliteration": ""},
    {"english": "Life is what you make it.", "native": "生活由你创造。", "transliteration": ""},
    {"english": "Be brave, take the first step.", "native": "勇敢，迈出第一步。", "transliteration": ""},
    {"english": "Courage is not the absence of fear.", "native": "勇气不是没有恐惧。", "transliteration": ""},
    {"english": "Face your fears head on.", "native": "直面恐惧。", "transliteration": ""},
    {"english": "Be kind to everyone you meet.", "native": "善待你遇到的每个人。", "transliteration": ""},
    {"english": "Kindness costs nothing, means everything.", "native": "善良无需代价，意义非凡。", "transliteration": ""},
    {"english": "Spread kindness wherever you go.", "native": "无论去哪里都传播善良。", "transliteration": ""},
    {"english": "Good things take time.", "native": "好事需要时间。", "transliteration": ""},
    {"english": "Wait patiently, trust the process.", "native": "耐心等待，相信过程。", "transliteration": ""},
    {"english": "Rome wasn't built in a day.", "native": "罗马不是一天建成的。", "transliteration": ""},
    {"english": "Forgive and set yourself free.", "native": "原谅并释放自己。", "transliteration": ""},
    {"english": "Let go of grudges, find peace.", "native": "放下怨恨，找到平静。", "transliteration": ""},
    {"english": "Forgiveness is a gift to yourself.", "native": "原谅是给自己的礼物。", "transliteration": ""},
    {"english": "You are stronger than you know.", "native": "你比自己知道的更强大。", "transliteration": ""},
    {"english": "Inner strength comes from within.", "native": "内在力量来自内心。", "transliteration": ""},
    {"english": "Challenges make you stronger.", "native": "挑战让你更强大。", "transliteration": ""},
    {"english": "Find joy in every moment.", "native": "在每一刻找到快乐。", "transliteration": ""},
    {"english": "Joy is contagious, spread it.", "native": "快乐会传染，传播它。", "transliteration": ""},
    {"english": "Dance like nobody's watching.", "native": "像没人看着一样跳舞。", "transliteration": ""},
    {"english": "Find balance in your life.", "native": "在生活中找到平衡。", "transliteration": ""},
    {"english": "Work hard, rest well.", "native": "努力工作，好好休息。", "transliteration": ""},
    {"english": "Too much of anything is not good.", "native": "过犹不及。", "transliteration": ""},
    {"english": "Growth happens outside your comfort zone.", "native": "成长发生在舒适区外。", "transliteration": ""},
    {"english": "Embrace change, grow stronger.", "native": "拥抱改变，变得更强大。", "transliteration": ""},
    {"english": "Every challenge is a chance to grow.", "native": "每个挑战都是成长机会。", "transliteration": ""},
    {"english": "Find your purpose, follow it.", "native": "找到你的目标，追随它。", "transliteration": ""},
    {"english": "Your life has meaning.", "native": "你的生命有意义。", "transliteration": ""},
    {"english": "Live with intention, not accident.", "native": "有目的地生活，不是偶然。", "transliteration": ""},
    {"english": "Be present in this moment.", "native": "活在当下这一刻。", "transliteration": ""},
    {"english": "Breathe deeply, stay grounded.", "native": "深呼吸，保持踏实。", "transliteration": ""},
    {"english": "Notice the little things around you.", "native": "注意周围的小事。", "transliteration": ""},
    {"english": "Where is the train station?", "native": "火车站在哪里？", "transliteration": "Huǒchēzhàn zài nǎlǐ?"},
    {"english": "I would like a coffee, please.", "native": "我想要一杯咖啡。", "transliteration": "Wǒ xiǎng yào yì bēi kāfēi."},
    {"english": "How much does this cost?", "native": "这个多少钱？", "transliteration": "Zhège duōshǎo qián?"},
    {"english": "Please help me.", "native": "请帮帮我。", "transliteration": "Qǐng bāng bang wǒ."},
    {"english": "I don't understand.", "native": "我听不懂。", "transliteration": "Wǒ tīng bù dǒng."},
    {"english": "Please speak slowly.", "native": "请说慢一点。", "transliteration": "Qǐng shuō màn yìdiǎn."},
    {"english": "The weather is beautiful today.", "native": "今天天气很好。", "transliteration": "Jīntiān tiānqì hěn hǎo."},
    {"english": "I am learning Chinese.", "native": "我在学中文。", "transliteration": "Wǒ zài xué zhōngwén."},
    {"english": "See you tomorrow.", "native": "明天见。", "transliteration": "Míngtiān jiàn."},
    {"english": "Thank you very much.", "native": "非常感谢。", "transliteration": "Fēicháng gǎnxiè."},
]
# ==== FALLBACK PHRASES END ====


def _load_json(path, default):
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return default


def _save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_phrase_history():
    data = _load_json(PHRASE_HISTORY_FILE, {"phrases": [], "last_updated": None})
    data.setdefault("phrases", [])
    return data


def save_phrase_history(data):
    data["last_updated"] = datetime.now().isoformat()
    _save_json(PHRASE_HISTORY_FILE, data)


def is_phrase_used(english):
    english_lower = english.lower().strip()
    for p in load_phrase_history()["phrases"]:
        if p.get("english", "").lower().strip() == english_lower:
            return True
    return False


def _history_native(p):
    for key in (PHRASE_KEY, "vietnamese", "native", "translation", "target"):
        value = p.get(key)
        if value:
            return str(value)
    return ""


def add_phrases_to_history(phrases, category):
    history = load_phrase_history()
    for phrase in phrases:
        history["phrases"].append({
            "english": phrase["english"],
            PHRASE_KEY: phrase["native"],
            "transliteration": phrase.get("transliteration", ""),
            "category": category,
            "generated_at": datetime.now().isoformat(),
        })
    save_phrase_history(history)
    print(f"[content] Saved {len(phrases)} phrases (history total: {len(history['phrases'])})")


def get_available_category():
    data = _load_json(RECENT_CATEGORIES_FILE, {"recent_categories": [], "last_updated": None})
    recent = data.get("recent_categories", [])
    available = [c for c in CATEGORIES if c not in recent]
    if not available:
        recent = recent[-5:]
        available = [c for c in CATEGORIES if c not in recent]
        print("[rotation] Reset recent categories")
    selected = random.choice(available)
    recent.append(selected)
    data["recent_categories"] = recent[-MAX_RECENT_CATEGORIES:]
    data["last_updated"] = datetime.now().isoformat()
    _save_json(RECENT_CATEGORIES_FILE, data)
    print(f"[rotation] Category: {selected} ({len(available)} available)")
    return selected


def _normalize_phrase(item):
    if not isinstance(item, dict):
        return None
    english = str(item.get("english", "")).strip()
    native = str(
        item.get(PHRASE_KEY)
        or item.get("native")
        or item.get("vietnamese")
        or item.get("translation")
        or ""
    ).strip()
    translit = str(item.get("transliteration") or item.get("romanization") or item.get("romaji") or "").strip()
    if not english or not native:
        return None
    if len(english.split()) > 16:
        return None
    if "/" in native or "|" in native:
        native = native.split("/")[0].split("|")[0].strip()
    return {
        "english": english.replace("  ", " ").strip(),
        "native": native.strip(),
        "transliteration": translit.strip().strip("[]"),
    }


def _history_keys(history):
    used_en = set()
    used_nat = set()
    for p in history.get("phrases", []):
        en = str(p.get("english", "")).lower().strip()
        nat = _history_native(p).lower().strip()
        if en:
            used_en.add(en)
        if nat:
            used_nat.add(nat)
    return used_en, used_nat


def generate_phrases(category_english: str, num_phrases: int = 5) -> list:
    category_native = CATEGORIES_NATIVE[category_english]
    history = load_phrase_history()
    used_en, used_nat = _history_keys(history)
    recent_english = [
        p["english"] for p in history["phrases"] if p.get("category") == category_english
    ][-30:]

    models = [config.AI_MODEL]
    if "gemini-fast" not in models:
        models.append("gemini-fast")

    if config.POLLINATIONS_API_KEY:
        for attempt in range(5):
            model = models[0] if attempt < 3 else models[-1]
            try:
                phrases = _request_phrases(category_english, category_native, recent_english, num_phrases, attempt, model)
                unique = []
                for item in phrases:
                    p = _normalize_phrase(item)
                    if not p:
                        continue
                    key_en = p["english"].lower().strip()
                    key_nat = p["native"].lower().strip()
                    if key_en in used_en or key_nat in used_nat:
                        continue
                    if any(key_en == u["english"].lower().strip() for u in unique):
                        continue
                    used_en.add(key_en)
                    used_nat.add(key_nat)
                    unique.append(p)
                    if len(unique) >= num_phrases:
                        break
                if len(unique) >= num_phrases:
                    add_phrases_to_history(unique[:num_phrases], category_english)
                    return unique[:num_phrases]
                print(f"[content] Attempt {attempt + 1}: only {len(unique)} fresh phrases (need {num_phrases})")
            except Exception as exc:  # noqa: BLE001 - network boundary
                print(f"[content] Attempt {attempt + 1} failed ({model}): {exc}")
            time.sleep(1.5 * (attempt + 1))
    else:
        print("[content] No POLLINATIONS_API_KEY, using fallback phrases")

    fresh_fallback = []
    for p in FALLBACK_PHRASES:
        if p["english"].lower().strip() in used_en or p["native"].lower().strip() in used_nat:
            continue
        fresh_fallback.append(p)
    if not fresh_fallback:
        raise RuntimeError("Phrase API unavailable and no unused fallback phrases left; refusing to reuse phrases")
    chosen = fresh_fallback[:num_phrases]
    if len(chosen) < num_phrases:
        print(f"[content] Only {len(chosen)} fresh fallback phrases; building a shorter lesson")
    add_phrases_to_history(chosen, category_english)
    return chosen


def _request_phrases(category_english, category_native, recent_english, num_phrases, attempt, model=None):
    avoid = ""
    if recent_english:
        avoid = "\nDo NOT reuse any of these phrases:\n" + "\n".join(f"- {p}" for p in recent_english)

    prompt = f"""Create {num_phrases * 6} unique {category_english} phrases for English speakers learning {LANGUAGE_NAME}.
{avoid}

Rules:
1. Keep every phrase short and natural (4-11 words in English).
2. Use natural commas for TTS breathing pauses.
3. Each phrase must be speakable in 2-4 seconds.
4. Write clean {LANGUAGE_NAME} in {NATIVE_NAME} with correct accents and orthography. One translation only, no slashes.
5. Transliteration is a friendly Roman-script pronunciation guide for English speakers (not IPA).
6. Vary the sentence patterns and emotions. No duplicates.
7. Phrases must feel like real everyday language, not textbook filler.

Return ONLY a JSON array:
[{{"english": "...", "native": "...", "transliteration": "..."}}]"""

    response = requests.post(
        "https://gen.pollinations.ai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {config.POLLINATIONS_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": model or config.AI_MODEL,
            "messages": [
                {"role": "system", "content": f"You are a {LANGUAGE_NAME} teacher creating short, natural, varied bilingual phrases. Reply with JSON only."},
                {"role": "user", "content": prompt},
            ],
            "temperature": min(0.95 + attempt * 0.02, 1.0),
        },
        timeout=90,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"].strip()

    if "```json" in content:
        content = content.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in content:
        content = content.split("```", 1)[1].split("```", 1)[0].strip()

    start = content.find("[")
    end = content.rfind("]")
    if start >= 0 and end > start:
        content = content[start:end + 1]

    data = json.loads(content)
    if not isinstance(data, list):
        raise ValueError("AI did not return a JSON array")
    return data
