"""
Facebook Reels Automation - Bilingual English/Chinese Content Generator
IMPROVED VERSION: Better backgrounds, English categories, no repeats, Velocity Chinese branding
"""

import os
import sys
import json
import random
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")

# Directories
BASE_DIR = Path(__file__).parent
FONTS_DIR = BASE_DIR / "fonts"
OUTPUT_DIR = BASE_DIR / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
AUDIO_DIR = OUTPUT_DIR / "audio"
VIDEO_DIR = OUTPUT_DIR / "video"
HISTORY_DIR = OUTPUT_DIR / "history"

for d in [OUTPUT_DIR, IMAGES_DIR, AUDIO_DIR, VIDEO_DIR, HISTORY_DIR]:
    d.mkdir(exist_ok=True)

# Video settings (9:16 vertical)
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

# English category names (for American/European learners)
CATEGORIES_ENGLISH = [
    "Motivation", "Love", "Success", "Wisdom", "Happiness",
    "Self Improvement", "Gratitude", "Friendship", "Hope", "Creativity",
    "Inner Peace", "Confidence", "Perseverance", "Inspiration", "Positive Life",
    "Courage", "Kindness", "Patience", "Forgiveness", "Strength",
    "Joy", "Balance", "Growth", "Purpose", "Mindfulness",
]

# Chinese translations for display
CATEGORIES_CHINESE = {
    "Motivation": "动力",
    "Love": "爱情",
    "Success": "成功",
    "Wisdom": "智慧",
    "Happiness": "幸福",
    "Self Improvement": "自我提升",
    "Gratitude": "感恩",
    "Friendship": "友谊",
    "Hope": "希望",
    "Creativity": "创造力",
    "Inner Peace": "内心平静",
    "Confidence": "自信",
    "Perseverance": "毅力",
    "Inspiration": "灵感",
    "Positive Life": "积极生活",
    "Courage": "勇气",
    "Kindness": "善良",
    "Patience": "耐心",
    "Forgiveness": "宽恕",
    "Strength": "力量",
    "Joy": "快乐",
    "Balance": "平衡",
    "Growth": "成长",
    "Purpose": "目标",
    "Mindfulness": "正念",
}

# Edge TTS voices
ENGLISH_VOICE = "en-US-GuyNeural"
CHINESE_VOICE = "zh-CN-XiaoxiaoNeural"

# Phrase history file (NEVER delete this!)
PHRASE_HISTORY_FILE = HISTORY_DIR / "all_generated_phrases.json"

# Viral hook styles for engagement (like Spanish bot)
VIRAL_STYLES = [
    "surprising fact",
    "common mistake correction",
    "quick tip",
    "must-know phrase",
    "local secret",
    "travel hack",
    "flirty phrase",
    "funny expression",
    "cultural insight",
    "word origin story"
]

# AI Model - MUST be set in .env file (NO HARDCODED DEFAULT)
# Add AI_MODEL=gemini-fast to your .env file
# GitHub Actions: Add AI_MODEL to repository secrets
AI_MODEL = os.getenv("AI_MODEL")

if not AI_MODEL:
    raise ValueError(
        "AI_MODEL not set! Please add 'AI_MODEL=gemini-fast' to your .env file. "
        "For GitHub Actions: Add AI_MODEL to repository secrets."
    )


# ============== PHRASE HISTORY MANAGEMENT (Prevent Repeats) ==============

def load_phrase_history():
    """Load all previously generated phrases"""
    if PHRASE_HISTORY_FILE.exists():
        with open(PHRASE_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"phrases": [], "last_updated": None}


def save_phrase_history(data):
    """Save phrase history"""
    data["last_updated"] = datetime.now().isoformat()
    with open(PHRASE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_phrase_used(english_phrase):
    """Check if phrase was already generated (exact match)"""
    history = load_phrase_history()
    english_lower = english_phrase.lower().strip()
    for p in history.get("phrases", []):
        if p.get("english", "").lower().strip() == english_lower:
            return True
    return False


def is_phrase_similar(new_phrase, used_phrases, similarity_threshold=0.6):
    """
    Check if a phrase is too similar to previously used phrases
    Simple word-based Jaccard similarity check
    
    Lower threshold (0.6) means stricter duplicate detection
    """
    new_words = set(new_phrase.lower().split())
    
    # Skip very short phrases - use substring match
    if len(new_words) < 3:
        for used in used_phrases:
            if new_phrase.lower() in used.lower() or used.lower() in new_phrase.lower():
                return True
        return False
    
    for used in used_phrases:
        used_words = set(used.lower().split())
        
        if len(new_words) == 0 or len(used_words) == 0:
            continue
        
        # Calculate Jaccard similarity
        intersection = len(new_words.intersection(used_words))
        union = len(new_words.union(used_words))
        similarity = intersection / union if union > 0 else 0
        
        if similarity >= similarity_threshold:
            return True
    
    return False


def filter_similar_phrases(phrases, history, similarity_threshold=0.6):
    """
    Filter out phrases that are too similar to previously used ones
    Returns list of unique phrases
    """
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    unique_phrases = []
    
    for phrase in phrases:
        english_text = phrase.get("english", "")
        
        if not is_phrase_similar(english_text, used_phrases, similarity_threshold):
            unique_phrases.append(phrase)
        else:
            print(f"[filter] ⚠️ Skipping similar: {english_text[:50]}...")
    
    return unique_phrases


def add_phrases_to_history(phrases, category):
    """Add new phrases to history"""
    history = load_phrase_history()
    for phrase in phrases:
        history["phrases"].append({
            "english": phrase["english"],
            "chinese": phrase["chinese"],
            "category": category,
            "generated_at": datetime.now().isoformat()
        })
    save_phrase_history(history)
    print(f"[history] Added {len(phrases)} phrases to history (total: {len(history['phrases'])})")


# ============== CONTENT GENERATION ==============

def generate_phrases(category_english: str, num_phrases: int = 5) -> list:
    """Generate unique bilingual phrases with natural pauses, ensuring no repeats"""

    import random
    
    category_chinese = CATEGORIES_CHINESE[category_english]
    
    # Load history to get used phrases
    history = load_phrase_history()
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    
    # Pick a viral style for variety
    viral_style = random.choice(VIRAL_STYLES)

    # Try AI first
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            import requests
            url = "https://gen.pollinations.ai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
                "Content-Type": "application/json"
            }

            # Build exclusion list from used phrases (last 20)
            exclusion_note = ""
            if used_phrases and len(used_phrases) > 0:
                recent = used_phrases[-20:] if len(used_phrases) > 20 else used_phrases
                exclusion_note = f"\n\nAVOID these phrases (already used): {recent}"

            prompt = f"""Create {num_phrases * 2} unique {category_english} phrases for English speakers learning Chinese (Mandarin).

Style: Make each phrase feel like a {viral_style} - something people would want to share!

IMPORTANT RULES FOR NATURAL SPEECH:
1. Keep phrases SHORT (5-12 words max per language)
2. Add NATURAL PAUSES using commas (e.g., "Dream big, start small")
3. Use punctuation for breathing room in TTS
4. Avoid long run-on sentences
5. Each phrase should be speakable in 3-5 seconds
6. Use everyday vocabulary - avoid exotic or rare words
7. Avoid complex grammar - keep it simple and practical

For each phrase:
1. English phrase (with commas for natural pauses)
2. Chinese translation (Simplified Chinese characters)
3. Pinyin pronunciation guide (with tone marks, e.g., "nǐ hǎo")

Return as JSON array:
[{{"english": "...", "chinese": "...", "pinyin": "..."}}]

IMPORTANT: Create FRESH, UNIQUE phrases that haven't been used before.{exclusion_note}"""

            payload = {
                "model": AI_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a viral Chinese teacher creating engaging educational content for social media. Create short, natural phrases with pauses."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 1.0  # Maximum creativity for unique content
            }

            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()

            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            phrases = json.loads(content)

            # First filter by similarity (stricter check)
            filtered_phrases = filter_similar_phrases(phrases, history)
            
            # Then filter by length and exact duplicates
            unique_phrases = []
            for phrase in filtered_phrases:
                # Skip if too long (over 15 words)
                if len(phrase["english"].split()) > 15:
                    continue
                # Double-check exact match
                if not is_phrase_used(phrase["english"]):
                    unique_phrases.append(phrase)
                if len(unique_phrases) >= num_phrases:
                    break

            if len(unique_phrases) >= num_phrases:
                add_phrases_to_history(unique_phrases[:num_phrases], category_english)
                return unique_phrases[:num_phrases]

        except Exception as e:
            print(f"[content] Attempt {attempt + 1} failed: {e}")

    # Fallback to fresh phrases
    print("[content] Using fallback phrases...")
    return get_fresh_fallback_phrases(category_english, num_phrases)


def get_fresh_fallback_phrases(category: str, num_phrases: int) -> list:
    """Get fallback phrases, filtering out used ones with similarity check"""

    # Expanded fallback phrases for ALL 25 categories
    all_fallbacks = {
        "Motivation": [
            {"english": "Believe in yourself.", "chinese": "相信自己。", "pinyin": "xiāng xìn zì jǐ."},
            {"english": "You are capable of amazing things.", "chinese": "你有能力成就惊人的事情。", "pinyin": "nǐ yǒu néng lì chéng jiù jīng rén de shì qíng."},
            {"english": "Dream big, start small.", "chinese": "胸怀大志，从小做起。", "pinyin": "xiōng huái dà zhì, cóng xiǎo zuò qǐ."},
            {"english": "Your future is created by your actions.", "chinese": "你的未来由你的行动创造。", "pinyin": "nǐ de wèi lái yóu nǐ de xíng dòng chuàng zào."},
            {"english": "Never give up on your dreams.", "chinese": "永不放弃梦想。", "pinyin": "yǒng bù fàng qì mèng xiǎng."},
            {"english": "Small steps lead to big changes.", "chinese": "小步引领大变化。", "pinyin": "xiǎo bù yǐn lǐng dà biàn huà."},
            {"english": "You are stronger than you think.", "chinese": "你比自己想象的更强大。", "pinyin": "nǐ bǐ zì jǐ xiǎng xiàng de gèng qiáng dà."},
        ],
        "Love": [
            {"english": "Love yourself first.", "chinese": "先爱自己。", "pinyin": "xiān ài zì jǐ."},
            {"english": "Love makes everything possible.", "chinese": "爱使一切成为可能。", "pinyin": "ài shǐ yī qiè chéng wéi kě néng."},
            {"english": "My heart beats for you.", "chinese": "我的心为你跳动。", "pinyin": "wǒ de xīn wèi nǐ tiào dòng."},
            {"english": "You are my everything.", "chinese": "你是我的一切。", "pinyin": "nǐ shì wǒ de yī qiè."},
            {"english": "Together forever, hand in hand.", "chinese": "永远在一起，手牵手。", "pinyin": "yǒng yuǎn zài yī qǐ, shǒu qiān shǒu."},
        ],
        "Success": [
            {"english": "Success comes from hard work.", "chinese": "成功来自努力。", "pinyin": "chéng gōng lái zì nǔ lì."},
            {"english": "Keep going, you're getting there.", "chinese": "继续前进，你快到了。", "pinyin": "jì xù qián jìn, nǐ kuài dào le."},
            {"english": "Winners never quit.", "chinese": "赢家永不放弃。", "pinyin": "yíng jiā yǒng bù fàng qì."},
            {"english": "Your effort will pay off.", "chinese": "你的努力会有回报。", "pinyin": "nǐ de nǔ lì huì yǒu huí bào."},
        ],
        "Wisdom": [
            {"english": "Knowledge is power.", "chinese": "知识就是力量。", "pinyin": "zhī shí jiù shì lì liàng."},
            {"english": "Learn from yesterday, live for today.", "chinese": "借鉴昨天，活在今天。", "pinyin": "jiè jiàn zuó tiān, huó zài jīn tiān."},
            {"english": "Think before you act.", "chinese": "三思而后行。", "pinyin": "sān sī ér hòu xíng."},
            {"english": "Experience is the best teacher.", "chinese": "经验是最好的老师。", "pinyin": "jīng yàn shì zuì hǎo de lǎo shī."},
        ],
        "Happiness": [
            {"english": "Happiness is a choice.", "chinese": "快乐是一种选择。", "pinyin": "kuài lè shì yī zhǒng xuǎn zé."},
            {"english": "Find joy in the little things.", "chinese": "在小事中寻找快乐。", "pinyin": "zài xiǎo shì zhōng xún zhǎo kuài lè."},
            {"english": "Smile, it makes others happy.", "chinese": "微笑，让别人也开心。", "pinyin": "wēi xiào, ràng bié rén yě kāi xīn."},
            {"english": "Today is a gift.", "chinese": "今天是礼物。", "pinyin": "jīn tiān shì lǐ wù."},
        ],
        "Self Improvement": [
            {"english": "Be better than yesterday.", "chinese": "比昨天更好。", "pinyin": "bǐ zuó tiān gèng hǎo."},
            {"english": "Grow through what you go through.", "chinese": "在经历中成长。", "pinyin": "zài jīng lì zhōng chéng zhǎng."},
            {"english": "Invest in yourself daily.", "chinese": "每天投资自己。", "pinyin": "měi tiān tóu zī zì jǐ."},
        ],
        "Gratitude": [
            {"english": "Thank you for everything.", "chinese": "谢谢你的一切。", "pinyin": "xiè xie nǐ de yī qiè."},
            {"english": "I appreciate your help.", "chinese": "我感激你的帮助。", "pinyin": "wǒ gǎn jī nǐ de bāng zhù."},
            {"english": "Grateful for this moment.", "chinese": "感激这一刻。", "pinyin": "gǎn jī zhè yī kè."},
        ],
        "Friendship": [
            {"english": "Friends forever, no matter what.", "chinese": "永远是朋友，无论如何。", "pinyin": "yǒng yuǎn shì péng yǒu, wú lùn rú hé."},
            {"english": "You are my best friend.", "chinese": "你是我最好的朋友。", "pinyin": "nǐ shì wǒ zuì hǎo de péng yǒu."},
            {"english": "True friends stick together.", "chinese": "真正的朋友在一起。", "pinyin": "zhēn zhèng de péng yǒu zài yī qǐ."},
        ],
        "Hope": [
            {"english": "There is always hope.", "chinese": "总有希望。", "pinyin": "zǒng yǒu xī wàng."},
            {"english": "Better days are coming.", "chinese": "更好的日子会来。", "pinyin": "gèng hǎo de rì zi huì lái."},
            {"english": "Keep faith, keep going.", "chinese": "保持信念，继续前进。", "pinyin": "bǎo chí xìn niàn, jì xù qián jìn."},
        ],
        "Creativity": [
            {"english": "Create something beautiful today.", "chinese": "今天创造美好的东西。", "pinyin": "jīn tiān chuàng zào měi hǎo de dōng xī."},
            {"english": "Your imagination is unlimited.", "chinese": "你的想象力无限。", "pinyin": "nǐ de xiǎng xiàng lì wú xiàn."},
            {"english": "Art comes from the heart.", "chinese": "艺术来自内心。", "pinyin": "yì shù lái zì nèi xīn."},
            {"english": "Express yourself freely.", "chinese": "自由表达自己。", "pinyin": "zì yóu biǎo dá zì jǐ."},
            {"english": "Innovation starts with curiosity.", "chinese": "创新始于好奇心。", "pinyin": "chuàng xīn shǐ yú hào qí xīn."},
        ],
        "Inner Peace": [
            {"english": "Find peace within yourself.", "chinese": "在内心寻找平静。", "pinyin": "zài nèi xīn xún zhǎo píng jìng."},
            {"english": "Breathe, relax, let go.", "chinese": "呼吸，放松，放下。", "pinyin": "hū xī, fàng sōng, fàng xià."},
            {"english": "Calm mind, happy heart.", "chinese": "心静，心喜。", "pinyin": "xīn jìng, xīn xǐ."},
        ],
        "Confidence": [
            {"english": "You are enough, just as you are.", "chinese": "你足够了，就做你自己。", "pinyin": "nǐ zú gòu le, jiù zuò nǐ zì jǐ."},
            {"english": "Stand tall, speak up.", "chinese": "挺直腰板，大声说话。", "pinyin": "tǐng zhí yāo bǎn, dà shēng shuō huà."},
            {"english": "Believe in your abilities.", "chinese": "相信你的能力。", "pinyin": "xiāng xìn nǐ de néng lì."},
        ],
        "Perseverance": [
            {"english": "Never give up, keep pushing.", "chinese": "永不放弃，继续前进。", "pinyin": "yǒng bù fàng qì, jì xù qián jìn."},
            {"english": "Storms make trees take deeper roots.", "chinese": "风暴使树根更深。", "pinyin": "fēng bào shǐ shù gēn gèng shēn."},
            {"english": "Patience and persistence win.", "chinese": "耐心和坚持获胜。", "pinyin": "nài xīn hé jiān chí huò shèng."},
        ],
        "Inspiration": [
            {"english": "Let your light shine bright.", "chinese": "让你的光芒闪耀。", "pinyin": "ràng nǐ de guāng máng shǎn yào."},
            {"english": "Inspire others by your actions.", "chinese": "用行动激励他人。", "pinyin": "yòng xíng dòng jī lì tā rén."},
            {"english": "Be the change you want to see.", "chinese": "成为你想看到的改变。", "pinyin": "chéng wéi nǐ xiǎng kàn dào de gǎi biàn."},
        ],
        "Positive Life": [
            {"english": "Choose positivity every day.", "chinese": "每天选择积极。", "pinyin": "měi tiān xuǎn zé jī jí."},
            {"english": "Good vibes only.", "chinese": "只要好氛围。", "pinyin": "zhǐ yào hǎo fēn wéi."},
            {"english": "Life is what you make it.", "chinese": "生活由你创造。", "pinyin": "shēng huó yóu nǐ chuàng zào."},
        ],
        "Courage": [
            {"english": "Be brave, take the first step.", "chinese": "勇敢，迈出第一步。", "pinyin": "yǒng gǎn, mài chū dì yī bù."},
            {"english": "Courage is not the absence of fear.", "chinese": "勇气不是没有恐惧。", "pinyin": "yǒng qì bù shì méi yǒu kǒng jù."},
            {"english": "Face your fears head on.", "chinese": "直面恐惧。", "pinyin": "zhí miàn kǒng jù."},
        ],
        "Kindness": [
            {"english": "Be kind to everyone you meet.", "chinese": "善待你遇到的每个人。", "pinyin": "shàn dài nǐ yù dào de měi gè rén."},
            {"english": "Kindness costs nothing, means everything.", "chinese": "善良无需代价，意义非凡。", "pinyin": "shàn liáng wú xū dài jià, yì yì fēi fán."},
            {"english": "Spread kindness wherever you go.", "chinese": "无论去哪里都传播善良。", "pinyin": "wú lùn qù nǎ lǐ dōu chuán bō shàn liáng."},
        ],
        "Patience": [
            {"english": "Good things take time.", "chinese": "好事需要时间。", "pinyin": "hǎo shì xū yào shí jiān."},
            {"english": "Wait patiently, trust the process.", "chinese": "耐心等待，相信过程。", "pinyin": "nài xīn děng dài, xiāng xìn guò chéng."},
            {"english": "Rome wasn't built in a day.", "chinese": "罗马不是一天建成的。", "pinyin": "luó mǎ bù shì yī tiān jiàn chéng de."},
        ],
        "Forgiveness": [
            {"english": "Forgive and set yourself free.", "chinese": "原谅并释放自己。", "pinyin": "yuán liàng bìng shì fàng zì jǐ."},
            {"english": "Let go of grudges, find peace.", "chinese": "放下怨恨，找到平静。", "pinyin": "fàng xià yuàn hèn, zhǎo dào píng jìng."},
            {"english": "Forgiveness is a gift to yourself.", "chinese": "原谅是给自己的礼物。", "pinyin": "yuán liàng shì gěi zì jǐ de lǐ wù."},
        ],
        "Strength": [
            {"english": "You are stronger than you know.", "chinese": "你比自己知道的更强大。", "pinyin": "nǐ bǐ zì jǐ zhī dào de gèng qiáng dà."},
            {"english": "Inner strength comes from within.", "chinese": "内在力量来自内心。", "pinyin": "nèi zài lì liàng lái zì nèi xīn."},
            {"english": "Challenges make you stronger.", "chinese": "挑战让你更强大。", "pinyin": "tiǎo zhàn ràng nǐ gèng qiáng dà."},
        ],
        "Joy": [
            {"english": "Find joy in every moment.", "chinese": "在每一刻找到快乐。", "pinyin": "zài měi yī kè zhǎo dào kuài lè."},
            {"english": "Joy is contagious, spread it.", "chinese": "快乐会传染，传播它。", "pinyin": "kuài lè huì chuán rǎn, chuán bō tā."},
            {"english": "Dance like nobody's watching.", "chinese": "像没人看着一样跳舞。", "pinyin": "xiàng méi rén kàn zhe yī yàng tiào wǔ."},
        ],
        "Balance": [
            {"english": "Find balance in your life.", "chinese": "在生活中找到平衡。", "pinyin": "zài shēng huó zhōng zhǎo dào píng héng."},
            {"english": "Work hard, rest well.", "chinese": "努力工作，好好休息。", "pinyin": "nǔ lì gōng zuò, hǎo hǎo xiū xī."},
            {"english": "Too much of anything is not good.", "chinese": "过犹不及。", "pinyin": "guò yóu bù jí."},
        ],
        "Growth": [
            {"english": "Growth happens outside your comfort zone.", "chinese": "成长发生在舒适区外。", "pinyin": "chéng zhǎng fā shēng zài shū shì qū wài."},
            {"english": "Embrace change, grow stronger.", "chinese": "拥抱改变，变得更强大。", "pinyin": "yōng bào gǎi biàn, biàn dé gèng qiáng dà."},
            {"english": "Every challenge is a chance to grow.", "chinese": "每个挑战都是成长机会。", "pinyin": "měi gè tiǎo zhàn dōu shì chéng zhǎng jī huì."},
        ],
        "Purpose": [
            {"english": "Find your purpose, follow it.", "chinese": "找到你的目标，追随它。", "pinyin": "zhǎo dào nǐ de mù biāo, zhuī suí tā."},
            {"english": "Your life has meaning.", "chinese": "你的生命有意义。", "pinyin": "nǐ de shēng mìng yǒu yì yì."},
            {"english": "Live with intention, not accident.", "chinese": "有目的地生活，不是偶然。", "pinyin": "yǒu mù dì de shēng huó, bù shì ǒu rán."},
        ],
        "Mindfulness": [
            {"english": "Be present in this moment.", "chinese": "活在当下这一刻。", "pinyin": "huó zài dāng xià zhè yī kè."},
            {"english": "Breathe deeply, stay grounded.", "chinese": "深呼吸，保持踏实。", "pinyin": "shēn hū xī, bǎo chí tà shí."},
            {"english": "Notice the little things around you.", "chinese": "注意周围的小事。", "pinyin": "zhù yì zhōu wéi de xiǎo shì."},
        ],
    }

    fallbacks = all_fallbacks.get(category, all_fallbacks["Motivation"])
    
    # Load history and filter with similarity check
    history = load_phrase_history()
    fresh_phrases = []
    for p in fallbacks:
        if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
            fresh_phrases.append(p)
    
    # If still not enough, try other categories' fallbacks
    if len(fresh_phrases) < num_phrases:
        for cat, cat_fallbacks in all_fallbacks.items():
            if cat != category:
                for p in cat_fallbacks:
                    if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
                        fresh_phrases.append(p)
                    if len(fresh_phrases) >= num_phrases:
                        break
            if len(fresh_phrases) >= num_phrases:
                break
    
    return fresh_phrases[:num_phrases]


# ============== AUDIO GENERATION ==============

async def generate_single_audio(text: str, voice: str, output_path: str):
    """Generate audio using Edge TTS"""
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"  TTS error: {e}")
        return False


def generate_all_audio(phrases: list, output_dir: str):
    """Generate audio for all phrases with proper timing"""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = []

    for i, phrase in enumerate(phrases):
        english_file = output_dir / f"english_{i}.mp3"
        chinese_file = output_dir / f"chinese_{i}.mp3"
        combined_file = output_dir / f"combined_{i}.mp3"

        print(f"\n  Phrase {i+1}:")
        print(f"    EN: {phrase['english']}")
        print(f"    CN: {phrase['chinese']}")

        # Generate English audio
        en_success = asyncio.run(generate_single_audio(phrase["english"], ENGLISH_VOICE, str(english_file)))
        if en_success:
            print(f"    ✓ English: {english_file.name}")
        else:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(english_file)]
            subprocess.run(cmd, capture_output=True)

        # Generate Chinese audio
        cn_success = asyncio.run(generate_single_audio(phrase["chinese"], CHINESE_VOICE, str(chinese_file)))
        if cn_success:
            print(f"    ✓ Chinese: {chinese_file.name}")
        else:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(chinese_file)]
            subprocess.run(cmd, capture_output=True)

        # Get ACTUAL durations
        en_duration = get_audio_duration(str(english_file))
        cn_duration = get_audio_duration(str(chinese_file))

        # Add pause between English and Chinese
        pause_between = 0.5
        total_duration = en_duration + pause_between + cn_duration

        print(f"    ⏱️  Total: {total_duration:.2f}s (EN: {en_duration:.2f}s + pause: {pause_between}s + CN: {cn_duration:.2f}s)")

        # Generate silence for pause
        silence_file = output_dir / f"silence_{i}.mp3"
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", str(pause_between), str(silence_file)],
                       capture_output=True)

        # Combine audio: English + silence + Chinese
        cmd = [
            "ffmpeg", "-y",
            "-i", str(english_file),
            "-i", str(silence_file),
            "-i", str(chinese_file),
            "-filter_complex", "[0:a][1:a][2:a]concat=n=3:v=0:a=1[out]",
            "-map", "[out]",
            str(combined_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if silence_file.exists():
            silence_file.unlink()

        if result.returncode != 0:
            concat_file = output_dir / f"concat_{i}.txt"
            with open(concat_file, "w", encoding="utf-8") as f:
                f.write(f"file '{english_file.as_posix()}'\n")
                f.write(f"file '{chinese_file.as_posix()}'\n")

            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_file),
                "-c:a", "aac",
                str(combined_file)
            ]
            subprocess.run(cmd, capture_output=True)
            if concat_file.exists():
                concat_file.unlink()

        actual_duration = get_audio_duration(str(combined_file))
        print(f"    ✓ Combined verified: {actual_duration:.2f}s")

        audio_files.append({
            "index": i,
            "english": str(english_file),
            "chinese": str(chinese_file),
            "combined": str(combined_file),
            "duration": actual_duration,
            "en_duration": en_duration,
            "cn_duration": cn_duration
        })

    print(f"\n[audio] ✓ Generated {len(audio_files)} phrase audios")
    return audio_files


def get_audio_duration(audio_file: str) -> float:
    """Get audio duration in seconds"""
    if not Path(audio_file).exists():
        return 2.0
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 2.0


def create_final_narration(audio_files: list, output_file: str):
    """Combine all audio files"""
    n = len(audio_files)
    print(f"[audio] Combining {n} audio files...")

    concat_file = Path(output_file).parent / "narration_list.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for audio_info in audio_files:
            combined_path = Path(audio_info["combined"])
            if combined_path.exists():
                path_str = str(combined_path.resolve()).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{path_str}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c:a", "copy", str(output_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if concat_file.exists():
        concat_file.unlink()

    if result.returncode == 0 and Path(output_file).exists() and Path(output_file).stat().st_size > 0:
        size = Path(output_file).stat().st_size
        print(f"\n[audio] ✓ Final narration: {Path(output_file).name} ({size/1024:.1f} KB)")
        return True

    return False


# ============== IMAGE GENERATION ==============

def create_impressive_background(category_english: str):
    """Create stunning gradient background with geometric patterns and glow"""
    from PIL import Image, ImageDraw

    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)

    # HIGH CONTRAST gradients for ALL 25 categories (very different colors like Motivation)
    category_colors = {
        "Motivation": [(138, 43, 226), (75, 0, 130), (255, 20, 147), (147, 112, 219)],  # Purple → Dark Purple → Pink → Light Purple
        "Love": [(255, 0, 100), (139, 0, 0), (255, 105, 180), (255, 192, 203)],  # Red → Dark Red → Hot Pink → Pink
        "Success": [(255, 215, 0), (0, 100, 0), (255, 140, 0), (34, 139, 34)],  # Gold → Dark Green → Orange → Forest Green
        "Wisdom": [(0, 0, 139), (255, 215, 0), (70, 130, 180), (255, 255, 0)],  # Dark Blue → Gold → Steel Blue → Yellow
        "Happiness": [(255, 255, 0), (255, 0, 255), (255, 165, 0), (147, 112, 219)],  # Yellow → Magenta → Orange → Purple
        "Self Improvement": [(0, 128, 0), (255, 215, 0), (0, 255, 0), (255, 140, 0)],  # Green → Gold → Lime → Orange
        "Gratitude": [(255, 127, 80), (75, 0, 130), (255, 160, 122), (138, 43, 226)],  # Coral → Dark Purple → Light Salmon → Blue Violet
        "Friendship": [(255, 192, 203), (0, 100, 80), (255, 105, 180), (0, 200, 160)],  # Pink → Dark Teal → Hot Pink → Medium Teal
        "Hope": [(0, 0, 100), (255, 255, 0), (70, 130, 180), (255, 215, 0)],  # Dark Blue → Yellow → Steel Blue → Gold
        "Creativity": [(255, 0, 127), (0, 0, 139), (255, 20, 147), (75, 0, 130)],  # Deep Pink → Dark Blue → Deep Pink → Dark Purple
        "Inner Peace": [(135, 206, 235), (0, 0, 100), (176, 224, 230), (75, 0, 130)],  # Sky Blue → Dark Blue → Powder Blue → Dark Purple
        "Confidence": [(255, 69, 0), (0, 0, 139), (255, 140, 0), (70, 130, 180)],  # Red Orange → Dark Blue → Orange → Steel Blue
        "Perseverance": [(139, 69, 19), (255, 215, 0), (160, 82, 45), (255, 140, 0)],  # Saddle Brown → Gold → Sienna → Orange
        "Inspiration": [(255, 0, 255), (75, 0, 130), (255, 20, 147), (0, 0, 139)],  # Magenta → Dark Purple → Deep Pink → Dark Blue
        "Positive Life": [(50, 205, 50), (255, 0, 127), (144, 238, 144), (255, 20, 147)],  # Lime Green → Deep Pink → Light Green → Deep Pink
        "Courage": [(178, 34, 34), (255, 215, 0), (220, 20, 60), (255, 140, 0)],  # Firebrick → Gold → Crimson → Orange
        "Kindness": [(255, 182, 193), (138, 43, 226), (255, 160, 122), (75, 0, 130)],  # Light Salmon → Dark Purple → Light Salmon → Dark Purple
        "Patience": [(34, 139, 34), (255, 255, 0), (60, 179, 113), (255, 215, 0)],  # Forest Green → Yellow → Medium Sea Green → Gold
        "Forgiveness": [(230, 230, 250), (75, 0, 130), (216, 191, 216), (138, 43, 226)],  # Lavender → Dark Purple → Thistle → Blue Violet
        "Strength": [(100, 100, 100), (255, 69, 0), (150, 150, 150), (255, 140, 0)],  # Gray → Red Orange → Light Gray → Orange
        "Joy": [(255, 255, 0), (255, 0, 127), (255, 215, 0), (147, 112, 219)],  # Yellow → Deep Pink → Gold → Purple
        "Balance": [(60, 179, 113), (138, 43, 226), (152, 251, 152), (75, 0, 130)],  # Medium Sea Green → Dark Purple → Pale Green → Dark Purple
        "Growth": [(0, 100, 0), (255, 215, 0), (34, 139, 34), (255, 140, 0)],  # Dark Green → Gold → Forest Green → Orange
        "Purpose": [(75, 0, 130), (255, 215, 0), (138, 43, 226), (255, 140, 0)],  # Dark Purple → Gold → Blue Violet → Orange
        "Mindfulness": [(210, 180, 140), (75, 0, 130), (245, 245, 220), (138, 43, 226)],  # Tan → Dark Purple → Beige → Blue Violet
    }

    colors = category_colors.get(category_english, [(138, 43, 226), (75, 0, 130), (255, 20, 147), (147, 112, 219)])

    # Create smooth multi-stop gradient
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        if ratio < 0.33:
            r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * (ratio * 3))
            g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * (ratio * 3))
            b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * (ratio * 3))
        elif ratio < 0.66:
            r = int(colors[1][0] + (colors[2][0] - colors[1][0]) * ((ratio - 0.33) * 3))
            g = int(colors[1][1] + (colors[2][1] - colors[1][1]) * ((ratio - 0.33) * 3))
            b = int(colors[1][2] + (colors[2][2] - colors[1][2]) * ((ratio - 0.33) * 3))
        else:
            r = int(colors[2][0] + (colors[3][0] - colors[2][0]) * ((ratio - 0.66) * 3))
            g = int(colors[2][1] + (colors[3][1] - colors[2][1]) * ((ratio - 0.66) * 3))
            b = int(colors[2][2] + (colors[3][2] - colors[2][2]) * ((ratio - 0.66) * 3))
        draw.rectangle([(0, y), (VIDEO_WIDTH, y + 1)], fill=(r, g, b))

    # Add subtle geometric pattern for depth (circles)
    for i in range(0, VIDEO_WIDTH, 120):
        for j in range(0, VIDEO_HEIGHT, 120):
            draw.ellipse(
                [(i + 30, j + 30), (i + 90, j + 90)],
                outline=(255, 255, 255, 20),
                width=1
            )

    # Add radial glow effect from center
    glow = Image.new('RGBA', (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)

    for radius in range(800, 0, -50):
        alpha = int(30 * (1 - radius / 800))
        glow_draw.ellipse(
            [(VIDEO_WIDTH//2 - radius, VIDEO_HEIGHT//3 - radius),
             (VIDEO_WIDTH//2 + radius, VIDEO_HEIGHT//3 + radius)],
            fill=(255, 255, 255, alpha)
        )

    # Composite glow over background
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, glow)

    return img


def generate_complete_image(phrase_data: dict, category_english: str, output_path: str):
    """Generate image with impressive background - BOLDER fonts, no text overflow"""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("PIL not available. Install: pip install Pillow")
        return None

    img = create_impressive_background(category_english)
    draw = ImageDraw.Draw(img)

    # Load fonts - BOLDER and LARGER for better visibility
    # English fonts (EXTRA BOLD) - Linux priority for GitHub Actions
    english_font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux (GitHub Actions) - PRIORITY
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",  # Alternative Linux
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",  # Another Linux option
        "C:/Windows/Fonts/arialbd.ttf",  # Windows Arial Bold
        "C:/Windows/Fonts/segoeusbi.ttf",  # Windows Segoe UI Semibold
    ]

    # Chinese fonts (EXTRA BOLD for better visibility) - local font priority
    chinese_font_paths = [
        str(FONTS_DIR / "NotoSansSC-Bold.ttf"),  # Local downloaded font
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",  # Linux Noto CJK Bold
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",  # Linux WenQuanYi Micro Hei
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",  # Alternative Linux Noto
        "C:/Windows/Fonts/msyhbd.ttc",  # Windows Microsoft YaHei BOLD
        "C:/Windows/Fonts/simsun.ttc",  # Windows SimSun
    ]

    def load_font(font_paths, size):
        """Load font with fallback - tries each path until one works"""
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except (IOError, OSError):
                continue
        return ImageFont.load_default()

    # English text fonts - EXTRA BOLD and BIGGER
    font_category = load_font(english_font_paths, 65)
    font_large = load_font(english_font_paths, 85)
    font_branding = load_font(english_font_paths, 55)

    # Chinese text fonts - EXTRA BOLD and BIGGER (use BOLD fonts)
    font_chinese = load_font(chinese_font_paths, 65)

    # Pinyin fonts - EXTRA BOLD and LARGER (use BOLD Chinese fonts)
    font_pinyin = load_font(chinese_font_paths, 65)

    english = phrase_data.get("english", "")
    chinese = phrase_data.get("chinese", "")
    pinyin = phrase_data.get("pinyin", "")

    def wrap_text(text, font, max_width):
        """Wrap text to fit within max_width - handles both English and CJK characters"""
        lines = []

        is_cjk = any('\u3040' <= c <= '\u309f' or
                      '\u30a0' <= c <= '\u30ff' or
                      '\u4e00' <= c <= '\u9fff' or
                      '\u3400' <= c <= '\u4dbf' or
                      '\uf900' <= c <= '\ufaff'
                      for c in text)

        if is_cjk:
            current_line = ''
            for char in text:
                test_line = current_line + char
                bbox = draw.textbbox((0, 0), test_line, font=font)
                width = bbox[2] - bbox[0]
                if width <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = char
            if current_line:
                lines.append(current_line)
        else:
            words = text.split()
            current_line = []
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=font)
                width = bbox[2] - bbox[0]
                if width <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
            if current_line:
                lines.append(' '.join(current_line))

        return lines

    # Category at top - rounded container
    category_text = category_english.upper()
    cat_bb = draw.textbbox((0, 0), category_text, font=font_category)
    cat_tw = cat_bb[2] - cat_bb[0]
    cat_th = cat_bb[3] - cat_bb[1]
    cat_pad = 30
    cat_x1 = VIDEO_WIDTH // 2 - cat_tw // 2 - cat_pad
    cat_y1 = 140 - cat_th // 2 - cat_pad
    cat_x2 = VIDEO_WIDTH // 2 + cat_tw // 2 + cat_pad
    cat_y2 = 140 + cat_th // 2 + cat_pad
    rounded_rect(draw, (cat_x1, cat_y1, cat_x2, cat_y2), 25, fill=(0, 0, 0, 200))
    draw.text(
        (VIDEO_WIDTH // 2, 140),
        category_text,
        fill=(255, 255, 255),
        font=font_category,
        anchor="mm",
        stroke_width=3,
        stroke_fill=(0, 0, 0)
    )

    # English text - centered container with safe margins for stroke
    en_margin = 130
    en_max_w = VIDEO_WIDTH - en_margin * 2
    english_lines = wrap_text(english, font_large, en_max_w)
    en_line_spacing = 110
    en_total_h = len(english_lines) * en_line_spacing
    en_pad = 60
    en_center = 520 + ((len(english_lines) - 1) * en_line_spacing) // 2
    en_y1 = en_center - en_total_h // 2 - en_pad
    en_y2 = en_center + en_total_h // 2 + en_pad

    rounded_rect(draw, (en_margin, en_y1, VIDEO_WIDTH - en_margin, en_y2), 28,
                 fill=(30, 40, 80, 240))

    for i, line in enumerate(english_lines):
        y_pos = 520 + (i * en_line_spacing)
        draw.text(
            (VIDEO_WIDTH // 2, y_pos), line,
            fill=(255, 255, 255), font=font_large,
            anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0)
        )

    # Chinese text - centered container with safe margins
    cn_margin = 80
    cn_max_w = VIDEO_WIDTH - cn_margin * 2
    chinese_lines = wrap_text(chinese, font_chinese, cn_max_w)
    cn_line_spacing = 90
    cn_total_h = len(chinese_lines) * cn_line_spacing
    cn_pad = 60
    cn_y1 = en_y2 + 50
    cn_y2 = cn_y1 + cn_total_h + cn_pad * 2

    rounded_rect(draw, (cn_margin, cn_y1, VIDEO_WIDTH - cn_margin, cn_y2), 24,
                 fill=(85, 45, 45, 240))

    for i, line in enumerate(chinese_lines):
        y_pos = cn_y1 + cn_pad + i * cn_line_spacing + cn_line_spacing // 2
        draw.text(
            (VIDEO_WIDTH // 2, y_pos), line,
            fill=(255, 255, 50), font=font_chinese,
            anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0)
        )

    # Pinyin - centered container with symmetric padding
    pinyin_text = f"[{pinyin}]"
    pinyin_lines = wrap_text(pinyin_text, font_pinyin, VIDEO_WIDTH - 160)

    if pinyin_lines:
        py_line_spacing = 65
        py_total_h = len(pinyin_lines) * py_line_spacing
        py_pad = 35
        py_y1 = cn_y2 + 40
        py_y2 = py_y1 + py_total_h + py_pad * 2

        rounded_rect(draw, (70, py_y1, VIDEO_WIDTH - 70, py_y2), 18,
                     fill=(40, 40, 60, 230))

        for i, py_line in enumerate(pinyin_lines):
            y_pos = py_y1 + py_pad + i * py_line_spacing + py_line_spacing // 2
            draw.text(
                (VIDEO_WIDTH // 2, y_pos), py_line,
                fill=(255, 255, 255), font=font_pinyin,
                anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0)
            )

    # Branding at bottom - BOLDER
    branding_y = VIDEO_HEIGHT - 90
    rounded_rect(draw, (0, branding_y - 40, VIDEO_WIDTH, branding_y + 60),
                 30, fill=(0, 0, 0, 200))
    draw.text(
        (VIDEO_WIDTH // 2, branding_y),
        "VELOCITY CHINESE",
        fill=(255, 255, 255),
        font=font_branding,
        anchor="mm",
        stroke_width=3,  # THICKER stroke
        stroke_fill=(0, 0, 0)
    )

    if img.mode == 'RGBA':
        img = img.convert('RGB')

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    print(f"  ✓ Image: {Path(output_path).name}")
    return output_path


def rounded_rect(draw, bbox, radius, fill=None, outline=None, width=1):
    x1, y1, x2, y2 = bbox
    r = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)
    draw.pieslice([x1, y1, x1 + r*2, y1 + r*2], 180, 270, fill=fill)
    draw.pieslice([x2 - r*2, y1, x2, y1 + r*2], 270, 360, fill=fill)
    draw.pieslice([x1, y2 - r*2, x1 + r*2, y2], 90, 180, fill=fill)
    draw.pieslice([x2 - r*2, y2 - r*2, x2, y2], 0, 90, fill=fill)
    draw.rectangle([x1 + r, y1, x2 - r, y2], fill=fill)
    draw.rectangle([x1, y1 + r, x2, y2 - r], fill=fill)


# ============== VIDEO CREATION ==============

def _run_ffmpeg(cmd, max_retries: int = 3, timeout: int = 600):
    """Run an ffmpeg command with retries. Returns True on success."""
    import time
    for attempt in range(1, max_retries + 1):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            rc = result.returncode
            out = Path(cmd[-1])
            if rc == 0 and out.exists() and out.stat().st_size > 0:
                return True
            stderr_tail = (result.stderr or "")[-600:].replace("\n", " ")
            print(f"[video] ffmpeg attempt {attempt}/{max_retries} failed (rc={rc}): {stderr_tail}")
        except subprocess.TimeoutExpired as e:
            print(f"[video] ffmpeg attempt {attempt}/{max_retries} timed out: {e}")
        except Exception as e:
            print(f"[video] ffmpeg attempt {attempt}/{max_retries} exception: {e}")
        try:
            partial = Path(cmd[-1])
            if partial.exists():
                partial.unlink()
        except Exception:
            pass
        if attempt < max_retries:
            time.sleep(3)
    return False


def create_video_from_images_audio(image_files: list, audio_files: list, combined_audio: str, output_file: str):
    """Create video from images and audio with PERFECT synchronization"""

    print(f"\n[video] Creating video from {len(image_files)} images...")
    print(f"[video] Ensuring complete audio playback and sync...")

    temp_clips = []

    for i, (img_path, audio_info) in enumerate(zip(image_files, audio_files)):
        duration = audio_info['duration']
        print(f"  Image {i+1}/{len(image_files)}: {duration:.2f}s (EN: {audio_info.get('en_duration', 0):.1f}s + CN: {audio_info.get('cn_duration', 0):.1f}s)")

        temp_clip = Path(output_file).parent / f"temp_clip_{i:02d}.mp4"
        temp_clips.append(temp_clip)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            str(temp_clip)
        ]

        if not _run_ffmpeg(cmd):
            raise RuntimeError(f"Failed to create clip {i+1} after retries")

    # Concatenate clips
    print("[video] Concatenating clips...")
    temp_video = Path(output_file).parent / "temp_video.mp4"
    concat_file = Path(output_file).parent / "concat_list.txt"

    with open(concat_file, "w") as f:
        for clip in temp_clips:
            f.write(f"file '{clip.resolve().as_posix()}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(temp_video)]
    if not _run_ffmpeg(cmd):
        raise RuntimeError("Failed to concatenate clips after retries")

    # Add audio
    print("[video] Adding audio (ensuring complete playback)...")
    audio_duration = get_audio_duration(combined_audio)
    print(f"[video] Audio duration: {audio_duration:.2f}s")

    if not Path(combined_audio).exists() or Path(combined_audio).stat().st_size == 0:
        raise RuntimeError(f"Narration audio missing or empty: {combined_audio}")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(temp_video),
        "-i", str(combined_audio),
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        str(output_file)
    ]
    mux_ok = _run_ffmpeg(cmd)
    if not mux_ok:
        print("[video] Mux with -c:v copy failed, retrying with re-encode...")
        cmd = [
            "ffmpeg", "-y",
            "-i", str(temp_video),
            "-i", str(combined_audio),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
            "-c:a", "aac",
            "-shortest",
            str(output_file)
        ]
        if not _run_ffmpeg(cmd):
            raise RuntimeError("Failed to mux video+audio after retries")

    # Verify
    video_duration = get_audio_duration(str(output_file).replace(".mp4", ".mp4"))
    print(f"[video] ✓ Video created: {Path(output_file).name} ({video_duration:.2f}s)")

    # Cleanup
    for clip in temp_clips:
        if clip.exists():
            clip.unlink()
    if temp_video.exists():
        temp_video.unlink()
    if concat_file.exists():
        concat_file.unlink()


# ============== MAIN WORKFLOW ==============

def generate_reel(category_english: str = None):
    """Generate complete Facebook Reel"""

    if not category_english:
        category_english = random.choice(CATEGORIES_ENGLISH)

    print(f"\n{'='*80}")
    print(f"Category: {category_english} ({CATEGORIES_CHINESE[category_english]})")
    print(f"{'='*80}\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reel_dir = VIDEO_DIR / f"{category_english}_{timestamp}"
    reel_dir.mkdir(exist_ok=True)

    # Step 1: Generate unique phrases
    print("[1/4] Generating unique phrases (checking history)...")
    phrases = generate_phrases(category_english, num_phrases=5)

    for i, phrase in enumerate(phrases, 1):
        print(f"  {i}. {phrase['english']} → {phrase['chinese']}")

    # Step 2: Generate images
    print("\n[2/4] Generating images with impressive backgrounds...")
    for i, phrase in enumerate(phrases):
        output_path = reel_dir / f"phrase_{i:02d}.jpg"
        generate_complete_image(phrase, category_english, str(output_path))
        print(f"  ✓ Image {i+1}: {phrase['english'][:40]}...")

    # Step 3: Generate audio
    print("\n[3/4] Generating audio (English + Chinese with 500ms pause)...")
    audio_files = generate_all_audio(phrases, str(reel_dir))

    final_audio = reel_dir / "narration.mp3"
    create_final_narration(audio_files, str(final_audio))

    # Step 4: Create video - CRITICAL: Sort images for correct order
    print("\n[4/4] Creating video...")
    output_video = reel_dir / "final_reel.mp4"

    image_files = sorted([str(p) for p in reel_dir.glob("phrase_*.jpg")])

    create_video_from_images_audio(
        image_files,
        audio_files,
        str(final_audio),
        str(output_video)
    )

    # Save metadata
    metadata = {
        "category_english": category_english,
        "category_chinese": CATEGORIES_CHINESE[category_english],
        "timestamp": timestamp,
        "phrases": phrases,
        "video": str(output_video),
        "audio": str(final_audio)
    }

    with open(reel_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*80}")
    print(f"✅ REEL COMPLETE!")
    print(f"  📁 {reel_dir}")
    print(f"  🎬 {output_video.name}")
    print(f"  🏷️  Branding: Velocity Chinese")
    print(f"{'='*80}\n")

    return metadata


def generate_daily_content(times_per_day: int = 5):
    """
    Generate multiple reels per day (for GitHub Actions scheduled runs)
    
    Args:
        times_per_day: Number of reels to generate (default: 5)
    """
    print(f"\n🎬 Generating {times_per_day} reels for today...")
    print("="*80)
    
    for i in range(times_per_day):
        print(f"\n{'='*80}")
        print(f"🎬 REEL {i+1}/{times_per_day}")
        print("="*80)
        generate_reel()
    
    print("\n" + "="*80)
    print(f"✅ ALL {times_per_day} REELS COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🇨🇳 VELOCITY CHINESE - FACEBOOK REELS AUTOMATION 🇨🇳")
    print("="*80)
    print("\n✨ IMPROVED FEATURES:")
    print("  ✓ Natural pauses with commas (non-robotic TTS)")
    print("  ✓ Perfect audio-video synchronization")
    print("  ✓ Complete audio playback guaranteed")
    print("  ✓ English category names (for American/European learners)")
    print("  ✓ Velocity Chinese branding at bottom")
    print("  ✓ NEVER repeats phrases (permanent history tracking)")
    print(f"\n📊 AVAILABLE CATEGORIES ({len(CATEGORIES_ENGLISH)} total):")
    for i, cat in enumerate(CATEGORIES_ENGLISH, 1):
        print(f"   {i:2d}. {cat} ({CATEGORIES_CHINESE[cat]})")
    print(f"\n📅 DAILY CAPACITY:")
    print(f"  • 5 reels per day = 25 unique phrases daily")
    print(f"  • {len(CATEGORIES_ENGLISH)} categories = Over 5 days before any category repeats")
    print(f"  • Phrase history is PERMANENT (never deletes)")
    print(f"  • AI generates FRESH phrases every time")
    print("="*80)

    generate_reel()

    print("\n" + "="*80)
    print("✅ READY FOR DAILY AUTOMATION!")
    print("="*80)
    print("\nTo generate 5 reels for today:")
    print("  from facebook_reels_automation import generate_daily_content")
    print("  generate_daily_content(times_per_day=5)")
    print("\nTo generate a single reel:")
    print("  generate_reel('Love')  # Or any category from the list above")
    print("="*80)
