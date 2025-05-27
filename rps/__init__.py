from otree.api import *
import random

author = 'Your Name'

doc = """
Rock Paper Scissors one-shot game with multiple prompting strategies for LLM bots.
Players play a single round against a randomly-choosing opponent.
"""

class C(BaseConstants):
    NAME_IN_URL = 'rps'
    PLAYERS_PER_GROUP = None  # Single player game
    NUM_ROUNDS = 1
    
    # Game choices
    CHOICES = [
        ('R', 'Rock'),
        ('P', 'Paper'), 
        ('S', 'Scissors')
    ]
    
    # Prompt strategies
    PROMPT_STRATEGIES = [
        'P1',   # Base prompt
        'P2r',  # Rock first
        'P2p',  # Paper first
        'P2s',  # Scissors first
        'P3a',  # Classic reworded
        'P3b',  # Added random
        'P3c',  # Random + optimal
        'P4'    # Clear points
    ]
    
    # Payoffs
    WIN_PAYOFF = 1
    LOSE_PAYOFF = 0
    TIE_PAYOFF = 0


class Subsession(BaseSubsession):
    def creating_session(self):
        # Assign prompt strategies to players (can be customized)
        for player in self.get_players():
            # Default to P1, but can be overridden by session config
            player.prompt_strategy = self.session.config.get('prompt_strategy', 'P1')


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # Player's choice
    choice = models.StringField(
        choices=C.CHOICES,
        widget=widgets.RadioSelect,
        label="Choose your move:"
    )
    
    # Opponent's choice (randomly generated)
    opponent_choice = models.StringField(choices=C.CHOICES)
    
    # Game result
    result = models.StringField()  # 'win', 'lose', 'tie'
    points_earned = models.IntegerField(initial=0)
    
    # Prompt strategy used
    prompt_strategy = models.StringField(choices=[(s, s) for s in C.PROMPT_STRATEGIES])
    
    def set_opponent_choice(self):
        """Randomly determine opponent's choice"""
        self.opponent_choice = random.choice(['R', 'P', 'S'])
    
    def determine_result(self):
        """Determine game result and points earned"""
        player_choice = self.choice
        opponent_choice = self.opponent_choice
        
        if player_choice == opponent_choice:
            self.result = 'tie'
            self.points_earned = C.TIE_PAYOFF
        elif (
            (player_choice == 'R' and opponent_choice == 'S') or
            (player_choice == 'P' and opponent_choice == 'R') or
            (player_choice == 'S' and opponent_choice == 'P')
        ):
            self.result = 'win'
            self.points_earned = C.WIN_PAYOFF
        else:
            self.result = 'lose'
            self.points_earned = C.LOSE_PAYOFF
    
    def get_choice_display(self, choice_letter):
        """Convert choice letter to full name"""
        choice_map = {'R': 'Rock', 'P': 'Paper', 'S': 'Scissors'}
        return choice_map.get(choice_letter, choice_letter)


# PAGES

class Instructions(Page):
    """Instructions page explaining the Rock Paper Scissors game"""
    
    @staticmethod
    def vars_for_template(player):
        return {
            'win_payoff': C.WIN_PAYOFF,
            'lose_payoff': C.LOSE_PAYOFF,
            'tie_payoff': C.TIE_PAYOFF
        }


class Choice(Page):
    """Page where player makes their Rock Paper Scissors choice"""
    form_model = 'player'
    form_fields = ['choice']
    
    @staticmethod
    def before_next_page(player, timeout_happened):
        # Generate opponent's choice
        player.set_opponent_choice()
        
        # Determine result and points
        player.determine_result()


class Results(Page):
    """Results page showing both choices and outcome"""
    
    @staticmethod
    def vars_for_template(player):
        return {
            'player_choice_display': player.get_choice_display(player.choice),
            'opponent_choice_display': player.get_choice_display(player.opponent_choice),
            'result_text': {
                'win': 'You Win!',
                'lose': 'You Lose!',
                'tie': "It's a Tie!"
            }[player.result],
            'result_class': {
                'win': 'success',
                'lose': 'danger', 
                'tie': 'warning'
            }[player.result]
        }


page_sequence = [Instructions, Choice, Results]