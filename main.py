import telebot
from telebot import types
import random, time, threading
from collections import defaultdict
import os

TOKEN = os.getenv("8918406710:AAFxHttlez3sytjiwK9_vG-ImmIxUsRoy7o")
if not TOKEN:
    raise RuntimeError(
        "Не задана переменная окружения TOKEN! "
        "Установи её перед запуском, например:\n"
        "  export TOKEN=твой_токен_бота   (Linux/Mac)\n"
        "  set TOKEN=твой_токен_бота      (Windows)\n"
        "или добавь TOKEN в настройки хостинга (Environment Variables)."
    )

bot = telebot.TeleBot(TOKEN)

# ══════════════════════════════════════════════════════════
#                        РОЛИ
# ══════════════════════════════════════════════════════════
ROLES = {
    # ── МАФИЯ ──
    "Дон Мафии": {
        "team": "mafia", "emoji": "👑",
        "desc": "Главарь. Подсосы предлагают жертву, Дон решает. Может проверить игрока ночью."
    },
    "Подсос": {
        "team": "mafia", "emoji": "🔫",
        "desc": "Предлагает Дону кандидата. Финальный выбор — за Доном."
    },
    "АЛЛАХУ АКБАР": {
        "team": "akbar", "emoji": "💥",
        "desc": "Нейтрал-камикадзе. Каждую ночь может взорваться — убивает себя И выбранную жертву. Побеждает если взорвался и унёс с собой хотя бы одного."
    },

    # ── НЕЙТРАЛЫ ──
    "Маньяк": {
        "team": "maniac", "emoji": "🔪",
        "desc": "Убивает каждую ночь. Победа — остаться одному."
    },
    "Серийный Убийца": {
        "team": "serial", "emoji": "☠️",
        "desc": "Убивает через ночь (устаёт). Победа — остаться одному."
    },
    "Оборотень": {
        "team": "werewolf", "emoji": "🐺",
        "desc": "Нейтрал. Если Шериф проверит — станет Сержантом. Если убьёт Дон — станет Подсосом."
    },
    "Поджигатель": {
        "team": "arsonist", "emoji": "🔥",
        "desc": "Каждую ночь минирует игроков или поджигает себя+всех заминированных. Победа — сжечь минимум 3 вместе с собой."
    },
    "Маг": {
        "team": "mage", "emoji": "🧙",
        "desc": "Если Шериф проверит или Дон убьёт — выживет и сможет убить обидчика. Использует один раз."
    },

    # ── МИРНЫЕ ──
    "Шериф": {
        "team": "citizen", "emoji": "🔍",
        "desc": "Проверяет точную роль игрока каждую ночь."
    },
    "Доктор": {
        "team": "citizen", "emoji": "💊",
        "desc": "Лечит одного игрока каждую ночь (себя — 1 раз за игру)."
    },
    "Диди": {
        "team": "citizen", "emoji": "💋",
        "desc": "Блокирует действие одного игрока на ночь."
    },
    "Телохранитель": {
        "team": "citizen", "emoji": "🛡",
        "desc": "Защищает одного — погибает вместо него."
    },
    "Хакер": {
        "team": "citizen", "emoji": "💻",
        "desc": "Автоматически узнаёт выбор Дона после нажатия кнопки."
    },
    "Гадалка": {
        "team": "citizen", "emoji": "🔮",
        "desc": "Проверяет живого игрока: видит 3 варианта роли, 1 из них правильный."
    },
    "Герой": {
        "team": "citizen", "emoji": "🦸",
        "desc": "Раз в игру воскрешает мёртвого. Тот становится Лохом ипани."
    },
    "Бомж": {
        "team": "citizen", "emoji": "🧟",
        "desc": "Каждую ночь ночует у одного из игроков. Если того убьют — Бомж узнаёт роль убийцы (команду). Неуязвим сам по себе, пока не надоест."
    },
    "Сержант": {
        "team": "citizen", "emoji": "🏅",
        "desc": "Помощник Шерифа. Также появляется когда Шериф проверяет Оборотня."
    },
    "Лох ипани": {
        "team": "citizen", "emoji": "🤡",
        "desc": "Обычный житель. Голосует днём. Ничего не умеет."
    }}

ROLE_DIST = {
    4:  ["Дон Мафии", "Шериф", "Лох ипани", "Лох ипани"],
    5:  ["Дон Мафии", "Шериф", "Доктор", "Лох ипани", "Лох ипани"],
    6:  ["Дон Мафии", "Подсос", "Шериф", "Доктор", "Лох ипани", "Лох ипани"],
    7:  ["Дон Мафии", "Подсос", "Шериф", "Доктор", "Диди", "Оборотень", "Лох ипани"],
    8:  ["Дон Мафии", "Подсос", "Маньяк", "Шериф", "Доктор", "Диди", "Бомж", "Лох ипани"],
    9:  ["Дон Мафии", "Подсос", "Маньяк", "Шериф", "Доктор", "Диди", "Телохранитель", "Сержант", "Лох ипани"],
    10: ["Дон Мафии", "Подсос", "АЛЛАХУ АКБАР", "Маньяк", "Шериф", "Доктор", "Диди", "Телохранитель", "Хакер", "Лох ипани"],
    11: ["Дон Мафии", "Подсос", "АЛЛАХУ АКБАР", "Маньяк", "Серийный Убийца", "Шериф", "Доктор", "Диди", "Телохранитель", "Хакер", "Лох ипани"],
    12: ["Дон Мафии", "Подсос", "АЛЛАХУ АКБАР", "Маньяк", "Серийный Убийца", "Шериф", "Доктор", "Диди", "Телохранитель", "Хакер", "Гадалка", "Лох ипани"],
    13: ["Дон Мафии", "Подсос", "Подсос", "АЛЛАХУ АКБАР", "Маньяк", "Оборотень", "Шериф", "Доктор", "Диди", "Телохранитель", "Хакер", "Герой", "Лох ипани"],
    14: ["Дон Мафии", "Подсос", "Подсос", "АЛЛАХУ АКБАР", "Маньяк", "Серийный Убийца", "Поджигатель", "Шериф", "Доктор", "Диди", "Телохранитель", "Хакер", "Гадалка", "Лох ипани"],
    15: ["Дон Мафии", "Подсос", "Подсос", "АЛЛАХУ АКБАР", "Маньяк", "Серийный Убийца", "Поджигатель", "Маг", "Шериф", "Доктор", "Диди", "Телохранитель", "Хакер", "Гадалка", "Лох ипани"],
    16: ["Дон Мафии", "Подсос", "Подсос", "АЛЛАХУ АКБАР", "Маньяк", "Серийный Убийца", "Поджигатель", "Маг", "Оборотень", "Шериф", "Доктор", "Диди", "Телохранитель", "Хакер", "Гадалка", "Лох ипани"],
    17: ["Дон Мафии", "Подсос", "Подсос", "Подсос", "АЛЛАХУ АКБАР", "Маньяк", "Серийный Убийца", "Поджигатель", "Маг", "Оборотень", "Шериф", "Доктор", "Диди", "Телохранитель", "Хакер", "Гадалка", "Лох ипани"],
    18: ["Дон Мафии", "Подсос", "Подсос", "Подсос", "Подсос", "АЛЛАХУ АКБАР", "Маньяк", "Серийный Убийца", "Поджигатель", "Оборотень", "Шериф", "Доктор", "Диди", "Телохранитель", "Хакер", "Гадалка", "Герой", "Лох ипани"],
}

# ══════════════════════════════════════════════════════════
#                    ХРАНИЛИЩЕ ИГР
# ══════════════════════════════════════════════════════════
games = {}

class GameState:
    def __init__(self, chat_id, creator_id):
        self.chat_id       = chat_id
        self.creator_id    = creator_id
        self.phase         = "lobby"
        self.players       = {}
        self.night_actions = {}
        self.mafia_suggestions = {}
        self.don_kill_target   = None
        self.day_votes     = {}
        self.day_num       = 0
        self.blocked       = set()
        self.protected     = None
        self.serial_skip   = False
        self.pop_used      = False
        self.sgt_used      = False
        self.timer         = None
        self.vote_msg_id   = None
        # Поджигатель
        self.mined         = set()
        self.arsonist_fired= False
        # Маг
        self.mage_triggered= False
        self.mage_revenge  = None
        # АЛЛАХУ АКБАР (нейтрал)
        self.kamikaze_used = False
        self.akbar_won     = False
        # Сержант
        self.sgt_vote      = {}
        self.sgt_target    = None
        self.sgt_action    = None   # "check" / "kill" — выбранное за ночь действие (только одно!)

    def alive_players(self):
        return {uid: p for uid, p in self.players.items() if p.get("alive", False)}

    def team_count(self, team):
        return sum(1 for p in self.players.values()
                   if p.get("alive", False) and ROLES[p["role"]]["team"] == team)

    def get_role(self, role_name):
        for uid, p in self.players.items():
            if p["role"] == role_name and p.get("alive", False):
                return uid
        return None

    def mafia_ids(self):
        return [uid for uid, p in self.players.items()
                if ROLES[p["role"]]["team"] == "mafia" and p.get("alive", False)]

    def dead_players(self):
        return {uid: p for uid, p in self.players.items() if not p.get("alive", False)}


# ══════════════════════════════════════════════════════════
#                       УТИЛИТЫ
# ══════════════════════════════════════════════════════════
def send(chat_id, text, **kwargs):
    try:
        return bot.send_message(chat_id, text, parse_mode="HTML", **kwargs)
    except Exception as e:
        print(f"[SEND ERR] {e}")

def pm(uid, text, markup=None):
    try:
        if markup:
            bot.send_message(uid, text, parse_mode="HTML", reply_markup=markup)
        else:
            bot.send_message(uid, text, parse_mode="HTML")
    except Exception as e:
        print(f"[PM ERR uid={uid}] {e}")

def bold(name): return f"<b>{name}</b>"
def pname(game, uid): return bold(game.players[uid]["name"])

def role_team_str(role):
    t = ROLES[role]["team"]
    return {
        "mafia":    "🔴 МАФИЯ",
        "citizen":  "🟢 Мирные",
        "maniac":   "🟣 Маньяк",
        "serial":   "⚫ Серийный убийца",
        "werewolf": "🐺 Оборотень",
        "arsonist": "🔥 Поджигатель",
        "mage":     "🧙 Маг",
        "akbar":    "💥 Нейтрал (АЛЛАХУ АКБАР)",
    }.get(t, t)

def check_win(game):
    mafia = game.team_count("mafia")
    citizens = game.team_count("citizen")

    if mafia == 0:
        return "citizen"

    if mafia >= citizens:
        return "mafia"

    return None


def announce_win(game, winner):
    winners = []
    losers = []

    for p in game.players.values():
        role = p["role"]
        team = ROLES[role]["team"]

        neutral_win = (
            (role in ["Маньяк", "Серийный Убийца", "Маг"] and p.get("alive", False))
            or (role == "Поджигатель" and getattr(game, "arsonist_fired", False))
            or (role == "АЛЛАХУ АКБАР" and getattr(game, "akbar_won", False))
        )

        ok = (team == winner) or neutral_win

        if ok:
            winners.append(p["name"])
        elif team not in ("citizen", "mafia"):
            losers.append(p["name"])

    texts = {
        "citizen": ("☀️", "Мирные победили!"),
        "mafia": ("🌑", "Мафия победила!")
    }

    em, txt = texts.get(winner, ("🏆", "Игра окончена"))

    reveal = "\n".join(
        f"{ROLES[p['role']]['emoji']} {p['name']} — {p['role']} {'✅' if p.get('alive', False) else '💀'}"
        for p in game.players.values()
    )

    msg = (
        f"{em} <b>{txt}</b>\n\n"
        f"🏆 Победители:\n" + "\n".join(winners)
    )

    if losers:
        msg += "\n\n🤡 Лошки:\n" + "\n".join(losers)

    msg += "\n\n<b>Роли:</b>\n" + reveal

    send(game.chat_id, msg)
    games.pop(game.chat_id, None)

# ══════════════════════════════════════════════════════════
#                         ЛОББИ
# ══════════════════════════════════════════════════════════
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    send(msg.chat.id,
        "🎭 <b>ДУГО МАФИЯ</b>\n\n"
        "/newgame — создать игру\n"
        "/join — войти\n"
        "/startgame — начать (4–18 игр.)\n"
        "/vote — досрочное голосование\n"
        "/status — живые/мёртвые\n"
        "/roles — все роли\n"
        "/endgame — завершить\n"
        "/help — справка и описание ролей\n\n"
        "⚡ Работает в темах Telegram!"
    )

def build_roles_text():
    groups = [
        ("🔴 МАФИЯ", ["Дон Мафии","Подсос"]),
        ("🟣 НЕЙТРАЛЫ", ["Маньяк","Серийный Убийца","Оборотень","Поджигатель","Маг","АЛЛАХУ АКБАР"]),
        ("🟢 МИРНЫЕ", ["Шериф","Доктор","Диди","Телохранитель","Хакер","Гадалка","Герой","Бомж","Сержант","Сержант","Лох ипани"]),
    ]
    text = "📖 <b>Все роли:</b>\n"
    for title, rlist in groups:
        text += f"\n{title}:\n"
        for r in rlist:
            if r in ROLES:
                ro = ROLES[r]
                text += f"{ro['emoji']} <b>{r}</b>\n  └ {ro['desc']}\n"
    return text

@bot.message_handler(commands=["roles"])
def cmd_roles(msg):
    send(msg.chat.id, build_roles_text())

@bot.message_handler(commands=["help"])
def cmd_help(msg):
    text = (
        "ℹ️ <b>СПРАВКА ПО ИГРЕ</b>\n\n"
        "/newgame — создать игру\n"
        "/join — войти в игру\n"
        "/startgame — начать (4–18 игроков)\n"
        "/vote — досрочное голосование днём\n"
        "/status — живые/мёртвые\n"
        "/roles — список всех ролей\n"
        "/endgame — завершить игру\n\n"
        + build_roles_text() +
        "\n🎬 <b>Титры:</b>\n"
        "👨‍💻 Кодер: @TLLetov\n"
        "🤝 Помощник: @ristocra"
    )
    send(msg.chat.id, text)

@bot.message_handler(commands=["newgame"])
def cmd_newgame(msg):
    cid = msg.chat.id
    if msg.chat.type == "private":
        send(cid, "❌ Только в групповом чате!"); return
    if cid in games:
        send(cid, "⚠️ Игра уже есть! /endgame — завершить."); return
    games[cid] = GameState(cid, msg.from_user.id)
    g = games[cid]
    uid, name = msg.from_user.id, msg.from_user.first_name
    g.players[uid] = {"name": name, "role": None, "alive": True, "healed_self": False}
    send(cid, f"🎭 <b>Игра создана!</b> Организатор: {bold(name)}\n\n/join — войти | /startgame — начать\n\nИгроки (1):\n1. {name}")

@bot.message_handler(commands=["join"])
def cmd_join(msg):
    cid = msg.chat.id
    if cid not in games:
        send(cid, "❌ /newgame сначала!"); return
    g = games[cid]
    if g.phase != "lobby":
        send(cid, "❌ Игра уже началась!"); return
    uid = msg.from_user.id
    if uid in g.players:
        send(cid, f"⚠️ {msg.from_user.first_name}, ты уже в игре!"); return
    if len(g.players) >= 18:
        send(cid, "❌ Максимум 18!"); return
    g.players[uid] = {"name": msg.from_user.first_name, "role": None, "alive": True, "healed_self": False}
    lst = "\n".join(f"{i+1}. {p['name']}" for i, p in enumerate(g.players.values()))
    send(cid, f"✅ <b>{msg.from_user.first_name}</b> вошёл!\n\nИгроки ({len(g.players)}):\n{lst}")

@bot.message_handler(commands=["startgame"])
def cmd_startgame(msg):
    cid = msg.chat.id
    if cid not in games: send(cid, "❌ /newgame сначала!"); return
    g = games[cid]
    if msg.from_user.id != g.creator_id:
        send(cid, "❌ Только организатор!"); return
    if g.phase != "lobby":
        send(cid, "⚠️ Игра уже идёт!"); return
    n = len(g.players)
    if n < 4: send(cid, f"❌ Минимум 4! Сейчас: {n}"); return
    if n > 18: send(cid, "❌ Максимум 18!"); return

    dist_key = max(k for k in ROLE_DIST if k <= n)
    role_list = list(ROLE_DIST[dist_key])
    while len(role_list) < n:
        role_list.append("Лох ипани")
    role_list = role_list[:n]
    random.shuffle(role_list)

    for uid, role in zip(g.players.keys(), role_list):
        g.players[uid]["role"] = role

    for uid, p in g.players.items():
        role = p["role"]
        r = ROLES[role]
        txt = (f"🎭 <b>Роль: {r['emoji']} {role}</b>\n"
               f"Команда: {role_team_str(role)}\n\n{r['desc']}")
        if r["team"] == "mafia":
            allies = [g.players[m]["name"] for m in g.mafia_ids() if m != uid]
            if allies:
                txt += f"\n\n🔫 Подельники: {', '.join(allies)}"
        pm(uid, txt)

    lst = "\n".join(f"{i+1}. {p['name']}" for i, p in enumerate(g.players.values()))
    send(cid, f"🎭 <b>Игра началась!</b>\nРоли в ЛС.\n⚠️ <i>Нет роли? Напишите боту /start в ЛС</i>\n\n<b>Игроки ({n}):</b>\n{lst}")
    time.sleep(1)
    start_night(g)

@bot.message_handler(commands=["endgame"])
def cmd_endgame(msg):
    cid = msg.chat.id
    if cid not in games: send(cid, "❌ Нет игры."); return
    g = games[cid]
    if msg.from_user.id not in g.players and msg.from_user.id != g.creator_id: return
    if g.timer: g.timer.cancel()
    del games[cid]
    send(cid, "🛑 Игра завершена.")

@bot.message_handler(commands=["status"])
def cmd_status(msg):
    cid = msg.chat.id
    if cid not in games: send(cid, "❌ Нет игры."); return
    g = games[cid]
    alive = g.alive_players()
    dead  = g.dead_players()
    text  = f"📊 <b>День {g.day_num} | {g.phase}</b>\n\n✅ Живые ({len(alive)}):\n"
    text += "\n".join(f"  • {p['name']}" for p in alive.values())
    if dead:
        text += f"\n\n💀 Мёртвые ({len(dead)}):\n"
        text += "\n".join(f"  • {p['name']} [{p['role']}]" for p in dead.values())
    send(cid, text)


# ══════════════════════════════════════════════════════════
#                      НОЧЬ — СТАРТ
# ══════════════════════════════════════════════════════════
def start_night(game):
    game.phase = "night"
    game.day_num += 1
    game.night_actions = {}
    game.mafia_suggestions = {}
    game.don_kill_target = None
    game.blocked = set()
    game.protected = None
    game.mage_revenge = None
    game.sgt_action = None

    send(game.chat_id,
        f"🌑 <b>Ночь {game.day_num}</b>\n\nЧекайте личку! ⏳ <b>40 секунд</b>.")

    alive = game.alive_players()

    # ── ПОДСОСЫ: предложить жертву Дону ──
    for mid in game.mafia_ids():
        if game.players[mid]["role"] == "Подсос":
            targets = {uid: p for uid, p in alive.items()
                       if ROLES[p["role"]]["team"] not in ("mafia",)}
            if not targets: continue
            kb = types.InlineKeyboardMarkup()
            for tid, tp in targets.items():
                kb.add(types.InlineKeyboardButton(tp["name"], callback_data=f"suggest_{game.chat_id}_{mid}_{tid}"))
            pm(mid, "🔫 <b>Подсос</b>: предложи жертву Дону:", kb)

    # ── ДОН: проверка ──
    don_id = game.get_role("Дон Мафии")
    if don_id:
        targets = {uid: p for uid, p in alive.items() if uid != don_id}
        if targets:
            kb = types.InlineKeyboardMarkup()
            for tid, tp in targets.items():
                kb.add(types.InlineKeyboardButton(tp["name"], callback_data=f"don_check_{game.chat_id}_{don_id}_{tid}"))
            pm(don_id, "👑 <b>Дон</b>: кого проверить? (необязательно)", kb)
        threading.Timer(15.0, lambda: send_don_kill_menu(game)).start()

    # ── АЛЛАХУ АКБАР (нейтрал) ──
    akbar_id = game.get_role("АЛЛАХУ АКБАР")
    if akbar_id and akbar_id not in game.blocked:
        targets = {uid: p for uid, p in alive.items() if uid != akbar_id}
        if targets:
            kb = types.InlineKeyboardMarkup()
            for tid, tp in targets.items():
                kb.add(types.InlineKeyboardButton(tp["name"], callback_data=f"akbar_{game.chat_id}_{akbar_id}_{tid}"))
            kb.add(types.InlineKeyboardButton("❌ Не взрываться", callback_data=f"akbar_{game.chat_id}_{akbar_id}_skip"))
            pm(akbar_id,
               "💥 <b>АЛЛАХУ АКБАР!</b>\nТы нейтральный камикадзе!\n"
               "Каждую ночь можешь взорваться — убьёшь СЕБЯ и выбранную цель.\n"
               "Победа — взорваться и унести хотя бы одного!\n\nКого возьмёшь с собой?", kb)

    # ── ШЕРИФ ──
    sher_id = game.get_role("Шериф")
    if sher_id:
        targets = {uid: p for uid, p in alive.items() if uid != sher_id}
        if targets:
            kb = types.InlineKeyboardMarkup()
            for tid, tp in targets.items():
                kb.add(types.InlineKeyboardButton(tp["name"], callback_data=f"sheriff_{game.chat_id}_{sher_id}_{tid}"))
            pm(sher_id, "🔍 <b>Шериф</b>: кого проверить?", kb)

    # ── ДОКТОР ──
    doc_id = game.get_role("Доктор")
    if doc_id:
        targets = dict(alive)
        if game.players[doc_id]["healed_self"]: targets.pop(doc_id, None)
        if targets:
            kb = types.InlineKeyboardMarkup()
            for tid, tp in targets.items():
                kb.add(types.InlineKeyboardButton(tp["name"], callback_data=f"doctor_{game.chat_id}_{doc_id}_{tid}"))
            pm(doc_id, "💊 <b>Доктор</b>: кого лечить?", kb)

    # ── ДИДИ ──
    lov_id = game.get_role("Диди")
    if lov_id:
        targets = {uid: p for uid, p in alive.items() if uid != lov_id}
        if targets:
            kb = types.InlineKeyboardMarkup()
            for tid, tp in targets.items():
                kb.add(types.InlineKeyboardButton(tp["name"], callback_data=f"lover_{game.chat_id}_{lov_id}_{tid}"))
            pm(lov_id, "💋 <b>Диди</b>: кого выебать?", kb)

    # ── ТЕЛОХРАНИТЕЛЬ ──
    body_id = game.get_role("Телохранитель")
    if body_id:
        targets = {uid: p for uid, p in alive.items() if uid != body_id}
        if targets:
            kb = types.InlineKeyboardMarkup()
            for tid, tp in targets.items():
                kb.add(types.InlineKeyboardButton(tp["name"], callback_data=f"bodyguard_{game.chat_id}_{body_id}_{tid}"))
            pm(body_id, "🛡 <b>Телохранитель</b>: кого защитить?", kb)

    # ── ХАКЕР ──
    hack_id = game.get_role("Хакер")
    if hack_id:
        pm(hack_id, "💻 <b>Хакер</b>: автоматически перехватишь выбор Дона.")

    # ── ГАДАЛКА ──
    gad_id = game.get_role("Гадалка")
    if gad_id:
        targets = {uid: p for uid, p in alive.items() if uid != gad_id}
        if targets:
            kb = types.InlineKeyboardMarkup()
            for tid, tp in targets.items():
                kb.add(types.InlineKeyboardButton(tp["name"], callback_data=f"fortune_{game.chat_id}_{gad_id}_{tid}"))
            pm(gad_id, "🔮 <b>Гадалка</b>: кого проверить? Получишь 3 варианта роли (1 правильный):", kb)

    # ── ГЕРОЙ ──
    hero_id = game.get_role("Герой")
    if hero_id and not game.pop_used:
        dead = game.dead_players()
        if dead:
            kb = types.InlineKeyboardMarkup()
            for tid, tp in dead.items():
                kb.add(types.InlineKeyboardButton(f"💀 {tp['name']}", callback_data=f"hero_{game.chat_id}_{hero_id}_{tid}"))
            kb.add(types.InlineKeyboardButton("❌ Не воскрешать", callback_data=f"hero_{game.chat_id}_{hero_id}_skip"))
            pm(hero_id, "🦸 <b>Герой</b>: воскресить кого-то? (раз в игру)", kb)

    # ── БОМЖ ──
    hobo_id = game.get_role("Бомж")
    if hobo_id:
        targets = {uid: p for uid, p in alive.items() if uid != hobo_id}
        if targets:
            kb = types.InlineKeyboardMarkup()
            for tid, tp in targets.items():
                kb.add(types.InlineKeyboardButton(f"🏠 {tp['name']}", callback_data=f"hobo_{game.chat_id}_{hobo_id}_{tid}"))
            pm(hobo_id, "🧟 <b>Бомж</b>: к кому пойдёшь ночевать?\nЕсли его убьют — узнаешь кто это сделал!", kb)

    # ── СЕРЖАНТ (помощник шерифа) — выбор действия ──
    sgt_id = game.get_role("Сержант")
    if sgt_id and sgt_id not in game.blocked:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔍 Проверить игрока", callback_data=f"sgt_action_{game.chat_id}_{sgt_id}_check"))
        kb.add(types.InlineKeyboardButton("💀 Проголосовать за убийство", callback_data=f"sgt_action_{game.chat_id}_{sgt_id}_kill"))
        pm(sgt_id, "🎖 <b>Сержант</b>: что делаешь этой ночью?", kb)


    man_id = game.get_role("Маньяк")
    if man_id:
        targets = {uid: p for uid, p in alive.items() if uid != man_id}
        if targets:
            kb = types.InlineKeyboardMarkup()
            for tid, tp in targets.items():
                kb.add(types.InlineKeyboardButton(tp["name"], callback_data=f"maniac_{game.chat_id}_{man_id}_{tid}"))
            pm(man_id, "🔪 <b>Маньяк</b>: кого убить?", kb)

    # ── СЕРИЙНЫЙ УБИЙЦА ──
    ser_id = game.get_role("Серийный Убийца")
    if ser_id:
        if game.serial_skip:
            pm(ser_id, "☠️ <b>Серийный</b>: эта ночь — отдых. Пропускаешь.")
            game.serial_skip = False
        else:
            targets = {uid: p for uid, p in alive.items() if uid != ser_id}
            if targets:
                kb = types.InlineKeyboardMarkup()
                for tid, tp in targets.items():
                    kb.add(types.InlineKeyboardButton(tp["name"], callback_data=f"serial_{game.chat_id}_{ser_id}_{tid}"))
                pm(ser_id, "☠️ <b>Серийный Убийца</b>: кого убить?", kb)
            game.serial_skip = True

    # ── ПОДЖИГАТЕЛЬ ──
    ars_id = game.get_role("Поджигатель")
    if ars_id and ars_id not in game.blocked:
        targets = {uid: p for uid, p in alive.items() if uid != ars_id}
        if targets:
            kb = types.InlineKeyboardMarkup()
            for tid, tp in targets.items():
                kb.add(types.InlineKeyboardButton(f"💣 {tp['name']}", callback_data=f"ars_mine_{game.chat_id}_{ars_id}_{tid}"))
            mined_count = len(game.mined)
            txt = (f"🔥 <b>Поджигатель</b>: заминировано {mined_count} чел.\n"
                   f"Выбери кого заминировать ИЛИ:")
            if mined_count >= 3:
                kb.add(types.InlineKeyboardButton("🔥 ПОДЖЕЧЬ ВСЕХ!", callback_data=f"ars_fire_{game.chat_id}_{ars_id}"))
            else:
                kb.add(types.InlineKeyboardButton(f"🔥 Поджечь (сейчас {mined_count} — нужно 3)", callback_data=f"ars_fire_{game.chat_id}_{ars_id}"))
            pm(ars_id, txt, kb)

    # ── МАГ ──
    mag_id = game.get_role("Маг")
    if mag_id:
        pm(mag_id, "🧙 <b>Маг</b>: ты в безопасности — если на тебя нападут, ты выживешь и сможешь отомстить.")

    # Таймер
    t = threading.Timer(40.0, lambda: resolve_night(game))
    game.timer = t
    t.start()


def send_don_kill_menu(game):
    if game.phase != "night": return
    don_id = game.get_role("Дон Мафии")
    if not don_id: return
    alive = game.alive_players()
    targets = {uid: p for uid, p in alive.items() if ROLES[p["role"]]["team"] != "mafia"}
    if not targets: return

    suggest_info = ""
    for sub_id, tgt_id in game.mafia_suggestions.items():
        sn = game.players[sub_id]["name"]
        tn = game.players[tgt_id]["name"] if tgt_id in game.players else "?"
        suggest_info += f"\n  🔫 {sn} → {bold(tn)}"

    kb = types.InlineKeyboardMarkup()
    for tid, tp in targets.items():
        kb.add(types.InlineKeyboardButton(tp["name"], callback_data=f"don_kill_{game.chat_id}_{don_id}_{tid}"))
    kb.add(types.InlineKeyboardButton("💤 Не убивать", callback_data=f"don_kill_{game.chat_id}_{don_id}_skip"))
    pm(don_id,
       f"👑 <b>Дон</b>, выбери жертву!\nПредложения:{suggest_info if suggest_info else ' нет'}", kb)


# ══════════════════════════════════════════════════════════
#               КОЛБЭКИ НОЧНЫХ ДЕЙСТВИЙ
# ══════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda c: c.data.startswith("suggest_"))
def cb_suggest(call):
    _, cid, mid, tid = call.data.split("_")
    cid, mid, tid = int(cid), int(mid), int(tid)
    if cid not in games: return
    g = games[cid]
    if g.phase != "night": return
    g.mafia_suggestions[mid] = tid
    bot.answer_callback_query(call.id, f"✅ Предложено: {g.players[tid]['name']}")
    don_id = g.get_role("Дон Мафии")
    if don_id:
        pm(don_id, f"📩 <b>{g.players[mid]['name']}</b> предлагает: {bold(g.players[tid]['name'])}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("don_kill_"))
def cb_don_kill(call):
    parts = call.data.split("_")
    cid, did, tid = int(parts[2]), int(parts[3]), parts[4]
    if cid not in games: return
    g = games[cid]
    if g.phase != "night": return
    if tid == "skip":
        g.don_kill_target = None
        bot.answer_callback_query(call.id, "💤 Не убиваешь.")
        pm(did, "💤 Решил не убивать.")
    else:
        tid = int(tid)
        # МАГ — защита
        if g.players[tid]["role"] == "Маг" and not g.mage_triggered:
            g.mage_triggered = True
            g.mage_revenge = did
            pm(tid, f"🧙 <b>Маг</b>: Дон пытался убить тебя! Ты выжил!\nОтомстить Дону?")
            threading.Timer(0.5, lambda: send_mage_revenge(g, tid, did)).start()
            bot.answer_callback_query(call.id, "⚡ Маг выжил!")
            pm(did, "🧙 Маг отразил удар! Он жив.")
            return
        g.don_kill_target = tid
        bot.answer_callback_query(call.id, f"✅ Цель: {g.players[tid]['name']}")
        pm(did, f"✅ Убиваешь: {bold(g.players[tid]['name'])}")
        hack_id = g.get_role("Хакер")
        if hack_id and hack_id not in g.blocked:
            pm(hack_id, f"💻 <b>Хакер</b>: Дон выбрал {bold(g.players[tid]['name'])}!")

@bot.callback_query_handler(func=lambda c: c.data.startswith("don_check_"))
def cb_don_check(call):
    parts = call.data.split("_")
    cid, did, tid = int(parts[2]), int(parts[3]), int(parts[4])
    if cid not in games: return
    g = games[cid]
    if g.phase != "night": return
    role = g.players[tid]["role"]
    res = "🔴 МАФИЯ" if ROLES[role]["team"] == "mafia" else "🟢 не мафия"
    pm(did, f"👑 Проверил {bold(g.players[tid]['name'])}: {res}")
    bot.answer_callback_query(call.id, "Проверено!")

@bot.callback_query_handler(func=lambda c: c.data.startswith("akbar_"))
def cb_akbar(call):
    parts = call.data.split("_")
    cid, aid, tid = int(parts[1]), int(parts[2]), parts[3]
    if cid not in games: return
    g = games[cid]
    if g.phase != "night": return
    if tid == "skip":
        bot.answer_callback_query(call.id, "💤 Эту ночь отдыхаешь.")
        pm(aid, "💤 Решил не взрываться этой ночью. Жди следующей!")
        return
    if aid in g.blocked:
        pm(aid, "💋 Диди тебя выебал — взрыв отменён!")
        bot.answer_callback_query(call.id, "Заблокирован!"); return
    tid = int(tid)
    g.night_actions["АЛЛАХУ АКБАР"] = tid
    # akbar_won выставляется в resolve_night только если жертва реально умерла
    bot.answer_callback_query(call.id, f"💥 АЛЛАХУ АКБАР! Взрываешь {g.players[tid]['name']}!")
    pm(aid, f"💥 <b>АЛЛАХУ АКБАР!</b> Ты уходишь вместе с {bold(g.players[tid]['name'])}! ☁️")

@bot.callback_query_handler(func=lambda c: c.data.startswith("sheriff_"))
def cb_sheriff(call):
    parts = call.data.split("_")
    cid, sid, tid = int(parts[1]), int(parts[2]), int(parts[3])

    if cid not in games:
        return

    g = games[cid]

    if g.phase != "night":
        return

    if sid in g.blocked:
        pm(sid, "💋 Диди тебя выебал — проверка отменена!")
        bot.answer_callback_query(call.id, "Заблокирован!")
        return

    role = g.players[tid]["role"]
    r = ROLES[role]

    if role == "Оборотень":
        g.players[tid]["role"] = "Сержант"

        pm(
            sid,
            f"🔍 Проверил {bold(g.players[tid]['name'])}: 🐺 Оборотень → теперь стал 🏅 Сержантом!"
        )

        pm(
            tid,
            "🎖 Шериф проверил тебя! Теперь ты 🏅 Сержант."
        )

    elif role == "Маг" and not g.mage_triggered:
        g.mage_triggered = True
        g.mage_revenge = sid

        pm(sid, "🧙 Маг отразил проверку! Он жив.")
        pm(tid, "🧙 Шериф проверял тебя!")

        threading.Timer(
            0.5,
            lambda: send_mage_revenge(g, tid, sid)
        ).start()

    else:
        pm(
            sid,
            f"🔍 {bold(g.players[tid]['name'])}: {r['emoji']} {role} ({role_team_str(role)})"
        )

    bot.answer_callback_query(call.id, "Проверено!")

@bot.callback_query_handler(func=lambda c: c.data.startswith("doctor_"))
def cb_doctor(call):
    parts = call.data.split("_")
    cid, did, tid = int(parts[1]), int(parts[2]), int(parts[3])
    if cid not in games: return
    g = games[cid]
    if g.phase != "night": return
    if did in g.blocked:
        pm(did, "💋 Диди тебя выебал — лечение отменено!")
        bot.answer_callback_query(call.id, "Заблокирован!"); return
    g.night_actions["Доктор"] = tid
    if tid == did: g.players[did]["healed_self"] = True
    bot.answer_callback_query(call.id, f"✅ Лечишь {g.players[tid]['name']}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("lover_"))
def cb_lover(call):
    parts = call.data.split("_")
    cid, lid, tid = int(parts[1]), int(parts[2]), int(parts[3])
    if cid not in games: return
    g = games[cid]
    if g.phase != "night": return
    g.blocked.add(tid)
    bot.answer_callback_query(call.id, f"💋 {g.players[tid]['name']} Выебан")

@bot.callback_query_handler(func=lambda c: c.data.startswith("bodyguard_"))
def cb_bodyguard(call):
    parts = call.data.split("_")
    cid, bid, tid = int(parts[1]), int(parts[2]), int(parts[3])
    if cid not in games: return
    g = games[cid]
    if g.phase != "night": return
    g.protected = tid
    bot.answer_callback_query(call.id, f"🛡 Защищаешь {g.players[tid]['name']}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("fortune_"))
def cb_fortune(call):
    parts = call.data.split("_")
    cid, gid, tid = int(parts[1]), int(parts[2]), int(parts[3])
    if cid not in games: return
    g = games[cid]
    if g.phase != "night": return
    if gid in g.blocked:
        pm(gid, "💋 Диди тебя выебал — гадание отменено!")
        bot.answer_callback_query(call.id, "Заблокирован!"); return
    real_role = g.players[tid]["role"]
    all_roles = [r for r in ROLES.keys() if r != real_role and r != "Сержант"]
    fake_roles = random.sample(all_roles, min(2, len(all_roles)))
    options = [real_role] + fake_roles
    random.shuffle(options)
    text = f"🔮 <b>Гадалка</b> смотрит на {bold(g.players[tid]['name'])}:\n\nОдна из этих ролей — правильная:\n"
    for i, r in enumerate(options, 1):
        text += f"{i}. {ROLES[r]['emoji']} {r}\n"
    pm(gid, text)
    bot.answer_callback_query(call.id, "Карты открыты!")

@bot.callback_query_handler(func=lambda c: c.data.startswith("hero_"))
def cb_hero(call):
    parts = call.data.split("_")
    cid, hid, tid = int(parts[1]), int(parts[2]), parts[3]
    if cid not in games: return
    g = games[cid]
    if g.pop_used:
        bot.answer_callback_query(call.id, "Уже использовал!"); return
    if tid == "skip":
        bot.answer_callback_query(call.id, "Пропустил."); return
    tid = int(tid)
    g.night_actions["Герой"] = tid
    g.pop_used = True
    bot.answer_callback_query(call.id, f"🦸 {g.players[tid]['name']} воскреснет!")
    pm(int(hid), f"🦸 Воскрешаешь {bold(g.players[tid]['name'])}!")

@bot.callback_query_handler(func=lambda c: c.data.startswith("hobo_"))
def cb_hobo(call):
    parts = call.data.split("_")
    cid, hid, tid = int(parts[1]), int(parts[2]), int(parts[3])
    if cid not in games: return
    g = games[cid]
    if g.phase != "night": return
    g.night_actions["Бомж"] = tid
    tname = g.players[tid]["name"]
    bot.answer_callback_query(call.id, f"🏠 Ночуешь у {tname}")
    pm(hid, f"🏠 Ночуешь у {bold(tname)}. Если его убьют — узнаешь кто!")

@bot.callback_query_handler(func=lambda c: c.data.startswith("sgt_action_"))
def cb_sgt_action(call):
    parts = call.data.split("_")
    cid, sid, action = int(parts[2]), int(parts[3]), parts[4]
    if cid not in games: return
    g = games[cid]
    if g.phase != "night": return
    if g.sgt_action is not None:
        bot.answer_callback_query(call.id, "❌ Ты уже выбрал действие этой ночью!")
        pm(sid, "🎖 Ты уже выбрал действие этой ночью — нельзя сделать и проверку, и голос за убийство одновременно.")
        return
    alive = g.alive_players()
    targets = {uid: p for uid, p in alive.items() if uid != sid}
    if not targets:
        bot.answer_callback_query(call.id, "Нет целей!"); return
    g.sgt_action = action
    kb = types.InlineKeyboardMarkup()
    if action == "check":
        for tid, tp in targets.items():
            kb.add(types.InlineKeyboardButton(tp["name"], callback_data=f"sgt_check_{cid}_{sid}_{tid}"))
        pm(sid, "🔍 <b>Сержант</b>: кого проверить? (мафия / не мафия)", kb)
        bot.answer_callback_query(call.id, "Выбери кого проверить")
    else:  # kill
        for tid, tp in targets.items():
            kb.add(types.InlineKeyboardButton(tp["name"], callback_data=f"sgt_kill_{cid}_{sid}_{tid}"))
        pm(sid, "💀 <b>Сержант</b>: за кого проголосовать на убийство?\n(цель умрёт этой ночью, если тебя не заблокируют)", kb)
        bot.answer_callback_query(call.id, "Выбери цель")

@bot.callback_query_handler(func=lambda c: c.data.startswith("sgt_check_"))
def cb_sgt_check(call):
    parts = call.data.split("_")
    cid, sid, tid = int(parts[2]), int(parts[3]), int(parts[4])
    if cid not in games: return
    g = games[cid]
    if g.phase != "night": return
    if g.sgt_action != "check":
        bot.answer_callback_query(call.id, "❌ Действие недействительно!"); return
    if sid in g.blocked:
        pm(sid, "💋 Диди тебя выебал — проверка отменена!")
        bot.answer_callback_query(call.id, "Заблокирован!"); return
    role = g.players[tid]["role"]
    is_m = "🔴 МАФИЯ" if ROLES[role]["team"] == "mafia" else "🟢 не мафия"
    pm(sid, f"🏅 Сержант проверил {bold(g.players[tid]['name'])}: {is_m}")
    bot.answer_callback_query(call.id, "Проверено!")

@bot.callback_query_handler(func=lambda c: c.data.startswith("sgt_kill_"))
def cb_sgt_kill(call):
    parts = call.data.split("_")
    cid, sid, tid = int(parts[2]), int(parts[3]), int(parts[4])
    if cid not in games: return
    g = games[cid]
    if g.phase != "night": return
    if g.sgt_action != "kill":
        bot.answer_callback_query(call.id, "❌ Действие недействительно!"); return
    if sid in g.blocked:
        pm(sid, "💋 Диди тебя выебал — голос отменён!")
        bot.answer_callback_query(call.id, "Заблокирован!"); return
    tname = g.players[tid]["name"]
    g.night_actions["Сержант_цель"] = tid
    pm(sid, f"💀 Ты проголосовал за расстрел {bold(tname)}! Цель умрёт этой ночью.")
    bot.answer_callback_query(call.id, f"Голос отдан: {tname}")


@bot.callback_query_handler(func=lambda c: c.data.startswith("maniac_"))
def cb_maniac(call):
    parts = call.data.split("_")
    cid, mid, tid = int(parts[1]), int(parts[2]), int(parts[3])
    if cid not in games: return
    g = games[cid]
    if g.phase != "night": return
    if mid in g.blocked:
        pm(mid, "💋 Диди тебя выебал — убийство отменено!")
        bot.answer_callback_query(call.id, "Заблокирован!"); return
    g.night_actions["Маньяк"] = tid
    bot.answer_callback_query(call.id, f"🔪 Цель: {g.players[tid]['name']}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("serial_"))
def cb_serial(call):
    parts = call.data.split("_")
    cid, sid, tid = int(parts[1]), int(parts[2]), int(parts[3])
    if cid not in games: return
    g = games[cid]
    if g.phase != "night": return
    if sid in g.blocked:
        pm(sid, "💋 Диди тебя выебал — убийство отменено!")
        bot.answer_callback_query(call.id, "Заблокирован!"); return
    g.night_actions["Серийный Убийца"] = tid
    bot.answer_callback_query(call.id, f"☠️ Цель: {g.players[tid]['name']}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("ars_mine_"))
def cb_ars_mine(call):
    parts = call.data.split("_")
    cid, aid, tid = int(parts[2]), int(parts[3]), int(parts[4])
    if cid not in games: return
    g = games[cid]
    if g.phase != "night": return
    if aid in g.blocked:
        pm(aid, "💋 Диди тебя выебал — минирование отменено!")
        bot.answer_callback_query(call.id, "Заблокирован!"); return
    g.mined.add(tid)
    tname = g.players[tid]["name"]
    bot.answer_callback_query(call.id, f"💣 {tname} заминирован!")
    pm(aid, f"💣 <b>{tname}</b> заминирован. Всего заминировано: {len(g.mined)}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("ars_fire_"))
def cb_ars_fire(call):
    parts = call.data.split("_")
    cid, aid = int(parts[2]), int(parts[3])
    if cid not in games: return
    g = games[cid]
    if g.phase != "night": return
    if len(g.mined) < 3:
        bot.answer_callback_query(call.id, f"❌ Нужно 3+ заминированных! Сейчас: {len(g.mined)}")
        return
    if aid in g.blocked:
        pm(aid, "💋 Диди тебя выебал — поджог отменён!")
        bot.answer_callback_query(call.id, "Заблокирован!"); return
    g.night_actions["Поджигатель"] = "fire"
    g.arsonist_fired = True
    bot.answer_callback_query(call.id, "🔥 ПОДЖИГАЕШЬ ВСЕХ!")
    pm(aid, "🔥 <b>ВСЁ ГОРИТ!</b> Ты поджигаешь себя и всех заминированных!")


# Маг — месть
def send_mage_revenge(game, mag_id, enemy_id):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(f"⚡ Убить {game.players[enemy_id]['name']}", callback_data=f"mage_kill_{game.chat_id}_{mag_id}_{enemy_id}"))
    kb.add(types.InlineKeyboardButton("🕊 Простить", callback_data=f"mage_kill_{game.chat_id}_{mag_id}_skip"))
    pm(mag_id, "🧙 <b>Маг</b>: отомстить обидчику?", kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("mage_kill_"))
def cb_mage_kill(call):
    parts = call.data.split("_")
    cid, mid, tid = int(parts[2]), int(parts[3]), parts[4]
    if cid not in games: return
    g = games[cid]
    if tid == "skip":
        pm(mid, "🕊 Простил обидчика.")
        bot.answer_callback_query(call.id, "Простил."); return
    tid = int(tid)
    g.night_actions["Маг_месть"] = tid
    bot.answer_callback_query(call.id, f"⚡ Мстишь {g.players[tid]['name']}!")
    pm(mid, f"⚡ Убиваешь {bold(g.players[tid]['name'])}!")


# ══════════════════════════════════════════════════════════
#                   РАЗРЕШЕНИЕ НОЧИ
# ══════════════════════════════════════════════════════════
def resolve_night(game):
    if game.phase != "night": return

    dead = []
    healed_id = game.night_actions.get("Доктор")
    body_id   = game.get_role("Телохранитель")
    prot_id   = game.protected
    revive_id = game.night_actions.get("Герой")

    def try_kill(target_id, killer_team="?"):
        if target_id is None: return False
        if not game.players[target_id]["alive"]: return False
        if target_id == healed_id:
            send(game.chat_id, f"💊 Доктор кого-то спас этой ночью!")
            # Бомж узнаёт если спасённый — его хозяин
            hobo_host = game.night_actions.get("Бомж")
            if hobo_host == target_id:
                hobo_id = game.get_role("Бомж")
                if hobo_id:
                    pm(hobo_id, f"🧟 Твоего хозяина {bold(game.players[target_id]['name'])} пытались убить, но Доктор спас! Убийца — команда: {killer_team}")
            return False
        if target_id == prot_id and body_id and game.players[body_id]["alive"]:
            game.players[body_id]["alive"] = False
            dead.append(body_id)
            send(game.chat_id, f"🛡 {pname(game, body_id)} (Телохранитель) погиб, защищая жертву!")
            return False
        game.players[target_id]["alive"] = False
        dead.append(target_id)
        # Бомж узнаёт кто убил его хозяина
        hobo_host = game.night_actions.get("Бомж")
        if hobo_host == target_id:
            hobo_id = game.get_role("Бомж")
            if hobo_id and hobo_id != target_id:
                pm(hobo_id,
                   f"🧟 <b>Бомж</b>: твоего хозяина {bold(game.players[target_id]['name'])} убили!\n"
                   f"Убийца из команды: <b>{killer_team}</b>")
        return True

    # Мафия убивает
    if game.don_kill_target:
        target = game.don_kill_target
        # Оборотень убит мафией → становится мафией
        if game.players[target]["role"] == "Оборотень":
            game.players[target]["role"] = "Подсос"
            send(game.chat_id, f"🐺 {pname(game, target)} был укушен мафией — стал одним из них!")
            pm(target, "🐺 Мафия убила тебя... Но ты стал <b>Подсосом</b> и теперь в их команде!")
        else:
            try_kill(target, "🔴 Мафия")

    # АЛЛАХУ АКБАР — нейтрал, взрывается сам и убивает цель
    akbar_target = game.night_actions.get("АЛЛАХУ АКБАР")
    if akbar_target:
        akbar_id = None
        for uid, p in game.players.items():
            if p["role"] == "АЛЛАХУ АКБАР": akbar_id = uid; break
        if akbar_id and game.players[akbar_id]["alive"]:
            game.players[akbar_id]["alive"] = False
            dead.append(akbar_id)
            send(game.chat_id, f"💥 <b>АЛЛАХУ АКБАР!</b> {pname(game, akbar_id)} взорвался во имя победы!")
        if try_kill(akbar_target, "💥 АЛЛАХУ АКБАР"):
            game.akbar_won = True

    # Маньяк
    try_kill(game.night_actions.get("Маньяк"), "🔪 Маньяк")

    # Серийный убийца
    try_kill(game.night_actions.get("Серийный Убийца"), "☠️ Серийный убийца")

    # Сержант — голос за убийство (реально убивает цель)
    try_kill(game.night_actions.get("Сержант_цель"), "🏅 Сержант")

    # Поджигатель — поджог
    if game.night_actions.get("Поджигатель") == "fire":
        ars_id = game.get_role("Поджигатель")
        if not ars_id:
            for uid, p in game.players.items():
                if p["role"] == "Поджигатель": ars_id = uid; break
        burned = list(game.mined)
        victims_names = []
        for uid in burned:
            if game.players[uid]["alive"]:
                game.players[uid]["alive"] = False
                dead.append(uid)
                victims_names.append(game.players[uid]["name"])
        if ars_id and game.players[ars_id]["alive"]:
            game.players[ars_id]["alive"] = False
            dead.append(ars_id)
        names_str = ", ".join(victims_names) if victims_names else "никто"
        send(game.chat_id, f"🔥 <b>ПОДЖИГАТЕЛЬ ПОДЖОГ ВСЕХ!</b>\nСгорели: {names_str}")

    # Маг — месть
    mag_revenge = game.night_actions.get("Маг_месть")
    if mag_revenge:
        try_kill(mag_revenge, "🧙 Маг")

    # Воскрешение Героем
    if revive_id and not game.players[revive_id]["alive"]:
        game.players[revive_id]["alive"] = True
        old_role = game.players[revive_id]["role"]
        game.players[revive_id]["role"] = "Лох ипани"
        send(game.chat_id,
             f"🦸 <b>Герой воскресил</b> {pname(game, revive_id)}!\n(Был {old_role}, теперь Лох ипани)")
        pm(revive_id, "🦸 Ты воскрешён! Теперь ты — 🤡 Лох ипани.")
        if revive_id in dead: dead.remove(revive_id)

    # Объявление погибших
    if dead:
        lines = "\n".join(
            f"💀 {pname(game, d)} — {ROLES[game.players[d]['role']]['emoji']} {game.players[d]['role']}"
            for d in dead
        )
        send(game.chat_id, f"🌅 <b>Ночь прошла...\n\nПогибли:</b>\n{lines}")
    else:
        send(game.chat_id, "🌅 <b>Ночь прошла без жертв!</b>")

    # Победа поджигателя
    # Нейтралы больше не завершают игру сразу

    winner = check_win(game)
    if winner:
        announce_win(game, winner)
        return

    time.sleep(1)
    start_day(game)


# ══════════════════════════════════════════════════════════
#                          ДЕНЬ
# ══════════════════════════════════════════════════════════
def start_day(game):
    game.phase = "day"
    game.day_votes = {}
    game.sgt_vote = {}
    game.sgt_target = None

    alive = game.alive_players()
    lst = "\n".join(f"• {p['name']}" for p in alive.values())
    send(game.chat_id,
        f"☀️ <b>День {game.day_num}</b>\n\nЖивые ({len(alive)}):\n{lst}\n\n"
        "💬 Обсуждайте! Через <b>45 сек</b> голосование.\n"
        "/vote — начать досрочно"
    )
    t = threading.Timer(45.0, lambda: start_vote(game))
    game.timer = t
    t.start()

@bot.message_handler(commands=["vote"])
def cmd_vote(msg):
    cid = msg.chat.id
    if cid not in games: return
    g = games[cid]
    if g.phase != "day":
        send(cid, "❌ Голосование только днём!"); return
    if msg.from_user.id not in g.players: return
    if g.timer: g.timer.cancel()
    start_vote(g)


def start_vote(game):
    if game.phase not in ("day", "vote"): return
    game.phase = "vote"
    game.day_votes = {}
    alive = game.alive_players()
    kb = types.InlineKeyboardMarkup()
    for uid, p in alive.items():
        kb.add(types.InlineKeyboardButton(p["name"], callback_data=f"vote_{game.chat_id}_{uid}"))
    kb.add(types.InlineKeyboardButton("🚫 Воздержаться", callback_data=f"vote_{game.chat_id}_skip"))
    send(game.chat_id, "🗳 <b>ГОЛОСОВАНИЕ!</b> Кого исключить?\n⏳ 25 секунд", reply_markup=kb)
    t = threading.Timer(25.0, lambda: resolve_vote(game))
    game.timer = t
    t.start()

@bot.callback_query_handler(func=lambda c: c.data.startswith("vote_"))
def cb_vote(call):
    parts = call.data.split("_")
    cid, target = int(parts[1]), parts[2]
    if cid not in games: return
    g = games[cid]
    if g.phase != "vote":
        bot.answer_callback_query(call.id, "Голосование завершено!"); return
    uid = call.from_user.id
    if uid not in g.alive_players():
        bot.answer_callback_query(call.id, "Мёртвые не голосуют!"); return
    g.day_votes[uid] = target
    name = "воздержался" if target == "skip" else g.players[int(target)]["name"]
    bot.answer_callback_query(call.id, f"✅ Голос: {name}")

def resolve_vote(game):
    if game.phase != "vote": return
    counts = defaultdict(int)
    for v in game.day_votes.values():
        counts[v] += 1
    if not counts:
        send(game.chat_id, "🗳 Никто не проголосовал — пропускаем...")
        time.sleep(1); start_night(game); return
    max_v = max(counts.values())
    tops  = [t for t, c in counts.items() if c == max_v]
    if len(tops) > 1 or "skip" in tops:
        send(game.chat_id, "🗳 Ничья — никто не исключён.")
    else:
        target = int(tops[0])
        role = game.players[target]["role"]
        game.players[target]["alive"] = False
        send(game.chat_id,
            f"⚖️ Исключён: {pname(game, target)}\nРоль: {ROLES[role]['emoji']} <b>{role}</b>")
        winner = check_win(game)
        if winner:
            announce_win(game, winner); return
    time.sleep(1)
    start_night(game)

if __name__ == "__main__":
    print("=" * 45)
    print("   🎭 Дуго МАФИЯ — запущена!")
    print("=" * 45)

    # Убираем активный webhook перед запуском polling
    try:
        bot.remove_webhook()
        time.sleep(1)
        print("✅ Webhook удалён")
    except Exception as e:
        print(f"Webhook cleanup warning: {e}")

    bot.infinity_polling(
        timeout=30,
        long_polling_timeout=20,
        skip_pending=True
    )
