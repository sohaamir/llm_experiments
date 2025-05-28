from otree.api import *
import random

author = 'Aamir Sohail'

doc = """
Rock Paper Scissors one-shot game with multiple prompting strategies for LLM bots.
Players play a single round against a randomly-choosing opponent.

Bots can be configured to use different LLMs (player_models.csv) and prompting strategies (prompts.py).

Prompting strategies taken from (Vidler & Walsh, 2025) https://arxiv.org/pdf/2503.02582
"""

class C(BaseConstants):
    NAME_IN_URL = 'rps_oneshot'
    PLAYERS_PER_GROUP = None  # Single player game
    NUM_ROUNDS = 1
    
    # Game choices
    CHOICES = [
        ('R', 'Rock'),
        ('P', 'Paper'), 
        ('S', 'Scissors')
    ]
    
    # Payoffs
    WIN_PAYOFF = 1
    LOSE_PAYOFF = 0
    TIE_PAYOFF = 0


class Subsession(BaseSubsession):
    pass


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
    
    def get_opponent_choice_display(self):
        """Convert opponent choice letter to full name"""
        choice_map = {'R': 'Rock', 'P': 'Paper', 'S': 'Scissors'}
        return choice_map.get(self.opponent_choice, self.opponent_choice)


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
    def vars_for_template(player):
        return {
            'win_payoff': C.WIN_PAYOFF,
            'lose_payoff': C.LOSE_PAYOFF,
            'tie_payoff': C.TIE_PAYOFF
        }
    
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
            'player_choice_display': player.get_choice_display(),
            'opponent_choice_display': player.get_opponent_choice_display(),
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


page_sequence = [Choice, Results]