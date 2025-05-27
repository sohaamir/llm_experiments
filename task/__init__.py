from otree.api import *
import random
import csv
import os
from itertools import cycle

author = 'Aamir Sohail'

doc = """
Multiplayer version of the Social Influence Task (SIT) supporting any combination of human 
participants and LLM bots using the `botex` package. 

Players are grouped in groups of 5 and make decisions in real-time. 

The implementation supports models from multiple LLM providers including:

- OpenAI (gpt-4.1, gpt-4.1-mini, gpt-4.1-nano, gpt-4.5-preview, gpt-4o)
- Anthropic (claude-3.5-sonnet, claude-3-haiku, claude-3-opus, claude-3-sonnet)
- Google (gemini-1.5, gemini-1.5-mini, gemini-1.5-nano)
- Local LLMs (tinyllama)
"""

# Constants for the experiment
class C(BaseConstants):
    NAME_IN_URL = 'social_influence_task'
    PLAYERS_PER_GROUP = 3
    NUM_ROUNDS = 1  # 64 rounds (same as the original task)
    
    # Reversal points
    REVERSAL_ROUNDS = [16, 33, 48]

# Hardcoded reward sequence for each round: [(A_reward, B_reward), ...]
# Same as before - sequence of 64 rounds defining which option is rewarded in each round
REWARD_SEQUENCE = [
    (1, 0),  # Round 1
    (1, 0),  # Round 2
    (1, 0),  # Round 3
    (1, 0),  # Round 4
    (0, 1),  # Round 5
    (1, 0),  # Round 6
    (1, 0),  # Round 7
    (1, 0),  # Round 8
    (0, 1),  # Round 9
    (1, 0),  # Round 10
    (1, 0),  # Round 11
    (1, 0),  # Round 12
    (0, 1),  # Round 13
    (1, 0),  # Round 14
    (1, 0),  # Round 15
    (1, 0),  # Round 16
    (0, 1),  # Round 17
    (0, 1),  # Round 18
    (1, 0),  # Round 19
    (0, 1),  # Round 20
    (0, 1),  # Round 21
    (0, 1),  # Round 22
    (1, 0),  # Round 23
    (0, 1),  # Round 24
    (0, 1),  # Round 25
    (0, 1),  # Round 26
    (1, 0),  # Round 27
    (0, 1),  # Round 28
    (0, 1),  # Round 29
    (0, 1),  # Round 30
    (1, 0),  # Round 31
    (0, 1),  # Round 32
    (0, 1),  # Round 33
    (1, 0),  # Round 34
    (1, 0),  # Round 35
    (1, 0),  # Round 36
    (0, 1),  # Round 37
    (1, 0),  # Round 38
    (1, 0),  # Round 39
    (0, 1),  # Round 40
    (1, 0),  # Round 41
    (1, 0),  # Round 42
    (0, 1),  # Round 43
    (1, 0),  # Round 44
    (1, 0),  # Round 45
    (1, 0),  # Round 46
    (0, 1),  # Round 47
    (1, 0),  # Round 48
    (0, 1),  # Round 49
    (1, 0),  # Round 50
    (0, 1),  # Round 51
    (0, 1),  # Round 52
    (0, 1),  # Round 53
    (1, 0),  # Round 54
    (0, 1),  # Round 55
    (0, 1),  # Round 56
    (1, 0),  # Round 57
    (0, 1),  # Round 58
    (0, 1),  # Round 59
    (0, 1),  # Round 60
    (1, 0),  # Round 61
    (0, 1),  # Round 62
    (0, 1),  # Round 63
    (0, 1),  # Round 64
]

# Pre-determined high probability option for each round
HIGH_PROBABILITY_OPTION = [
    'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A',  # Rounds 1-16
    'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B',  # Rounds 17-33
    'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A',  # Rounds 34-48
    'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B'  # Rounds 49-64
]


class Subsession(BaseSubsession):
    def creating_session(self):
        if self.round_number == 1:
            # Group players using group_by_arrival_time
            self.group_randomly(fixed_id_in_group=True)
            
        # Set rewards for all groups in this subsession
        for group in self.get_groups():
            group.set_round_rewards()


class Group(BaseGroup):
    # Reward outcomes for the current round
    round_reward_A = models.IntegerField()             # Reward for option A in current round (1 or 0)
    round_reward_B = models.IntegerField()             # Reward for option B in current round (1 or 0)
    
    # Probability settings for the two options
    high_probability_option = models.StringField()     # Which option ('A' or 'B') has high probability in this round
    
    # Reversal indicator
    reversal_happened = models.IntegerField(initial=0)  # 1 if a reversal happened in this round, 0 otherwise
    
    # Tracking progress
    all_first_choices_made = models.BooleanField(initial=False)
    all_second_choices_made = models.BooleanField(initial=False)
    
    def set_round_rewards(self):
        """Set the rewards for options A and B in the current round"""
        # Get rewards from the pre-generated sequence
        self.round_reward_A, self.round_reward_B = REWARD_SEQUENCE[self.round_number - 1]
        
        # Set which option has high probability in this round
        self.high_probability_option = HIGH_PROBABILITY_OPTION[self.round_number - 1]
        
        # Check if this is a reversal round
        self.reversal_happened = 1 if self.round_number in C.REVERSAL_ROUNDS else 0
        
        print(f"Round {self.round_number}: Option {self.high_probability_option} has high probability")
        print(f"Rewards: A = {self.round_reward_A}, B = {self.round_reward_B}")
        if self.reversal_happened:
            print(f"REVERSAL occurred at round {self.round_number}")
    
    # Update the get_other_players_first_choices method
    def get_other_players_first_choices(self, current_player_id):
        """Get the first choices of all other players in the group"""
        other_players = [p for p in self.get_players() if p.id_in_group != current_player_id]
        # Only include players who have made choices
        return {p.id_in_group: p.field_maybe_none('choice1') for p in other_players}
    
    def check_all_first_choices_made(self):
        """Check if all players have made their first choice"""
        for player in self.get_players():
            # Use field_maybe_none to safely check if choice1 is None
            if player.field_maybe_none('choice1') is None:
                return False
        self.all_first_choices_made = True
        return True
    
    def check_all_second_choices_made(self):
        """Check if all players have made their second choice"""
        for player in self.get_players():
            # Use field_maybe_none to safely check if choice2 is None
            if player.field_maybe_none('choice2') is None:
                return False
        self.all_second_choices_made = True
        return True
    
    def get_other_players_first_choices(self, current_player_id):
        """Get the first choices of all other players in the group"""
        other_players = [p for p in self.get_players() if p.id_in_group != current_player_id]
        return {p.id_in_group: p.field_maybe_none('choice1') for p in other_players}



class Player(BasePlayer):
    # Model assignment tracking
    assigned_model = models.StringField(initial="human")  # Records which model was assigned to this player

    # Choice and bet tracking variables
    choice1 = models.StringField(widget=widgets.RadioSelect, choices=['A', 'B'])     # Player's first choice ('A' or 'B')
    choice2 = models.StringField(widget=widgets.RadioSelect, choices=['A', 'B'])     # Player's second choice ('A' or 'B')
    bet1 = models.IntegerField(widget=widgets.RadioSelect, choices=[1, 2, 3])       # Amount bet on first choice (1-3)
    bet2 = models.IntegerField(widget=widgets.RadioSelect, choices=[1, 2, 3])       # Amount bet on second choice (1-3)

    # Choice tracking variables
    switch_vs_stay = models.IntegerField()               # Whether player switched (1) or stayed (0) between choices
    trial_reward = models.IntegerField(initial=0)        # Reward received in current trial (1 or 0)
    loss_or_gain = models.IntegerField()                 # Whether player gained (1) or lost (-1) points
    
    # Social influence tracking
    choice1_with = models.FloatField(initial=0)        # Percentage of others who made same first choice
    choice1_against = models.FloatField(initial=0)     # Percentage of others who made different first choice
    choice2_with = models.FloatField(initial=0)        # Percentage of others who made same second choice
    choice2_against = models.FloatField(initial=0)     # Percentage of others who made different second choice
    
    # Performance metrics
    choice1_accuracy = models.BooleanField(initial=0)    # Whether first choice was optimal
    choice2_accuracy = models.BooleanField(initial=0)    # Whether second choice was optimal
    choice1_accuracy_sum = models.IntegerField(initial=0)  # Sum choice1 accuracy over trials
    choice2_accuracy_sum = models.IntegerField(initial=0)  # Sum choice2 accuracy over trials
    choice1_reward_binary = models.IntegerField(initial=0)  # Whether first choice was rewarded (1) or not (0)
    choice2_reward_binary = models.IntegerField(initial=0)  # Whether second choice was rewarded (1) or not (0)
    choice1_reward_binary_sum = models.IntegerField(initial=0)  # Sum of choice1_reward_binary over trials
    choice2_reward_binary_sum = models.IntegerField(initial=0)  # Sum of choice2_reward_binary over trials

    # Earnings tracking
    choice1_earnings = models.IntegerField(initial=0)     # Points earned from first choice
    choice2_earnings = models.IntegerField(initial=0)     # Points earned from second choice
    choice1_sum_earnings = models.IntegerField(initial=0)  # Sum of choice1_earnings over trials
    choice2_sum_earnings = models.IntegerField(initial=0)  # Sum of choice2_earnings over trials
    bonus_payment_score = models.IntegerField(initial=0)  # Total bonus points earned

    # Is this player a bot? Used for analysis
    is_bot = models.BooleanField()
    
    # Virtual players' choices - First choice (tracking 4 other players)
    player1_choice_one = models.StringField()
    player2_choice_one = models.StringField()


    # Virtual players' choices - Second choice
    player1_choice_two = models.StringField()
    player2_choice_two = models.StringField()


    # Track accuracy of virtual players' choices - First choice
    player1_choice1_accuracy = models.BooleanField()
    player2_choice1_accuracy = models.BooleanField()


    # Track accuracy of virtual players' choices - Second choice
    player1_choice2_accuracy = models.BooleanField()
    player2_choice2_accuracy = models.BooleanField()


    # Track whether virtual players gained or lost points
    player1_loss_or_gain = models.IntegerField()
    player2_loss_or_gain = models.IntegerField()


    # determine if this player is a bot
    def set_bot_flag(self):
        """Set the is_bot flag based on participant.label"""
        # botex sets participant.label for bots
        if self.participant.label and 'bot' in self.participant.label.lower():
            self.is_bot = True
        # Or check if participant was created by botex
        elif hasattr(self.participant, '_is_bot') and self.participant._is_bot:
            self.is_bot = True
        # Alternative check using participant vars
        elif 'is_bot' in self.participant.vars and self.participant.vars['is_bot']:
            self.is_bot = True
        else:
            self.is_bot = False
    
    def set_model_assignment(self):
        """Set the model assignment based on actual bot status"""
        participant_code = self.participant.code
        session_config = self.session.config
        
        # Method 1: Check for position-based bot assignment
        position_model_key = f'bot_position_{self.id_in_group}_model'
        if position_model_key in session_config:
            self.assigned_model = session_config[position_model_key]
            self.is_bot = True
            print(f"Player {self.id_in_group} (participant {participant_code}): "
                f"assigned_model={self.assigned_model} via position, is_bot={self.is_bot}")
            return
        
        # Method 2: Check intended model for this player position
        intended_model_key = f'player_{self.id_in_group}_intended_model'
        if intended_model_key in session_config:
            intended_model = session_config[intended_model_key]
            # Check if this participant is actually a bot by looking at other indicators
            if (hasattr(self.participant, 'label') and self.participant.label and 'bot' in str(self.participant.label).lower()) or \
            (hasattr(self.participant, 'vars') and 'is_bot' in self.participant.vars and self.participant.vars['is_bot']):
                self.assigned_model = intended_model
                self.is_bot = True
                print(f"Player {self.id_in_group} (participant {participant_code}): "
                    f"assigned_model={self.assigned_model} via intended model, is_bot={self.is_bot}")
                return
        
        # Default: This participant is human
        self.assigned_model = "human"
        self.is_bot = False
        print(f"Player {self.id_in_group} (participant {participant_code}): "
            f"assigned_model={self.assigned_model}, is_bot={self.is_bot}")
    
    # Modify the calculate_first_choice_social_influence method
    def calculate_first_choice_social_influence(self):
        """Calculate the percentage of others who made same/different first choices"""
        # Get my choice safely using field_maybe_none
        my_choice = self.field_maybe_none('choice1')
        if my_choice is None:
            self.choice1_with = 0
            self.choice1_against = 0
            return
            
        other_players = [p for p in self.group.get_players() if p.id_in_group != self.id_in_group]
        # Only count players who have made choices
        valid_choices = [p.field_maybe_none('choice1') for p in other_players]
        valid_choices = [c for c in valid_choices if c is not None]
        
        same_choice1 = sum(1 for c in valid_choices if c == my_choice)
        
        total_valid_choices = len(valid_choices)
        if total_valid_choices > 0:
            self.choice1_with = same_choice1 / total_valid_choices
            self.choice1_against = 1 - self.choice1_with
        else:
            self.choice1_with = 0
            self.choice1_against = 0

    # Modify the calculate_second_choice_social_influence method too
    def calculate_second_choice_social_influence(self):
        """Calculate the percentage of others who made same/different second choices"""
        other_players = [p for p in self.group.get_players() if p.id_in_group != self.id_in_group]
        
        # Only count players who have made a choice
        valid_other_players = [p for p in other_players if p.choice2 is not None]
        
        # Check if this player has made a choice yet
        if self.choice2 is None:
            self.choice2_with = 0
            self.choice2_against = 0
            return
        
        same_choice2 = sum(1 for p in valid_other_players if p.choice2 == self.choice2)
        
        total_valid_players = len(valid_other_players)
        if total_valid_players > 0:
            self.choice2_with = same_choice2 / total_valid_players
            self.choice2_against = 1 - self.choice2_with
        else:
            self.choice2_with = 0
            self.choice2_against = 0
    
    def calculate_choice1_earnings(self):
        """Calculate earnings for first choice"""
        # Ensure group rewards are set for this round if not already set
        if self.group.field_maybe_none('round_reward_A') is None or self.group.field_maybe_none('round_reward_B') is None:
            self.group.set_round_rewards()
            
        # For choice1, see if it would have been rewarded
        if self.choice1 == 'A':
            choice1_reward = self.group.round_reward_A
        else:  # 'B'
            choice1_reward = self.group.round_reward_B
                
        # Set binary reward outcome
        self.choice1_reward_binary = choice1_reward
            
        # Calculate earnings
        if choice1_reward == 1:  # Would have been rewarded
            self.choice1_earnings = self.bet1 * 20  # Positive points
        else:  # Would not have been rewarded
            self.choice1_earnings = -1 * self.bet1 * 20  # Negative points
    
    def calculate_choice2_earnings(self):
        """Calculate earnings for second choice"""
        # Ensure group rewards are set for this round if not already set
        if self.group.field_maybe_none('round_reward_A') is None or self.group.field_maybe_none('round_reward_B') is None:
            self.group.set_round_rewards()
            
        # For choice2, calculate reward
        if self.choice2 == 'A':
            self.trial_reward = self.group.round_reward_A
        else:  # 'B'
            self.trial_reward = self.group.round_reward_B
        
        # Set binary reward outcome
        self.choice2_reward_binary = self.trial_reward
        
        # Calculate earnings
        if self.trial_reward == 1:  # Option was rewarded
            self.choice2_earnings = self.bet2 * 20  # Positive points
        else:  # Option was not rewarded
            self.choice2_earnings = -1 * self.bet2 * 20  # Negative points
        
        # Set whether the player gained or lost points
        self.loss_or_gain = 1 if self.choice2_earnings > 0 else -1
    
    def update_cumulative_sums(self):
        """Update all cumulative sums across rounds"""
        if self.round_number == 1:
            # First round - initialize all sums with current values
            self.choice1_accuracy_sum = int(self.choice1_accuracy)
            self.choice2_accuracy_sum = int(self.choice2_accuracy)
            self.choice1_reward_binary_sum = self.choice1_reward_binary
            self.choice2_reward_binary_sum = self.choice2_reward_binary
            self.choice1_sum_earnings = self.choice1_earnings
            self.choice2_sum_earnings = self.choice2_earnings
            self.bonus_payment_score = self.choice2_earnings  # Initialize with second choice earnings
        else:
            # Subsequent rounds - add current values to previous sums
            previous_player = self.in_round(self.round_number - 1)
            self.choice1_accuracy_sum = previous_player.choice1_accuracy_sum + int(self.choice1_accuracy)
            self.choice2_accuracy_sum = previous_player.choice2_accuracy_sum + int(self.choice2_accuracy)
            self.choice1_reward_binary_sum = previous_player.choice1_reward_binary_sum + self.choice1_reward_binary
            self.choice2_reward_binary_sum = previous_player.choice2_reward_binary_sum + self.choice2_reward_binary
            self.choice1_sum_earnings = previous_player.choice1_sum_earnings + self.choice1_earnings
            self.choice2_sum_earnings = previous_player.choice2_sum_earnings + self.choice2_earnings
            self.bonus_payment_score = previous_player.bonus_payment_score + self.choice2_earnings
    
    # Save data about other players in the group
    def save_other_players_data(self):
        """Save data about other players in the group"""
        # Get other players
        other_players = [p for p in self.group.get_players() if p.id_in_group != self.id_in_group]
        
        # Save data for up to 4 other players
        for i, p in enumerate(other_players):
            if i == 0:  # First player
                if p.choice1 is not None:
                    self.player1_choice_one = p.choice1
                if p.choice2 is not None:
                    self.player1_choice_two = p.choice2
                    self.player1_choice1_accuracy = p.choice1_accuracy
                    self.player1_choice2_accuracy = p.choice2_accuracy
                    self.player1_loss_or_gain = p.loss_or_gain
                    
            elif i == 1:  # Second player
                if p.choice1 is not None:
                    self.player2_choice_one = p.choice1
                if p.choice2 is not None:
                    self.player2_choice_two = p.choice2
                    self.player2_choice1_accuracy = p.choice1_accuracy
                    self.player2_choice2_accuracy = p.choice2_accuracy
                    self.player2_loss_or_gain = p.loss_or_gain
                    



# PAGES
class GroupingWaitPage(WaitPage):
    """Wait page to form groups based on arrival time"""
    group_by_arrival_time = True
    title_text = "Waiting for Other Players"
    body_text = "Please wait while we form groups of 3 players..."
    template_name = 'global/BotWaitPage.html'  # Use the custom template, not the default WaitPage
    
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1


class FirstDecisions(Page):
    form_model = 'player'
    form_fields = ['choice1', 'bet1']
    
    @staticmethod
    def vars_for_template(player):
        # Ensure group rewards are set for this round
        if player.round_number > 1:
            player.group.set_round_rewards()
        
        return {
            'round_number': player.round_number,
        }
    
    @staticmethod
    def before_next_page(player, timeout_happened):
        # Set model assignment on first round
        if player.round_number == 1:
            player.set_model_assignment()

        # Mark this player as having made their first choice
        player.group.check_all_first_choices_made()


class FirstDecisionsWaitPage(WaitPage):
    """Wait page after first decisions to ensure all players have made their choices"""
    title_text = "Waiting for Other Players"
    body_text = "Please wait for all players to make their initial choices..."
    template_name = 'global/BotWaitPage.html'
    
    @staticmethod
    def after_all_players_arrive(group):
        # At this point all players should have completed their choices
        # Update group-level tracking first
        group.all_first_choices_made = True
        
        # Then calculate social influence for each player
        for player in group.get_players():
            # Skip any calculations for players without choices (shouldn't happen if wait page works correctly)
            if player.field_maybe_none('choice1') is not None:
                player.calculate_first_choice_social_influence()


class SecondDecisions(Page):
    form_model = 'player'
    form_fields = ['choice2', 'bet2']
    
    @staticmethod
    def is_displayed(player):
        # Only show this page if the player has made their first choice
        return player.field_maybe_none('choice1') is not None
    
    @staticmethod
    def vars_for_template(player):
        # Get the first choices of all other players
        other_players_choices = {}
        other_player_index = 1  # Start with Player 1
        
        for p in player.group.get_players():
            if p.id_in_group != player.id_in_group:
                # Use field_maybe_none for safety
                choice = p.field_maybe_none('choice1')
                if choice is not None:
                    # Use sequential numbering instead of actual player IDs
                    other_players_choices[f"Player {other_player_index}"] = choice
                    other_player_index += 1
        
        return {
            'round_number': player.round_number,
            'choice1': player.field_maybe_none('choice1'),
            'bet1': player.field_maybe_none('bet1'),
            'other_players_choices': other_players_choices,
        }
    
    @staticmethod
    def before_next_page(player, timeout_happened):
        # Calculate earnings for first choice (not shown to player)
        player.calculate_choice1_earnings()
        
        # Calculate earnings for second choice
        player.calculate_choice2_earnings()
        
        # Update accuracy metrics
        player.choice1_accuracy = (player.choice1 == player.group.high_probability_option)
        player.choice2_accuracy = (player.choice2 == player.group.high_probability_option)
        
        # Update all cumulative sums
        player.update_cumulative_sums()
        
        # Calculate if player switched or stayed
        player.switch_vs_stay = 1 if player.choice1 != player.choice2 else 0
        
        # Check if all players have made their second choices
        player.group.check_all_second_choices_made()


class SecondDecisionsWaitPage(WaitPage):
    """Wait page after second decisions to ensure all players have made their choices"""
    title_text = "Waiting for Other Players"
    body_text = "Please wait for all players to make their second choices..."
    template_name = 'global/BotWaitPage.html'
    
    # Update SecondDecisionsWaitPage similarly
    @staticmethod
    def after_all_players_arrive(group):
        # Calculate social influence for second choices for players who have made choices
        for player in group.get_players():
            if player.choice2 is not None:
                player.calculate_second_choice_social_influence()
                # Save other players' data for later analysis
                player.save_other_players_data()


class RoundResults(Page):
    @staticmethod
    def vars_for_template(player):
        # Calculate the absolute value of points earned for display
        points_display = abs(player.choice2_earnings)
        
        # Get the second choices of all players with sequential numbering
        all_players_results = {}
        other_player_index = 1  # Start with Player 1
        
        for p in player.group.get_players():
            if p.id_in_group != player.id_in_group:
                all_players_results[f"Player {other_player_index}"] = {
                    'choice': p.choice2,
                    'outcome': 'Correct' if p.trial_reward == 1 else 'Incorrect'
                }
                other_player_index += 1
        
        return {
            'round_number': player.round_number,
            'choice2': player.choice2,
            'choice_outcome': "correct" if player.trial_reward == 1 else "incorrect",
            'points_earned': player.choice2_earnings,
            'points_display': points_display,
            'total_points': player.bonus_payment_score,
            'all_players_results': all_players_results,
        }


class ResultsWaitPage(WaitPage):
    """Wait page after results to ensure all players are ready for the next round"""
    title_text = "Waiting for Other Players"
    body_text = "Please wait for all players to review their results..."
    template_name = 'global/WaitPage.html'
    
    @staticmethod
    def is_displayed(player):
        return player.round_number < C.NUM_ROUNDS


class FinalResults(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS
    
    @staticmethod
    def before_next_page(player, timeout_happened):
        # Store cumulative data in participant vars for use in subsequent apps
        player.participant.vars['choice1_sum_earnings'] = player.choice1_sum_earnings
        player.participant.vars['choice2_sum_earnings'] = player.choice2_sum_earnings
        player.participant.vars['choice1_accuracy_sum'] = player.choice1_accuracy_sum
        player.participant.vars['choice2_accuracy_sum'] = player.choice2_accuracy_sum
        player.participant.vars['choice1_reward_binary_sum'] = player.choice1_reward_binary_sum
        player.participant.vars['choice2_reward_binary_sum'] = player.choice2_reward_binary_sum
        player.participant.vars['bonus_payoff'] = cu(max(0, player.bonus_payment_score / 600))
        player.participant.finished = True
    
    @staticmethod
    def vars_for_template(player):
        return {
            'bonus_payment_score': player.bonus_payment_score,
            'bonus_payoff': cu(max(0, player.bonus_payment_score / 600)),
        }


page_sequence = [
    GroupingWaitPage,
    FirstDecisions,
    FirstDecisionsWaitPage,
    SecondDecisions,
    SecondDecisionsWaitPage,
    RoundResults,
    ResultsWaitPage,
    FinalResults
]