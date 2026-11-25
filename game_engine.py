import random
import uuid

COLORS = ["red", "yellow", "green", "blue"]
COLOR_AR = {"red": "أحمر", "yellow": "أصفر", "green": "أخضر", "blue": "أزرق"}
COLOR_HEX = {"red": "#e74c3c", "yellow": "#f1c40f", "green": "#27ae60", "blue": "#2980b9"}

def make_card(color, value):
    return {"id": uuid.uuid4().hex[:12], "color": color, "value": value}

def build_deck():
    deck = []
    for color in COLORS:
        deck.append(make_card(color, "0"))
        for value in [str(n) for n in range(1, 10)] + ["skip", "reverse", "draw2"]:
            deck.append(make_card(color, value))
            deck.append(make_card(color, value))
    for value in ["wild", "wild4"]:
        for _ in range(4):
            deck.append(make_card(None, value))
    random.shuffle(deck)
    return deck

class GameManager:
    def __init__(self):
        self.games = {}

    def create_game(self, user_id, player_name):
        deck = build_deck()
        player_hand = [deck.pop() for _ in range(7)]
        ai_hand = [deck.pop() for _ in range(7)]
        first = deck.pop()
        while first["value"] in ("wild", "wild4", "skip", "reverse", "draw2"):
            deck.append(first)
            random.shuffle(deck)
            first = deck.pop()
        game = {
            "deck": deck, "discard": [first],
            "hands": {"player": player_hand, "ai": ai_hand},
            "turn": "player", "current_color": first["color"],
            "status": "playing", "winner": None, "player_name": player_name,
            "message": "دورك الآن!"
        }
        self.games[user_id] = game
        return self._public_state(game)

    def get_state(self, user_id):
        game = self.games.get(user_id)
        return self._public_state(game) if game else None

    def _draw_one(self, game, who):
        if not game["deck"]:
            top = game["discard"].pop()
            game["deck"] = game["discard"]
            game["discard"] = [top]
            random.shuffle(game["deck"])
        if game["deck"]:
            game["hands"][who].append(game["deck"].pop())

    def _is_playable(self, card, game):
        top = game["discard"][-1]
        return card["color"] is None or card["color"] == game["current_color"] or card["value"] == top["value"]

    def _public_state(self, game):
        if not game:
            return None
        top = game["discard"][-1]
        return {
            "hand": game["hands"]["player"],
            "ai_count": len(game["hands"]["ai"]),
            "top_card": top,
            "current_color": game["current_color"],
            "current_color_ar": COLOR_AR[game["current_color"]],
            "turn": game["turn"], "status": game["status"],
            "winner": game["winner"], "message": game["message"],
            "playable_ids": [c["id"] for c in game["hands"]["player"] if self._is_playable(c, game)]
        }

    def _advance_ai(self, game):
        if game["status"] != "playing":
            return
        game["turn"] = "ai"
        hand = game["hands"]["ai"]
        playable = [c for c in hand if self._is_playable(c, game)]
        if not playable:
            self._draw_one(game, "ai")
            playable = [c for c in hand if self._is_playable(c, game)]
        if playable:
            card = next((c for c in playable if c["value"] in ("wild4", "draw2", "skip")), playable[0])
            self._apply_card(game, "ai", card, random.choice(COLORS) if card["color"] is None else None)
        if game["status"] == "playing":
            game["turn"] = "player"
            game["message"] = "دورك الآن!"

    def _apply_card(self, game, who, card, chosen_color=None):
        hand = game["hands"][who]
        hand.remove(card)
        game["discard"].append(card)
        if card["color"] is None:
            game["current_color"] = chosen_color or random.choice(COLORS)
        else:
            game["current_color"] = card["color"]

        if not hand:
            game["status"] = "finished"
            game["winner"] = who
            game["message"] = "فزت!" if who == "player" else "فاز الكمبيوتر!"
            return

        if card["value"] in ("draw2", "wild4"):
            target = "ai" if who == "player" else "player"
            amount = 2 if card["value"] == "draw2" else 4
            for _ in range(amount):
                self._draw_one(game, target)
        if card["value"] == "skip":
            pass
        game["message"] = "تم لعب الورقة."

    def play_card(self, user_id, card_id, chosen_color=None):
        game = self.games.get(user_id)
        if not game:
            raise ValueError("ابدأ مباراة جديدة أولاً.")
        if game["status"] != "playing" or game["turn"] != "player":
            raise ValueError("ليس دورك الآن.")
        card = next((c for c in game["hands"]["player"] if c["id"] == card_id), None)
        if not card:
            raise ValueError("هذه الورقة غير موجودة في يدك.")
        if not self._is_playable(card, game):
            raise ValueError("لا يمكنك لعب هذه الورقة الآن.")
        if card["value"] in ("wild", "wild4") and chosen_color not in COLORS:
            raise ValueError("اختر لوناً صالحاً.")
        self._apply_card(game, "player", card, chosen_color)
        if game["status"] == "playing":
            self._advance_ai(game)
        return self._public_state(game)

    def draw_card(self, user_id):
        game = self.games.get(user_id)
        if not game:
            raise ValueError("ابدأ مباراة جديدة أولاً.")
        if game["status"] != "playing" or game["turn"] != "player":
            raise ValueError("ليس دورك الآن.")
        self._draw_one(game, "player")
        game["message"] = "سحبت ورقة. يمكنك لعبها إذا كانت مناسبة."
        # In this MVP, drawing ends the player's turn.
        self._advance_ai(game)
        return self._public_state(game)
