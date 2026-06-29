import os
import random
import logging
from typing import Dict, List

try:
    import telebot
    from telebot.types import Message
except Exception as e:
    raise RuntimeError(
        "pyTelegramBotAPI (telebot) is required. Install with 'pip install pyTelegramBotAPI'"
    ) from e

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    logger.warning("No TOKEN environment variable found — bot will not connect until TOKEN is set.")
    TOKEN = ""  # empty token will raise when trying to start polling

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

games: Dict[int, "GameState"] = {}

# Minimal role definitions and distributions. Expand as needed.
ROLES = {
    "mafia": {"team": "mafia", "desc": "Mafia: kills at night"},
    "don": {"team": "mafia", "desc": "Don: leader of mafia"},
    "sheriff": {"team": "town", "desc": "Sheriff: checks at night"},
    "doctor": {"team": "town", "desc": "Doctor: can heal at night"},
    "villager": {"team": "town", "desc": "Villager: a normal townsperson"},
}

# Simple role distributions by player count (fallback to a default mix)
ROLE_DIST = {
    3: ["mafia", "sheriff", "villager"],
    4: ["mafia", "doctor", "sheriff", "villager"],
    5: ["mafia", "don", "doctor", "sheriff", "villager"],
}


def choose_roles_for(n: int) -> List[str]:
    if n in ROLE_DIST:
        return ROLE_DIST[n][:]
    # Fallback: 1 mafia, rest villagers, add a sheriff if >=4
    roles = ["mafia"]
    if n >= 4:
        roles.append("sheriff")
    if n >= 5:
        roles.append("doctor")
    while len(roles) < n:
        roles.append("villager")
    return roles


class GameState:
    def __init__(self, chat_id: int, creator_id: int):
        self.chat_id = chat_id
        self.creator_id = creator_id
        # players: dict of user_id -> {name, role, alive}
        self.players: Dict[int, Dict] = {}
        self.started = False
        self.day_phase = False
        self.votes: Dict[int, int] = {}  # voter_id -> target_id

    def add_player(self, user_id: int, name: str):
        if user_id in self.players:
            return False
        self.players[user_id] = {"name": name, "role": None, "alive": True}
        return True

    def alive_players(self) -> Dict[int, Dict]:
        return {uid: p for uid, p in self.players.items() if p.get("alive", False)}

    def team_count(self, team: str) -> int:
        return sum(1 for p in self.alive_players().values() if ROLES.get(p.get("role"), {}).get("team") == team)

    def get_role(self, role_name: str):
        for uid, p in self.players.items():
            if p.get("role") == role_name:
                return uid
        return None

    def mafia_ids(self) -> List[int]:
        return [uid for uid, p in self.alive_players().items() if ROLES.get(p.get("role"), {}).get("team") == "mafia"]

    def dead_players(self) -> List[int]:
        return [uid for uid, p in self.players.items() if not p.get("alive", True)]

    def assign_roles(self):
        n = len(self.players)
        roles = choose_roles_for(n)
        random.shuffle(roles)
        ids = list(self.players.keys())
        random.shuffle(ids)
        for uid, role in zip(ids, roles):
            self.players[uid]["role"] = role

    def is_over(self) -> bool:
        # Simple win condition: if no mafia remain -> town wins; if mafia >= town -> mafia wins
        mafia_alive = self.team_count("mafia")
        town_alive = self.team_count("town")
        if mafia_alive == 0:
            return True
        if mafia_alive >= town_alive:
            return True
        return False


# helper send functions

def send(chat_id: int, text: str, **kwargs):
    try:
        bot.send_message(chat_id, text, **kwargs)
    except Exception as e:
        logger.exception("Failed to send message to %s: %s", chat_id, e)


def pm(uid: int, text: str):
    try:
        bot.send_message(uid, text)
    except Exception:
        logger.exception("Failed to PM %s", uid)


def bold(text: str) -> str:
    return f"<b>{text}</b>"


# Commands

@bot.message_handler(commands=["start", "help"])  # type: ignore
def cmd_start(message: Message):
    text = (
        "Mafia bot ready. Commands:\n"
        "/newgame - create a new game in this chat\n"
        "/join - join the waiting game\n"
        "/startgame - assign roles and start the game (creator only)\n"
        "/endgame - end the current game (creator only)\n"
        "/roles - show role list\n"
        "/status - show current game status\n"
        "/vote <user_id> - vote to lynch a player during day\n"
    )
    send(message.chat.id, text)


@bot.message_handler(commands=["newgame"])  # type: ignore
def cmd_newgame(message: Message):
    chat_id = message.chat.id
    if chat_id in games and not games[chat_id].is_over() and games[chat_id].started:
        send(chat_id, "A game is already in progress in this chat. Use /endgame to stop it.")
        return
    game = GameState(chat_id, message.from_user.id)
    games[chat_id] = game
    game.add_player(message.from_user.id, message.from_user.first_name or "Player")
    send(chat_id, f"New game created by {bold(message.from_user.first_name or 'Player')}. Players should /join.")


@bot.message_handler(commands=["join"])  # type: ignore
def cmd_join(message: Message):
    chat_id = message.chat.id
    if chat_id not in games:
        send(chat_id, "No active waiting game in this chat. Use /newgame to create one.")
        return
    game = games[chat_id]
    added = game.add_player(message.from_user.id, message.from_user.first_name or "Player")
    if added:
        send(chat_id, f"{bold(message.from_user.first_name or 'Player')} joined the game. Total players: {len(game.players)}")
    else:
        send(chat_id, "You are already in the game.")


@bot.message_handler(commands=["roles"])  # type: ignore
def cmd_roles(message: Message):
    lines = [f"{name}: {info.get('desc', '')}" for name, info in ROLES.items()]
    send(message.chat.id, "\n".join(lines))


@bot.message_handler(commands=["startgame"])  # type: ignore
def cmd_startgame(message: Message):
    chat_id = message.chat.id
    if chat_id not in games:
        send(chat_id, "No game to start; create one with /newgame")
        return
    game = games[chat_id]
    if message.from_user.id != game.creator_id:
        send(chat_id, "Only the game creator can start the game.")
        return
    if game.started:
        send(chat_id, "Game already started.")
        return
    if len(game.players) < 3:
        send(chat_id, "Need at least 3 players to start.")
        return
    game.assign_roles()
    game.started = True
    game.day_phase = False
    # PM each player their role
    for uid, p in game.players.items():
        role = p.get("role")
        pm(uid, f"Your role: {bold(role)} - {ROLES.get(role, {}).get('desc', '')}")
    send(chat_id, "Game started! Night falls...")
    start_night(game)


@bot.message_handler(commands=["endgame"])  # type: ignore
def cmd_endgame(message: Message):
    chat_id = message.chat.id
    if chat_id not in games:
        send(chat_id, "No active game in this chat.")
        return
    game = games[chat_id]
    if message.from_user.id != game.creator_id:
        send(chat_id, "Only the game creator can end the game.")
        return
    del games[chat_id]
    send(chat_id, "Game ended by creator.")


@bot.message_handler(commands=["status"])  # type: ignore
def cmd_status(message: Message):
    chat_id = message.chat.id
    if chat_id not in games:
        send(chat_id, "No active game in this chat.")
        return
    game = games[chat_id]
    lines = [f"Game started: {game.started}", f"Players ({len(game.players)}):"]
    for uid, p in game.players.items():
        alive = "alive" if p.get("alive", False) else "dead"
        role = p.get("role") or "(unassigned)"
        lines.append(f"- {p.get('name')} (id={uid}) - {alive} - role: {role}")
    send(chat_id, "\n".join(lines))


def start_night(game: GameState):
    # This simplified night just announces mafia members to themselves and then resolves nothing
    mafia = game.mafia_ids()
    if mafia:
        names = ", ".join(game.players[uid]["name"] for uid in mafia)
        for uid in mafia:
            pm(uid, f"Mafia team members: {names}")
    # Immediately resolve night in this simplified implementation
    resolve_night(game)


def resolve_night(game: GameState):
    # Placeholder simplified: no night kills; go to day
    send(game.chat_id, "Dawn. No one was killed during the night (simplified rules).")
    start_day(game)


def start_day(game: GameState):
    game.day_phase = True
    game.votes = {}
    send(game.chat_id, "Day has started. Discuss and /vote <user_id> to lynch.")


@bot.message_handler(commands=["vote"])  # type: ignore
def cmd_vote(message: Message):
    chat_id = message.chat.id
    if chat_id not in games:
        send(chat_id, "No active game here.")
        return
    game = games[chat_id]
    if not game.started or not game.day_phase:
        send(chat_id, "You can only vote during the day phase of a started game.")
        return
    parts = message.text.strip().split()
    if len(parts) < 2:
        send(chat_id, "Usage: /vote <user_id>")
        return
    try:
        target_id = int(parts[1])
    except ValueError:
        send(chat_id, "Provide a numeric user id from /status list (e.g. /vote 12345678)")
        return
    if target_id not in game.players:
        send(chat_id, "That user id is not in the game.")
        return
    if not game.players[target_id].get("alive", True):
        send(chat_id, "You cannot vote for a dead player.")
        return
    voter_id = message.from_user.id
    if voter_id not in game.players or not game.players[voter_id].get("alive", True):
        send(chat_id, "Only alive players in the game can vote.")
        return
    game.votes[voter_id] = target_id
    send(chat_id, f"{bold(game.players[voter_id]['name'])} voted for {bold(game.players[target_id]['name'])}.")
    # quick resolve check: if all alive players have voted, resolve
    if len(game.votes) >= len(game.alive_players()):
        resolve_vote(game)


def resolve_vote(game: GameState):
    # Count votes
    tally: Dict[int, int] = {}
    for voter, target in game.votes.items():
        tally[target] = tally.get(target, 0) + 1
    if not tally:
        send(game.chat_id, "No votes were cast.")
        return
    # find max
    max_votes = max(tally.values())
    candidates = [uid for uid, v in tally.items() if v == max_votes]
    if len(candidates) > 1:
        send(game.chat_id, "Tie in voting; no one is lynched.")
        game.votes = {}
        return
    lynched = candidates[0]
    game.players[lynched]["alive"] = False
    send(game.chat_id, f"{bold(game.players[lynched]['name'])} was lynched (id={lynched}).")
    if game.is_over():
        # determine winner
        winner = "town"
        if game.team_count("mafia") >= game.team_count("town"):
            winner = "mafia"
        send(game.chat_id, f"Game over. {winner.capitalize()} win!")
        del games[game.chat_id]
        return
    # otherwise start next night
    game.day_phase = False
    start_night(game)


# Graceful polling start
if __name__ == "__main__":
    if not TOKEN:
        print("TOKEN not set. Set the TOKEN environment variable and restart the bot.")
    else:
        print("Starting bot polling...")
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception:
            logger.exception("Bot polling stopped unexpectedly.")
