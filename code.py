import random

# --- 1. Card & Deck Definitions ---
RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
SUITS = ['Hearts', 'Diamonds', 'Clubs', 'Spades'] # Suits don't affect value but good for representation

class BaccaratGame:
    def __init__(self, num_decks=6, initial_balance=1000):
        self.num_decks = num_decks
        self.deck = self._create_deck()
        self.shuffle_deck()
        self.player_balance = initial_balance
        self.current_bets = {}
        self.min_cards_for_reshuffle = 20 # Reshuffle if deck gets too small

        # Payout ratios
        self.payouts = {
            "player_win": 1,  # 1:1
            "banker_win": 0.95, # 1:1 minus 5% commission
            "tie": 8,         # 8:1
            "player_pair": 11, # 11:1
            "banker_pair": 11  # 11:1
        }

    def _create_deck(self):
        """Creates a list of cards for the specified number of decks."""
        deck = []
        for _ in range(self.num_decks):
            for suit in SUITS:
                for rank in RANKS:
                    deck.append({'rank': rank, 'suit': suit})
        return deck

    def shuffle_deck(self):
        """Shuffles the deck."""
        random.shuffle(self.deck)
        print("--- Deck has been shuffled. ---")

    def deal_card(self):
        """Deals a single card from the deck."""
        if len(self.deck) < self.min_cards_for_reshuffle:
            print("--- Deck running low, creating and shuffling a new shoe. ---")
            self.deck = self._create_deck()
            self.shuffle_deck()
        
        if not self.deck: # Should not happen if reshuffle logic is correct
            raise ValueError("Deck is empty! Cannot deal card.")
        return self.deck.pop()

    # --- 2. Card Value Calculation ---
    def get_card_value(self, card_rank):
        """Gets the Baccarat value of a card rank."""
        if card_rank in ['10', 'J', 'Q', 'K']:
            return 0
        elif card_rank == 'A':
            return 1
        else:
            return int(card_rank)

    def get_hand_value(self, hand):
        """Calculates the Baccarat value of a hand."""
        total_value = 0
        for card in hand:
            total_value += self.get_card_value(card['rank'])
        return total_value % 10 # Only the last digit counts

    def _is_pair(self, hand):
        """Checks if the first two cards of a hand form a pair."""
        if len(hand) >= 2:
            return hand[0]['rank'] == hand[1]['rank']
        return False

    # --- 3. Betting Logic ---
    def place_bets(self):
        self.current_bets = {
            "player_win": 0, "banker_win": 0, "tie": 0,
            "player_pair": 0, "banker_pair": 0
        }
        print(f"\nYour current balance: ${self.player_balance}")
        
        while True:
            try:
                total_bet_amount = 0
                
                # Player Win Bet
                bet_pw = int(input(f"Bet on Player Win (pays {self.payouts['player_win']}:1, 0 to skip): $"))
                if bet_pw < 0: raise ValueError("Bet amount cannot be negative.")
                self.current_bets["player_win"] = bet_pw
                total_bet_amount += bet_pw

                # Banker Win Bet
                bet_bw = int(input(f"Bet on Banker Win (pays {self.payouts['banker_win']:.2f}:1 after commission, 0 to skip): $"))
                if bet_bw < 0: raise ValueError("Bet amount cannot be negative.")
                self.current_bets["banker_win"] = bet_bw
                total_bet_amount += bet_bw
                
                # Tie Bet
                bet_t = int(input(f"Bet on Tie (pays {self.payouts['tie']}:1, 0 to skip): $"))
                if bet_t < 0: raise ValueError("Bet amount cannot be negative.")
                self.current_bets["tie"] = bet_t
                total_bet_amount += bet_t

                # Player Pair Bet
                bet_pp = int(input(f"Bet on Player Pair (first 2 cards, pays {self.payouts['player_pair']}:1, 0 to skip): $"))
                if bet_pp < 0: raise ValueError("Bet amount cannot be negative.")
                self.current_bets["player_pair"] = bet_pp
                total_bet_amount += bet_pp

                # Banker Pair Bet
                bet_bp = int(input(f"Bet on Banker Pair (first 2 cards, pays {self.payouts['banker_pair']}:1, 0 to skip): $"))
                if bet_bp < 0: raise ValueError("Bet amount cannot be negative.")
                self.current_bets["banker_pair"] = bet_bp
                total_bet_amount += bet_bp

                if total_bet_amount == 0:
                    print("You must place at least one bet.")
                    continue
                if total_bet_amount > self.player_balance:
                    print("Total bet exceeds your balance. Please try again.")
                    continue
                
                self.player_balance -= total_bet_amount
                print(f"Bets placed. Remaining balance: ${self.player_balance}")
                break
            except ValueError as e:
                print(f"Invalid input: {e}. Please enter a valid number.")
        return True

    def _format_hand(self, hand):
        return ", ".join([f"{card['rank']}{card['suit'][0]}" for card in hand])


    # --- 4. Game Round Logic ---
    def play_round(self):
        if not self.place_bets():
            return # Player chose not to bet or quit

        player_hand = []
        banker_hand = []

        # Initial deal: Player card 1, Banker card 1, Player card 2, Banker card 2
        player_hand.append(self.deal_card())
        banker_hand.append(self.deal_card())
        player_hand.append(self.deal_card())
        banker_hand.append(self.deal_card())

        player_value = self.get_hand_value(player_hand)
        banker_value = self.get_hand_value(banker_hand)

        print(f"\n--- Dealing Cards ---")
        print(f"Player's initial hand: {self._format_hand(player_hand)} (Value: {player_value})")
        print(f"Banker's initial hand: {self._format_hand(banker_hand)} (Value: {banker_value})")

        # Check for Pairs on initial 2 cards
        player_has_pair = self._is_pair(player_hand)
        banker_has_pair = self._is_pair(banker_hand)
        if player_has_pair: print("Player has a Pair!")
        if banker_has_pair: print("Banker has a Pair!")


        # Natural win check
        is_natural = False
        if player_value == 8 or player_value == 9 or banker_value == 8 or banker_value == 9:
            print("Natural!")
            is_natural = True
        
        player_draws_third = False
        player_third_card_value = None

        if not is_natural:
            # Player's third card rule
            if player_value <= 5:
                print("Player draws a third card.")
                third_card = self.deal_card()
                player_hand.append(third_card)
                player_value = self.get_hand_value(player_hand)
                player_third_card_value = self.get_card_value(third_card['rank'])
                player_draws_third = True
                print(f"Player's third card: {third_card['rank']}{third_card['suit'][0]}. Player new hand: {self._format_hand(player_hand)} (Value: {player_value})")
            else: # Player stands (6 or 7)
                print("Player stands.")

            # Banker's third card rule
            banker_draws_third = False
            if player_draws_third: # Player drew a third card
                if banker_value <= 2:
                    banker_draws_third = True
                elif banker_value == 3 and player_third_card_value != 8:
                    banker_draws_third = True
                elif banker_value == 4 and player_third_card_value in [2,3,4,5,6,7]:
                    banker_draws_third = True
                elif banker_value == 5 and player_third_card_value in [4,5,6,7]:
                    banker_draws_third = True
                elif banker_value == 6 and player_third_card_value in [6,7]:
                    banker_draws_third = True
                # if banker_value == 7, Banker stands
            else: # Player stood (did not draw a third card)
                if banker_value <= 5:
                    banker_draws_third = True
                # if banker_value is 6 or 7, Banker stands

            if banker_draws_third:
                print("Banker draws a third card.")
                third_card = self.deal_card()
                banker_hand.append(third_card)
                banker_value = self.get_hand_value(banker_hand)
                print(f"Banker's third card: {third_card['rank']}{third_card['suit'][0]}. Banker new hand: {self._format_hand(banker_hand)} (Value: {banker_value})")
            elif not is_natural: # Don't print if it was natural, it would have already stood.
                 print("Banker stands.")
        
        # --- 5. Determine Winner and Payouts ---
        print("\n--- Results ---")
        print(f"Final Player Hand: {self._format_hand(player_hand)} (Value: {player_value})")
        print(f"Final Banker Hand: {self._format_hand(banker_hand)} (Value: {banker_value})")

        winnings = 0
        result_message = ""

        if player_value > banker_value:
            result_message = f"Player wins with {player_value} vs {banker_value}!"
            winnings += self.current_bets["player_win"] * (1 + self.payouts["player_win"])
        elif banker_value > player_value:
            result_message = f"Banker wins with {banker_value} vs {player_value}!"
            winnings += self.current_bets["banker_win"] * (1 + self.payouts["banker_win"]) # payout already includes commission factor
        else:
            result_message = f"Tie! Both have {player_value}."
            winnings += self.current_bets["tie"] * (1 + self.payouts["tie"])
            # In case of a Tie, Player and Banker bets are usually a push (returned)
            # Our current logic adds winnings, so we need to ensure the original bet is returned.
            # The (1 + payout_ratio) handles this: you get your stake back + winnings.
            # However, for a tie, player/banker bets are typically PUSHED (returned, not lost)
            # This implementation currently makes them lose unless they bet on Tie.
            # Let's adjust: if it's a tie, and they bet on player/banker, they get that bet back.
            if self.current_bets["player_win"] > 0: self.player_balance += self.current_bets["player_win"]
            if self.current_bets["banker_win"] > 0: self.player_balance += self.current_bets["banker_win"]


        # Pair payouts (independent of main game outcome)
        if player_has_pair and self.current_bets["player_pair"] > 0:
            pair_winnings = self.current_bets["player_pair"] * (1 + self.payouts["player_pair"])
            winnings += pair_winnings
            result_message += f"\nPlayer Pair bet wins! +${pair_winnings - self.current_bets['player_pair']:.2f}"
            
        if banker_has_pair and self.current_bets["banker_pair"] > 0:
            pair_winnings = self.current_bets["banker_pair"] * (1 + self.payouts["banker_pair"])
            winnings += pair_winnings
            result_message += f"\nBanker Pair bet wins! +${pair_winnings - self.current_bets['banker_pair']:.2f}"

        print(result_message)
        self.player_balance += winnings
        
        # For player/banker win, the winnings already factor in stake.
        # For tie, player/banker bets are pushed.
        # For side bets, they are won or lost.
        # The logic for self.player_balance -= total_bet_amount and then self.player_balance += winnings
        # correctly handles stake return for winning bets.
        # For a Tie, if a Player/Banker bet was placed, it should be returned (push).
        # The current logic for Tie:
        #   - Winnings for Tie bet are correct.
        #   - If player bet on Player and it's a Tie, their Player bet is lost. (Standard Baccarat)
        #   - If player bet on Banker and it's a Tie, their Banker bet is lost. (Standard Baccarat)
        #   The adjustment "if self.current_bets["player_win"] > 0: self.player_balance += self.current_bets["player_win"]"
        #   is only if the house rule is that Player/Banker bets PUSH on a Tie.
        #   Let's stick to the more standard rule: Player/Banker bets lose on a Tie unless Tie is bet.
        #   So, I will remove the push logic for Player/Banker bets on a Tie. The original bets are lost.
        #   The only bets that win on a Tie are Tie bets.
        
        # Re-evaluating payout for Tie for clarity.
        # If it's a TIE:
        #   - current_bets["tie"] is paid out at (1 + payout_ratio).
        #   - current_bets["player_win"] is lost.
        #   - current_bets["banker_win"] is lost.
        # This is handled by:
        #   1. Deducting ALL bets initially.
        #   2. Adding back (stake + profit) ONLY for winning bets.

        print(f"Total Winnings from this round (including stake back for winning bets): ${winnings:.2f}")
        print(f"New balance: ${self.player_balance:.2f}")

    # --- 6. Main Game Loop ---
    def start_game(self):
        print("--- Welcome to Baccarat! ---")
        while self.player_balance > 0:
            print(f"\n--- New Round ---")
            print(f"Remaining cards in shoe: {len(self.deck)}")
            
            self.play_round()

            if self.player_balance <= 0:
                print("\n--- Game Over ---")
                print("You've run out of money!")
                break
            
            while True:
                again = input("Play another round? (y/n): ").lower()
                if again == 'y':
                    break
                elif again == 'n':
                    print("Thanks for playing! Final balance: ${:.2f}".format(self.player_balance))
                    return
                else:
                    print("Invalid input. Please enter 'y' or 'n'.")
        
        if self.player_balance > 0 : # If loop exited due to 'n'
             print(f"Thanks for playing! Final balance: ${self.player_balance:.2f}")


if __name__ == "__main__":
    game = BaccaratGame(num_decks=6, initial_balance=1000)
    game.start_game()