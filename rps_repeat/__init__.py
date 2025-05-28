from otree.api import *
import random

author = 'Aamir Sohail'

doc = """
Multi-round Rock Paper Scissors game where players compete in pairs over multiple rounds.

Dyads are customizable for the following scenarios:

- Human vs Human
- Human vs Bot (LLM)
- Bot vs Bot (LLM)

Bots can be configured to use different LLMs (player_models.csv) and prompting strategies (prompts.py).

Prompting strategies are taken from Vidler and Walsh (2025) https://arxiv.org/pdf/2503.02582
"""

class C(BaseConstants):
    NAME_IN_URL = 'rps_repeat'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 3
    
    # Game choices
    CHOICES = [
        ('R', 'Rock'),
        ('P', 'Paper'), 
        ('S', 'Scissors')
    ]
    
    # Payoffs
    WIN_PAYOFF = 3
    LOSE_PAYOFF = 0
    TIE_PAYOFF = 1


class Subsession(BaseSubsession):
    def creating_session(self):
        # Use matrix grouping
        if self.round_number == 1:
            # Group players into pairs
            matrix = []
            players = self.get_players()
            for i in range(0, len(players), 2):
                if i + 1 < len(players):
                    matrix.append([players[i], players[i + 1]])
            self.set_group_matrix(matrix)
        else:
            # Keep same groups across rounds
            self.group_like_round(1)


class Group(BaseGroup):
    def set_payoffs(self):
        """Calculate payoffs for both players in the group"""
        players = self.get_players()
        p1, p2 = players[0], players[1]
        
        p1_choice = p1.choice
        p2_choice = p2.choice
        
        if p1_choice == p2_choice:
            # Tie
            p1.round_payoff = C.TIE_PAYOFF
            p2.round_payoff = C.TIE_PAYOFF
            p1.result = 'tie'
            p2.result = 'tie'
        elif (
            (p1_choice == 'R' and p2_choice == 'S') or
            (p1_choice == 'P' and p2_choice == 'R') or
            (p1_choice == 'S' and p2_choice == 'P')
        ):
            # Player 1 wins
            p1.round_payoff = C.WIN_PAYOFF
            p2.round_payoff = C.LOSE_PAYOFF
            p1.result = 'win'
            p2.result = 'lose'
        else:
            # Player 2 wins
            p1.round_payoff = C.LOSE_PAYOFF
            p2.round_payoff = C.WIN_PAYOFF
            p1.result = 'lose'
            p2.result = 'win'


class Player(BasePlayer):
    # Player's choice for this round
    choice = models.StringField(
        choices=C.CHOICES,
        widget=widgets.RadioSelect,
        label="Choose your move:"
    )
    
    # Round result and payoff
    result = models.StringField()  # 'win', 'lose', 'tie'
    round_payoff = models.IntegerField(initial=0)

    # Model assignment
    model = models.StringField()  # Store the assigned model name
    
    # Simplified version of your method
    def set_model_assignment(self):
        """Set the model assignment based on player position"""
        intended_model_key = f'player_{self.id_in_group}_intended_model'
        if intended_model_key in self.session.config:
            self.model = self.session.config[intended_model_key]
        else:
            self.model = "human"  # Default for human participants
        
        print(f"Player {self.id_in_group}: assigned model = {self.model}")
    
    def choice_display_text(self, choice_letter):
        """Convert choice letter to full name - renamed to avoid conflict with oTree's get_choice_display()"""
        choice_map = {'R': 'Rock', 'P': 'Paper', 'S': 'Scissors'}
        return choice_map.get(choice_letter, choice_letter)
    
    def get_opponent(self):
        """Get the other player in the group"""
        return self.get_others_in_group()[0]
    
    def get_total_payoff(self):
        """Calculate total payoff across all rounds"""
        return sum([p.round_payoff for p in self.in_all_rounds()])
    
    def get_round_history(self):
        """Get history of choices and results for previous rounds with full choice names"""
        history = []
        for round_player in self.in_previous_rounds():
            opponent = round_player.get_opponent()
            history.append({
                'round': round_player.round_number,
                'my_choice': self.choice_display_text(round_player.choice),
                'opponent_choice': self.choice_display_text(opponent.choice),
                'my_result': round_player.result,
                'my_payoff': round_player.round_payoff
            })
        return history

# PAGES
class GroupingWaitPage(WaitPage):
    """Wait page to form groups of 2 players"""
    group_by_arrival_time = False  # Changed to False for bot compatibility
    title_text = "Forming Groups"
    body_text = "Waiting for other players to join..."

    @staticmethod
    def after_all_players_arrive(group):
        # Set model assignments for all players in the group
        for player in group.get_players():
            player.set_model_assignment()
    
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

class Choice(Page):
    """Page where player makes their Rock Paper Scissors choice"""
    form_model = 'player'
    form_fields = ['choice']
    
    @staticmethod
    def vars_for_template(player):
        history = player.get_round_history()
        return {
            'num_rounds': C.NUM_ROUNDS,
            'win_payoff': C.WIN_PAYOFF,
            'lose_payoff': C.LOSE_PAYOFF,
            'tie_payoff': C.TIE_PAYOFF,
            'round_number': player.round_number,
            'total_rounds': C.NUM_ROUNDS,
            'history': history,
            'has_history': len(history) > 0
        }
    
    def is_experiment_complete(self):
        """Check if this player has completed all rounds"""
        return (self.round_number == C.NUM_ROUNDS and 
                hasattr(self, 'choice') and 
                self.choice is not None)


class WaitForPartner(WaitPage):
    """Wait for both players to make their choices"""
    title_text = "Waiting for opponent"
    body_text = "Waiting for other player to make their choice..."
    
    @staticmethod
    def after_all_players_arrive(group):
        group.set_payoffs()


class Results(Page):
    """Results page showing both choices and outcome"""
    
    @staticmethod
    def vars_for_template(player):
        opponent = player.get_opponent()
        is_final = (player.round_number == C.NUM_ROUNDS)
        
        return {
            'my_choice': player.get_choice_display(),
            'opponent_choice': opponent.get_choice_display(),
            'my_result': player.result,
            'my_payoff': player.round_payoff,
            'round_number': player.round_number,
            'next_round_number': player.round_number + 1,
            'total_rounds': C.NUM_ROUNDS,
            'total_payoff': player.get_total_payoff(),
            'is_final_round': is_final,
            'is_not_final_round': not is_final,
            'result_text': {
                'win': 'You Win!',
                'lose': 'You Lose!',
                'tie': "It's a Tie!"
            }[player.result],
            'result_class': {
                'win': 'success',
                'lose': 'danger', 
                'tie': 'warning'
            }[player.result],
            'status_message': "Game Complete! See final results." if is_final else f"Next: Round {player.round_number + 1}"
        }


class FinalResults(Page):
    """Final results page - shown only in the last round"""
    
    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS
    
    @staticmethod
    def app_after_this_page(player, upcoming_apps):
        # Ensure experiment properly terminates
        participant = player.participant
        participant.finished = True
    
    @staticmethod
    def vars_for_template(player):
        opponent = player.get_opponent()
        
        # Get complete history
        my_history = []
        for round_player in player.in_all_rounds():
            round_opponent = round_player.get_opponent()
            my_history.append({
                'round': round_player.round_number,
                'my_choice': round_player.get_choice_display(),
                'opponent_choice': round_opponent.get_choice_display(),
                'result': round_player.result,
                'payoff': round_player.round_payoff
            })
        
        # Calculate final scores
        my_total = player.get_total_payoff()
        opponent_total = opponent.get_total_payoff()
        
        if my_total > opponent_total:
            overall_result = 'win'
        elif my_total < opponent_total:
            overall_result = 'lose'
        else:
            overall_result = 'tie'
        
        return {
            'my_total_payoff': my_total,
            'opponent_total_payoff': opponent_total,
            'overall_result': overall_result,
            'history': my_history,
            'overall_result_text': {
                'win': 'You Won Overall!',
                'lose': 'You Lost Overall!',
                'tie': 'Overall Tie!'
            }[overall_result],
            'overall_result_class': {
                'win': 'success',
                'lose': 'danger',
                'tie': 'warning'
            }[overall_result]
        }


page_sequence = [GroupingWaitPage, Choice, WaitForPartner, Results, FinalResults]