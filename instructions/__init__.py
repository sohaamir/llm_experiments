from otree.api import *

author = 'Aamir Sohail'

doc = """
Instructions and comprehension checks for the Social Influence Task experiment.
"""

class C(BaseConstants):
    NAME_IN_URL = 'instructions'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # Comprehension check fields
    comprehension_q1 = models.StringField(
        choices=[
            ['40 points', '40 points'],
            ['minus 40 points', 'minus 40 points'],
            ['60 points', '60 points'],
            ['minus 60 points', 'minus 60 points']
        ],
        widget=widgets.RadioSelect
    )
    
    comprehension_q2 = models.StringField(
        choices=[
            ['Option 1', 'Option 1'],
            ['Option 2', 'Option 2'],
            ['Option 3', 'Option 3'],
            ['Option 4', 'Option 4']
        ],
        widget=widgets.RadioSelect
    )
    
    comprehension_q3 = models.StringField(
        choices=[
            ['From your initial choice and bet only', 'From your initial choice and bet only'],
            ['From your second bet and choice only', 'From your second bet and choice only'],
            ['From either the first and second choices/bets but randomly on each trial', 'From either the first and second choices/bets but randomly on each trial'],
            ['From both the first and second choices/bets on each trial', 'From both the first and second choices/bets on each trial']
        ],
        widget=widgets.RadioSelect
    )
    
    comprehension_q4 = models.StringField(
        choices=[
            ['Randomly determined', 'Randomly determined'],
            ['One option will give you a reward everytime, and the other will give you a loss everytime', 'One option will give you a reward everytime, and the other will give you a loss everytime'],
            ['One option will give you a reward randomly, and the other will give you a loss randomly', 'One option will give you a reward randomly, and the other will give you a loss randomly'],
            ['One option will give you a reward most of the time, and the other will give you a loss most of the time', 'One option will give you a reward most of the time, and the other will give you a loss most of the time']
        ],
        widget=widgets.RadioSelect
    )
    
    # Track if answers are correct
    q1_correct = models.BooleanField(initial=False)
    q2_correct = models.BooleanField(initial=False)
    q3_correct = models.BooleanField(initial=False)
    q4_correct = models.BooleanField(initial=False)
    all_correct = models.BooleanField(initial=False)


class Welcome(Page):
    """Initial page with study information and consent"""
    pass


class TaskStructure(Page):
    """Reward structure page"""
    pass


class RoundStructure(Page):
    """Task RoundStructure page"""
    pass


class Comprehension(Page):
    form_model = 'player'
    form_fields = ['comprehension_q1', 'comprehension_q2', 'comprehension_q3', 'comprehension_q4']
    
    @staticmethod
    def before_next_page(player, timeout_happened):
        # Check each answer and store correctness
        player.q1_correct = player.comprehension_q1 == 'minus 60 points'
        player.q2_correct = player.comprehension_q2 == 'Option 3'
        player.q3_correct = player.comprehension_q3 == 'From either the first and second choices/bets but randomly on each trial'
        player.q4_correct = player.comprehension_q4 == 'One option will give you a reward most of the time, and the other will give you a loss most of the time'
        player.all_correct = player.q1_correct and player.q2_correct and player.q3_correct and player.q4_correct


class ComprehensionResults(Page):
    @staticmethod
    def vars_for_template(player):
        return {
            'q1_correct': player.q1_correct,
            'q2_correct': player.q2_correct,
            'q3_correct': player.q3_correct,
            'q4_correct': player.q4_correct,
            'q1_answer': player.comprehension_q1,
            'q2_answer': player.comprehension_q2,
            'q3_answer': player.comprehension_q3,
            'q4_answer': player.comprehension_q4,
            'all_correct': player.all_correct
        }


class Transition(Page):
    """Transition page to the main task"""
    
    @staticmethod
    def before_next_page(player, timeout_happened):
        # Mark this participant as ready to start the task
        player.participant.vars['instructions_completed'] = True


page_sequence = [Welcome, TaskStructure, RoundStructure, Comprehension, ComprehensionResults, Transition]