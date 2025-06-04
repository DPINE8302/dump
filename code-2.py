from flask import Flask, render_template_string, request, session, redirect, url_for, flash
import random
import os

app = Flask(__name__)
# Secret key is crucial for session management. Use a strong, random key in production.
app.secret_key = os.urandom(24) 

# --- Baccarat Game Logic (adapted for web) ---
RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
SUITS = ['♥', '♦', '♣', '♠'] # Using Unicode symbols for better web display

class BaccaratGame:
    def __init__(self, num_decks=6):
        self.num_decks = num_decks
        # These attributes will be loaded from and saved to the Flask session
        self.deck = []
        self.player_balance = 1000  # Default starting balance
        self.current_bets = {}
        self.player_hand = []
        self.banker_hand = []
        self.player_value = 0
        self.banker_value = 0
        self.player_third_card_drawn = None 
        self.banker_third_card_drawn = None
        self.result_message = ""
        self.round_history = [] 
        self.min_cards_for_reshuffle = 20 # Reshuffle if deck gets below this

        self.payouts = {
            "player_win": 1,    # Pays 1:1
            "banker_win": 0.95, # Pays 1:1 minus 5% commission (so 0.95 profit on stake)
            "tie": 8,           # Pays 8:1
            "player_pair": 11,  # Pays 11:1
            "banker_pair": 11   # Pays 11:1
        }

    def load_state(self, session_data):
        """Loads game state from a dictionary (e.g., Flask session)."""
        self.deck = session_data.get('deck', self._create_deck()) # Start with fresh deck if none
        if not self.deck or len(self.deck) < self.min_cards_for_reshuffle:
             self.deck = self._create_deck()
             self.shuffle_deck()
             # Only flash if deck was actually present and then reshuffled
             if 'deck' in session_data and len(session_data.get('deck', [])) < self.min_cards_for_reshuffle :
                 flash("Deck was low, new shoe shuffled.", "info")


        self.player_balance = session_data.get('player_balance', 1000)
        self.current_bets = session_data.get('current_bets', {})
        self.player_hand = session_data.get('player_hand', [])
        self.banker_hand = session_data.get('banker_hand', [])
        self.player_value = session_data.get('player_value', 0)
        self.banker_value = session_data.get('banker_value', 0)
        self.player_third_card_drawn = session_data.get('player_third_card_drawn', None)
        self.banker_third_card_drawn = session_data.get('banker_third_card_drawn', None)
        self.result_message = session_data.get('result_message', "Place your bets to start.")
        self.round_history = session_data.get('round_history', [])


    def save_state(self):
        """Returns a dictionary of the current game state for session storage."""
        return {
            'deck': self.deck,
            'player_balance': self.player_balance,
            'current_bets': self.current_bets,
            'player_hand': self.player_hand,
            'banker_hand': self.banker_hand,
            'player_value': self.player_value,
            'banker_value': self.banker_value,
            'player_third_card_drawn': self.player_third_card_drawn,
            'banker_third_card_drawn': self.banker_third_card_drawn,
            'result_message': self.result_message,
            'round_history': self.round_history,
        }

    def _create_deck(self):
        deck = []
        for _ in range(self.num_decks):
            for suit in SUITS:
                for rank in RANKS:
                    deck.append({'rank': rank, 'suit': suit})
        return deck

    def shuffle_deck(self):
        random.shuffle(self.deck)
        # flash("Deck has been shuffled.", "info") # Avoid flashing too often during internal calls

    def deal_card(self):
        if not self.deck or len(self.deck) < self.min_cards_for_reshuffle:
            flash("Deck running low, creating and shuffling a new shoe.", "warning")
            self.deck = self._create_deck()
            self.shuffle_deck()
        
        if not self.deck: # Failsafe, should not be reached if above logic is sound
            self.deck = self._create_deck() 
            self.shuffle_deck()
            flash("CRITICAL: Deck was empty. Created and shuffled a new shoe.", "error")
        return self.deck.pop()

    def get_card_value(self, card_rank):
        if card_rank in ['10', 'J', 'Q', 'K']: return 0
        elif card_rank == 'A': return 1
        else: return int(card_rank)

    def get_hand_value(self, hand):
        return sum(self.get_card_value(card['rank']) for card in hand) % 10

    def _is_pair(self, hand):
        return len(hand) >= 2 and hand[0]['rank'] == hand[1]['rank']

    def _format_card(self, card):
        return f"{card['rank']}{card['suit']}" if card else ""

    def _format_hand_display(self, hand):
        return ", ".join([self._format_card(c) for c in hand]) if hand else "No cards"

    def set_bets(self, bets_from_form):
        self.current_bets = { "player_win": 0, "banker_win": 0, "tie": 0, "player_pair": 0, "banker_pair": 0 }
        total_bet_amount = 0
        try:
            bet_amounts = {
                "player_win": int(bets_from_form.get("bet_player_win", 0)),
                "banker_win": int(bets_from_form.get("bet_banker_win", 0)),
                "tie": int(bets_from_form.get("bet_tie", 0)),
                "player_pair": int(bets_from_form.get("bet_player_pair", 0)),
                "banker_pair": int(bets_from_form.get("bet_banker_pair", 0)),
            }

            for bet_type, amount in bet_amounts.items():
                if amount < 0:
                    flash("Bet amount cannot be negative.", "error")
                    return False
                self.current_bets[bet_type] = amount
                total_bet_amount += amount
            
            if total_bet_amount == 0:
                flash("You must place at least one bet.", "error")
                return False
            if total_bet_amount > self.player_balance:
                flash(f"Total bet (${total_bet_amount}) exceeds your balance (${self.player_balance}).", "error")
                return False
            
            self.player_balance -= total_bet_amount
            flash(f"Bets placed: ${total_bet_amount}. Balance after bets: ${self.player_balance:.2f}", "success")
            return True
        except ValueError:
            flash("Invalid bet amount. Please enter whole numbers only.", "error")
            return False

    def play_round_logic(self):
        self.player_hand, self.banker_hand = [], []
        self.player_third_card_drawn, self.banker_third_card_drawn = None, None
        
        # Initial deal
        for _ in range(2):
            self.player_hand.append(self.deal_card())
            self.banker_hand.append(self.deal_card())

        self.player_value = self.get_hand_value(self.player_hand)
        self.banker_value = self.get_hand_value(self.banker_hand)

        player_has_pair = self._is_pair(self.player_hand)
        banker_has_pair = self._is_pair(self.banker_hand)

        is_natural = (self.player_value >= 8 or self.banker_value >= 8)
        
        player_draws_third, player_third_card_actual_value = False, None

        if not is_natural:
            if self.player_value <= 5: # Player draws
                self.player_third_card_drawn = self.deal_card()
                self.player_hand.append(self.player_third_card_drawn)
                self.player_value = self.get_hand_value(self.player_hand)
                player_third_card_actual_value = self.get_card_value(self.player_third_card_drawn['rank'])
                player_draws_third = True
            
            # Banker's turn
            banker_draws_third = False
            if player_draws_third:
                if self.banker_value <= 2: banker_draws_third = True
                elif self.banker_value == 3 and player_third_card_actual_value != 8: banker_draws_third = True
                elif self.banker_value == 4 and player_third_card_actual_value in [2,3,4,5,6,7]: banker_draws_third = True
                elif self.banker_value == 5 and player_third_card_actual_value in [4,5,6,7]: banker_draws_third = True
                elif self.banker_value == 6 and player_third_card_actual_value in [6,7]: banker_draws_third = True
            else: # Player stood
                if self.banker_value <= 5: banker_draws_third = True
            
            if banker_draws_third:
                self.banker_third_card_drawn = self.deal_card()
                self.banker_hand.append(self.banker_third_card_drawn)
                self.banker_value = self.get_hand_value(self.banker_hand)
        
        # Determine Winner and Payouts
        current_winnings_for_round = 0
        result_summary = []

        main_result_text = ""
        if self.player_value > self.banker_value:
            main_result_text = f"Player wins ({self.player_value} vs {self.banker_value})!"
            if self.current_bets.get("player_win", 0) > 0:
                payout = self.current_bets["player_win"] * (1 + self.payouts["player_win"])
                current_winnings_for_round += payout
                result_summary.append(f"Player Win bet paid ${payout:.2f}.")
        elif self.banker_value > self.player_value:
            main_result_text = f"Banker wins ({self.banker_value} vs {self.player_value})!"
            if self.current_bets.get("banker_win", 0) > 0:
                payout = self.current_bets["banker_win"] * (1 + self.payouts["banker_win"])
                current_winnings_for_round += payout
                result_summary.append(f"Banker Win bet paid ${payout:.2f} (includes 5% commission).")
        else: # Tie
            main_result_text = f"Tie! Both have {self.player_value}."
            if self.current_bets.get("tie", 0) > 0:
                payout = self.current_bets["tie"] * (1 + self.payouts["tie"])
                current_winnings_for_round += payout
                result_summary.append(f"Tie bet paid ${payout:.2f}.")
        
        if player_has_pair and self.current_bets.get("player_pair", 0) > 0:
            payout = self.current_bets["player_pair"] * (1 + self.payouts["player_pair"])
            current_winnings_for_round += payout
            result_summary.append(f"Player Pair bet paid ${payout:.2f}.")
        
        if banker_has_pair and self.current_bets.get("banker_pair", 0) > 0:
            payout = self.current_bets["banker_pair"] * (1 + self.payouts["banker_pair"])
            current_winnings_for_round += payout
            result_summary.append(f"Banker Pair bet paid ${payout:.2f}.")

        self.player_balance += current_winnings_for_round
        self.result_message = main_result_text
        if result_summary:
            self.result_message += " " + " ".join(result_summary)
        else:
            self.result_message += " No winning bets this round."
        
        if current_winnings_for_round > 0:
            flash(f"Total paid out this round: ${current_winnings_for_round:.2f}. New balance: ${self.player_balance:.2f}", "success")
        else:
            flash(f"{self.result_message} New balance: ${self.player_balance:.2f}", "info")


        self.round_history.append({
            "player_hand_str": self._format_hand_display(self.player_hand), "player_val": self.player_value,
            "banker_hand_str": self._format_hand_display(self.banker_hand), "banker_val": self.banker_value,
            "result_text": main_result_text
        })
        if len(self.round_history) > 5: self.round_history.pop(0) # Keep last 5 results

    def reset_for_new_round(self):
        self.player_hand, self.banker_hand = [], []
        self.player_value, self.banker_value = 0, 0
        self.current_bets = {}
        self.result_message = "Place your bets for the next round."
        self.player_third_card_drawn, self.banker_third_card_drawn = None, None
        # Deck is not reset here to maintain shoe continuity

# --- HTML Template ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Baccarat Game</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #0F3D0F; color: #E0E0E0; display: flex; flex-direction: column; align-items: center; min-height: 100vh; }
        .container { background-color: #1A4A1A; padding: 20px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.3); width: 90%; max-width: 800px; margin-top: 20px; }
        h1, h2 { color: #FFD700; text-align: center; text-shadow: 1px 1px 2px #000; }
        .balance { font-size: 1.4em; font-weight: bold; margin-bottom: 20px; text-align: center; color: #FFFFFF; background-color: #2A6A2A; padding: 10px; border-radius: 5px; }
        .game-area, .betting-area-flex { display: flex; justify-content: space-around; margin-bottom: 20px; gap: 20px; }
        .hand { border: 2px solid #FFD700; padding: 15px; border-radius: 8px; width: 45%; background-color: #2A5A2A; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
        .hand h3 { margin-top: 0; color: #FFD700; border-bottom: 1px solid #FFD700; padding-bottom: 5px; }
        .cards { font-size: 1.8em; color: #FFFFFF; background-color: #3A7A3A; padding:15px; border-radius:5px; text-align:center; min-height: 40px; font-weight: bold; letter-spacing: 2px; }
        .bet-form { display: flex; flex-direction: column; gap: 10px; }
        .bet-form div { display: flex; justify-content: space-between; align-items: center; }
        .bet-form label { font-weight: bold; color: #C0C0C0; }
        .bet-form input[type="number"] { width: 80px; padding: 8px; border: 1px solid #FFD700; border-radius: 4px; background-color: #E0E0E0; color: #0F3D0F; text-align: right; }
        .action-buttons { display: flex; justify-content: center; gap: 15px; margin-top: 20px; }
        .action-button {
            background-color: #FFD700; color: #0F3D0F; padding: 12px 20px; border: none;
            border-radius: 5px; cursor: pointer; font-size: 1.1em; font-weight: bold; text-transform: uppercase;
            transition: background-color 0.3s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .action-button:hover { background-color: #E6C300; }
        .action-button.reset { background-color: #B22222; color: #FFFFFF; }
        .action-button.reset:hover { background-color: #8B0000; }
        .messages { margin-top: 20px; width: 100%; }
        .messages div { padding: 12px; border-radius: 5px; margin-bottom: 10px; text-align: center; font-weight: bold; }
        .messages .info { background-color: #3A8A3A; color: #FFFFFF; border-left: 6px solid #2A6A2A; }
        .messages .error { background-color: #B22222; color: #FFFFFF; border-left: 6px solid #800000; }
        .messages .success { background-color: #2E8B57; color: #FFFFFF; border-left: 6px solid #1E7B37; }
        .messages .warning { background-color: #DAA520; color: #0F3D0F; border-left: 6px solid #B8860B; }
        .history { margin-top: 30px; }
        .history table { width: 100%; border-collapse: collapse; background-color: #2A5A2A; border: 1px solid #FFD700; }
        .history th, .history td { border: 1px solid #FFD700; padding: 10px; text-align: left; color: #E0E0E0; }
        .history th { background-color: #3A7A3A; color: #FFD700; }
        .deck-info { text-align: center; margin-bottom: 15px; font-style: italic; color: #B0B0B0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Baccarat</h1>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            <div class="messages">
            {% for category, message in messages %}
              <div class="{{ category }}">{{ message }}</div>
            {% endfor %}
            </div>
          {% endif %}
        {% endwith %}

        <div class="balance">Balance: ${{ "%.2f"|format(game.player_balance) }}</div>
        <div class="deck-info">Cards in Shoe: {{ game.deck|length if game.deck else 'N/A' }}</div>

        {% if session.get('round_phase', 'betting') == 'betting' %}
        <h2>Place Your Bets</h2>
        <div class="betting-area-flex">
            <form method="POST" action="{{ url_for('index') }}" class="bet-form">
                <input type="hidden" name="action" value="place_bet">
                <div><label for="bet_player_win">Player Win (1:1): $</label><input type="number" name="bet_player_win" value="{{ game.current_bets.get('player_win', 0) }}" min="0"></div>
                <div><label for="bet_banker_win">Banker Win (0.95:1): $</label><input type="number" name="bet_banker_win" value="{{ game.current_bets.get('banker_win', 0) }}" min="0"></div>
                <div><label for="bet_tie">Tie (8:1): $</label><input type="number" name="bet_tie" value="{{ game.current_bets.get('tie', 0) }}" min="0"></div>
                <div><label for="bet_player_pair">Player Pair (11:1): $</label><input type="number" name="bet_player_pair" value="{{ game.current_bets.get('player_pair', 0) }}" min="0"></div>
                <div><label for="bet_banker_pair">Banker Pair (11:1): $</label><input type="number" name="bet_banker_pair" value="{{ game.current_bets.get('banker_pair', 0) }}" min="0"></div>
                <div class="action-buttons"><input type="submit" class="action-button" value="Deal Cards"></div>
            </form>
        </div>
        {% else %} <!-- round_phase == 'results' -->
        <h2>Round Results</h2>
        <div class="game-area">
            <div class="hand">
                <h3>Player (Value: {{ game.player_value }})</h3>
                <div class="cards">{{ game._format_hand_display(game.player_hand) }}</div>
                {% if game.player_third_card_drawn %}<p style="text-align:center; font-style:italic;">Third Card: {{ game._format_card(game.player_third_card_drawn) }}</p>{% endif %}
            </div>
            <div class="hand">
                <h3>Banker (Value: {{ game.banker_value }})</h3>
                <div class="cards">{{ game._format_hand_display(game.banker_hand) }}</div>
                 {% if game.banker_third_card_drawn %}<p style="text-align:center; font-style:italic;">Third Card: {{ game._format_card(game.banker_third_card_drawn) }}</p>{% endif %}
            </div>
        </div>
        <div class="action-buttons">
            <form method="POST" action="{{ url_for('index') }}">
                <input type="hidden" name="action" value="next_round">
                <input type="submit" class="action-button" value="Next Round">
            </form>
        </div>
        {% endif %}
        
        <div class="history">
            <h2>Round History</h2>
            {% if game.round_history %}
            <table>
                <tr><th>Player Hand (Value)</th><th>Banker Hand (Value)</th><th>Result</th></tr>
                {% for r in game.round_history|reverse %}
                <tr><td>{{ r.player_hand_str }} ({{r.player_val}})</td><td>{{ r.banker_hand_str }} ({{r.banker_val}})</td><td>{{ r.result_text }}</td></tr>
                {% endfor %}
            </table>
            {% else %}<p style="text-align:center;">No rounds played yet in this session.</p>{% endif %}
        </div>
         <div class="action-buttons" style="margin-top:30px;">
            <form method="POST" action="{{ url_for('reset_game_session') }}">
                <input type="submit" class="action-button reset" value="Reset Game (New Shoe & Balance)">
            </form>
        </div>
    </div>
</body>
</html>
"""

def get_game_from_session():
    """Helper to get or initialize game instance from session."""
    game = BaccaratGame() # Create a new default instance
    if 'game_state' in session:
        game.load_state(session['game_state'])
    else: # First time or after a full reset, ensure deck is ready
        game.deck = game._create_deck()
        game.shuffle_deck()
        flash("Welcome to Baccarat! A new shoe has been shuffled.", "info")
    return game

def save_game_to_session(game):
    """Helper to save game instance to session."""
    session['game_state'] = game.save_state()

@app.route('/', methods=['GET', 'POST'])
def index():
    game = get_game_from_session()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'place_bet':
            if game.set_bets(request.form): # Valid bets placed and balance deducted
                game.play_round_logic() # Deal cards, determine winner, update balance
                session['round_phase'] = 'results'
            else:
                # set_bets already flashed errors, stay in betting phase
                session['round_phase'] = 'betting'
        
        elif action == 'next_round':
            if game.player_balance <= 0:
                flash("Game Over! You've run out of money. Resetting game.", "error")
                session.pop('game_state', None) # Clear state
                session.pop('round_phase', None)
                return redirect(url_for('index')) # Will re-initialize

            game.reset_for_new_round()
            session['round_phase'] = 'betting'
        
        save_game_to_session(game)
        return redirect(url_for('index')) # PRG pattern

    # For GET request or after POST redirect, ensure phase is set
    if 'round_phase' not in session:
        session['round_phase'] = 'betting'
    
    return render_template_string(HTML_TEMPLATE, game=game, session=session)

@app.route('/reset_game', methods=['POST'])
def reset_game_session():
    session.pop('game_state', None)
    session.pop('round_phase', None) 
    flash("Game has been completely reset. New shoe and fresh balance.", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True) # debug=True is helpful for development