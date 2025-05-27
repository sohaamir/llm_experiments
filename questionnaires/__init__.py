from otree.api import *

author = 'Aamir Sohail'

doc = """
Psychological Questionnaires Battery FOR LLM bots including LSAS, DASS, AQ-10, AMI, SRP-SF, and SSMS
"""

class C(BaseConstants):
    NAME_IN_URL = 'questionnaires'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    
    # Number of questions in each questionnaire
    NUM_LSAS_QUESTIONS = 24  # Each question has two parts (anxiety and avoidance)
    NUM_DASS_QUESTIONS = 21
    NUM_AQ_QUESTIONS = 10
    NUM_AMI_QUESTIONS = 18
    NUM_SRPSF_QUESTIONS = 29
    NUM_SSMS_QUESTIONS = 21


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass

class Player(BasePlayer):
    # Generate LSAS anxiety fields (all 24) - using different variable name
    for lsas_idx in range(1, C.NUM_LSAS_QUESTIONS + 1):
        locals()[f'lsas_anxiety_{lsas_idx}'] = models.IntegerField(
            choices=[
                [0, 'None'],
                [1, 'Mild'],
                [2, 'Moderate'],
                [3, 'Severe'],
            ],
            widget=widgets.RadioSelect,
            label=""
        )
    # Clean up the loop variable
    del lsas_idx
    
    # Generate LSAS avoidance fields (all 24) - using different variable name
    for lsas_avoid_idx in range(1, C.NUM_LSAS_QUESTIONS + 1):
        locals()[f'lsas_avoidance_{lsas_avoid_idx}'] = models.IntegerField(
            choices=[
                [0, 'Never (0%)'],
                [1, 'Occasionally (1-33%)'],
                [2, 'Often (34-66%)'],
                [3, 'Usually (67-100%)'],
            ],
            widget=widgets.RadioSelect,
            label=""
        )
    # Clean up the loop variable
    del lsas_avoid_idx
    
    # Total scores for LSAS
    lsas_anxiety_score = models.IntegerField()
    lsas_avoidance_score = models.IntegerField()
    lsas_total_score = models.IntegerField()
    
    # LSAS Subscales
    lsas_p_score = models.IntegerField()  # Performance anxiety
    lsas_s_score = models.IntegerField()  # Social interaction anxiety
    
    # Fields for DASS (Depression Anxiety Stress Scale)
    # Each item is scored from 0 (Did not apply to me at all) to 3 (Applied to me very much)
    for dass_idx in range(1, C.NUM_DASS_QUESTIONS + 1):
        locals()[f'dass_{dass_idx}'] = models.IntegerField(
            choices=[
                [0, 'Did not apply to me at all'],
                [1, 'Applied to me to some degree, or some of the time'],
                [2, 'Applied to me to a considerable degree, or a good part of time'],
                [3, 'Applied to me very much, or most of the time'],
            ],
            widget=widgets.RadioSelect,
            label=f"Question {dass_idx}"
        )
    # Clean up the loop variable
    del dass_idx
    
    # Total scores for DASS
    dass_depression_score = models.IntegerField()  # Doubled scores
    dass_anxiety_score = models.IntegerField()     # Doubled scores
    dass_stress_score = models.IntegerField()      # Doubled scores
    dass_total_score = models.IntegerField()
    
    # Fields for AQ-10 (Autism Quotient-10) - Updated with direct 0/1 scoring
    # Questions 1, 7, 8, 10 are scored 1 for agree, 0 for disagree
    # Questions 2, 3, 4, 5, 6, 9 are scored 1 for disagree, 0 for agree

    # Questions where agree = 1 point (1, 7, 8, 10)
    aq_1 = models.IntegerField(
        choices=[
            [1, 'Definitely Agree'],
            [1, 'Slightly Agree'],
            [0, 'Slightly Disagree'],
            [0, 'Definitely Disagree'],
        ],
        widget=widgets.RadioSelect,
        label="Question 1"
    )

    aq_7 = models.IntegerField(
        choices=[
            [1, 'Definitely Agree'],
            [1, 'Slightly Agree'],
            [0, 'Slightly Disagree'],
            [0, 'Definitely Disagree'],
        ],
        widget=widgets.RadioSelect,
        label="Question 7"
    )

    aq_8 = models.IntegerField(
        choices=[
            [1, 'Definitely Agree'],
            [1, 'Slightly Agree'],
            [0, 'Slightly Disagree'],
            [0, 'Definitely Disagree'],
        ],
        widget=widgets.RadioSelect,
        label="Question 8"
    )

    aq_10 = models.IntegerField(
        choices=[
            [1, 'Definitely Agree'],
            [1, 'Slightly Agree'],
            [0, 'Slightly Disagree'],
            [0, 'Definitely Disagree'],
        ],
        widget=widgets.RadioSelect,
        label="Question 10"
    )

    # Questions where disagree = 1 point (2, 3, 4, 5, 6, 9)
    aq_2 = models.IntegerField(
        choices=[
            [0, 'Definitely Agree'],
            [0, 'Slightly Agree'],
            [1, 'Slightly Disagree'],
            [1, 'Definitely Disagree'],
        ],
        widget=widgets.RadioSelect,
        label="Question 2"
    )

    aq_3 = models.IntegerField(
        choices=[
            [0, 'Definitely Agree'],
            [0, 'Slightly Agree'],
            [1, 'Slightly Disagree'],
            [1, 'Definitely Disagree'],
        ],
        widget=widgets.RadioSelect,
        label="Question 3"
    )

    aq_4 = models.IntegerField(
        choices=[
            [0, 'Definitely Agree'],
            [0, 'Slightly Agree'],
            [1, 'Slightly Disagree'],
            [1, 'Definitely Disagree'],
        ],
        widget=widgets.RadioSelect,
        label="Question 4"
    )

    aq_5 = models.IntegerField(
        choices=[
            [0, 'Definitely Agree'],
            [0, 'Slightly Agree'],
            [1, 'Slightly Disagree'],
            [1, 'Definitely Disagree'],
        ],
        widget=widgets.RadioSelect,
        label="Question 5"
    )

    aq_6 = models.IntegerField(
        choices=[
            [0, 'Definitely Agree'],
            [0, 'Slightly Agree'],
            [1, 'Slightly Disagree'],
            [1, 'Definitely Disagree'],
        ],
        widget=widgets.RadioSelect,
        label="Question 6"
    )

    aq_9 = models.IntegerField(
        choices=[
            [0, 'Definitely Agree'],
            [0, 'Slightly Agree'],
            [1, 'Slightly Disagree'],
            [1, 'Definitely Disagree'],
        ],
        widget=widgets.RadioSelect,
        label="Question 9"
    )
    
    # Attention check questions for AQ-10
    aq_check_1 = models.IntegerField(
        choices=[
            [0, 'Definitely Agree'],
            [0, 'Slightly Agree'],
            [0, 'Slightly Disagree'],
            [1, 'Definitely Disagree'],
        ],
        widget=widgets.RadioSelect,
        label="Please select 'Definitely Disagree' for this question."
    )

    aq_check_2 = models.IntegerField(
        choices=[
            [1, 'Definitely Agree'],
            [0, 'Slightly Agree'],
            [0, 'Slightly Disagree'],
            [0, 'Definitely Disagree'],
        ],
        widget=widgets.RadioSelect,
        label="Please select 'Definitely Agree' for this question."
    )

    aq_check_3 = models.IntegerField(
        choices=[
            [0, 'Definitely Agree'],
            [1, 'Slightly Agree'],
            [0, 'Slightly Disagree'],
            [0, 'Definitely Disagree'],
        ],
        widget=widgets.RadioSelect,
        label="Please select 'Slightly Agree' for this question."
    )
    
    # Total score for AQ-10
    aq_total_score = models.IntegerField()
    
    # Fields for AMI (Ambivalent Misogyny Inventory) - Updated to 18 questions
    # Scored from 4 (Completely Untrue) to 0 (Completely True)
    for ami_idx in range(1, C.NUM_AMI_QUESTIONS + 1):
        locals()[f'ami_{ami_idx}'] = models.IntegerField(
            choices=[
                [4, 'Completely Untrue'],
                [3, 'Somewhat Untrue'],
                [2, 'Neither True nor Untrue'],
                [1, 'Somewhat True'],
                [0, 'Completely True'],
            ],
            widget=widgets.RadioSelect,
            label=f"Question {ami_idx}"
        )
    # Clean up the loop variable
    del ami_idx
    
    # Total score for AMI
    ami_total_score = models.IntegerField()
    
    # AMI Subscales (updated for 18 questions)
    ami_es_score = models.IntegerField()  # Emotional Stereotyping subscale
    ami_sm_score = models.IntegerField()  # Sexual Manipulation subscale
    ami_ba_score = models.IntegerField()  # Benevolent Acts subscale
    
    # Fields for SRP-SF (Self-Report Psychopathy Scale-Short Form)
    # Question 2 is reverse scored (5 for Disagree Strongly, 1 for Agree Strongly)
    # All other questions are standard scored (1 for Disagree Strongly, 5 for Agree Strongly)

    # Standard scored questions (all except question 2)
    for srpsf_idx in [1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 
                      17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29]:
        locals()[f'srpsf_{srpsf_idx}'] = models.IntegerField(
            choices=[
                [1, 'Disagree Strongly'],
                [2, 'Disagree'],
                [3, 'Neutral'],
                [4, 'Agree'],
                [5, 'Agree Strongly'],
            ],
            widget=widgets.RadioSelect,
            label=f"Question {srpsf_idx}"
        )
    # Clean up the loop variable
    del srpsf_idx

    # Reverse scored question 2
    srpsf_2 = models.IntegerField(
        choices=[
            [5, 'Disagree Strongly'],
            [4, 'Disagree'],
            [3, 'Neutral'],
            [2, 'Agree'],
            [1, 'Agree Strongly'],
        ],
        widget=widgets.RadioSelect,
        label="Question 2"
    )
    
    # Total score for SRP-SF
    srpsf_total_score = models.IntegerField()
    
    # SRP-SF Subscales
    srpsf_ipm_score = models.IntegerField()  # Interpersonal Manipulation
    srpsf_ca_score = models.IntegerField()   # Callous Affect
    srpsf_els_score = models.IntegerField()  # Erratic Lifestyle
    srpsf_ct_score = models.IntegerField()   # Criminal Tendencies
    
    # Fields for SSMS (Schizotypal Symptoms & Mood Scale)
    # Questions where Yes=1, No=0: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 17, 20, 21]
    # Questions where Yes=0, No=1: [14, 15, 16, 18, 19]

    # Standard scored questions (Yes=1, No=0)
    for ssms_std_idx in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 17, 20, 21]:
        locals()[f'ssms_{ssms_std_idx}'] = models.IntegerField(
            choices=[
                [0, 'No'],
                [1, 'Yes'],
            ],
            widget=widgets.RadioSelect,
            label=f"Question {ssms_std_idx}"
        )
    # Clean up the loop variable
    del ssms_std_idx

    # Reverse scored questions (Yes=0, No=1)
    for ssms_rev_idx in [14, 15, 16, 18, 19]:
        locals()[f'ssms_{ssms_rev_idx}'] = models.IntegerField(
            choices=[
                [1, 'No'],
                [0, 'Yes'],
            ],
            widget=widgets.RadioSelect,
            label=f"Question {ssms_rev_idx}"
        )
    # Clean up the loop variable
    del ssms_rev_idx
    
    # Total score for SSMS
    ssms_total_score = models.IntegerField()
    
    # SSMS Subscales
    ssms_cd_score = models.IntegerField()  # Cognitive Disorganization
    ssms_ia_score = models.IntegerField()  # Introvertive Anhedonia
    

    # Calculate LSAS scores
    def calculate_lsas_scores(self):
        # Calculate main scores
        anxiety_score = sum(getattr(self, f'lsas_anxiety_{idx}', 0) or 0 for idx in range(1, C.NUM_LSAS_QUESTIONS + 1))
        avoidance_score = sum(getattr(self, f'lsas_avoidance_{idx}', 0) or 0 for idx in range(1, C.NUM_LSAS_QUESTIONS + 1))
        self.lsas_anxiety_score = anxiety_score
        self.lsas_avoidance_score = avoidance_score
        self.lsas_total_score = anxiety_score + avoidance_score
        
        # Calculate LSAS-P subscale (Performance anxiety)
        lsas_p_questions = [1, 2, 3, 4, 6, 8, 9, 13, 14, 16, 17, 20, 21]
        lsas_p_anxiety = sum(getattr(self, f'lsas_anxiety_{idx}', 0) or 0 for idx in lsas_p_questions)
        lsas_p_avoidance = sum(getattr(self, f'lsas_avoidance_{idx}', 0) or 0 for idx in lsas_p_questions)
        self.lsas_p_score = lsas_p_anxiety + lsas_p_avoidance
        
        # Calculate LSAS-S subscale (Social interaction anxiety)
        lsas_s_questions = [5, 7, 10, 11, 12, 15, 18, 19, 22, 23, 24]
        lsas_s_anxiety = sum(getattr(self, f'lsas_anxiety_{idx}', 0) or 0 for idx in lsas_s_questions)
        lsas_s_avoidance = sum(getattr(self, f'lsas_avoidance_{idx}', 0) or 0 for idx in lsas_s_questions)
        self.lsas_s_score = lsas_s_anxiety + lsas_s_avoidance
    
    # Calculate DASS scores
    def calculate_dass_scores(self):
        # Depression items (DASS-D)
        depression_items = [3, 5, 10, 13, 16, 17, 21]
        # Anxiety items (DASS-A)
        anxiety_items = [2, 4, 7, 9, 15, 19, 20]
        # Stress items (DASS-S)
        stress_items = [1, 6, 8, 11, 12, 14, 18]
        
        # Double the scores for each subscale as per instructions
        depression_score = sum(getattr(self, f'dass_{idx}') for idx in depression_items) * 2
        anxiety_score = sum(getattr(self, f'dass_{idx}') for idx in anxiety_items) * 2
        stress_score = sum(getattr(self, f'dass_{idx}') for idx in stress_items) * 2
        
        self.dass_depression_score = depression_score
        self.dass_anxiety_score = anxiety_score
        self.dass_stress_score = stress_score
        self.dass_total_score = depression_score + anxiety_score + stress_score
    
    # Calculate AQ-10 scores (updated for direct 0/1 scoring)
    def calculate_aq_scores(self):
        # Since questions are now directly scored as 0/1, just sum them up
        self.aq_total_score = sum(getattr(self, f'aq_{idx}') for idx in range(1, C.NUM_AQ_QUESTIONS + 1))
    
    # Calculate AMI scores
    def calculate_ami_score(self):
        # Total score
        self.ami_total_score = sum(getattr(self, f'ami_{idx}') for idx in range(1, C.NUM_AMI_QUESTIONS + 1))
        
        # AMI-ES (Emotional Stereotyping) - questions 1, 6, 7, 13, 16, 18
        ami_es_items = [1, 6, 7, 13, 16, 18]
        self.ami_es_score = sum(getattr(self, f'ami_{idx}') for idx in ami_es_items)
        
        # AMI-SM (Sexual Manipulation) - questions 2, 3, 4, 8, 14, 17
        ami_sm_items = [2, 3, 4, 8, 14, 17]
        self.ami_sm_score = sum(getattr(self, f'ami_{idx}') for idx in ami_sm_items)
        
        # AMI-BA (Benevolent Acts) - questions 5, 9, 10, 11, 12, 15
        ami_ba_items = [5, 9, 10, 11, 12, 15]
        self.ami_ba_score = sum(getattr(self, f'ami_{idx}') for idx in ami_ba_items)
    
    # Calculate SRP-SF scores (updated for question 2 reverse scoring)
    def calculate_srpsf_score(self):
        # All questions are now properly scored in their field definitions
        # Question 2 is reverse scored in the field definition, so we can sum directly
        self.srpsf_total_score = sum(getattr(self, f'srpsf_{idx}') for idx in range(1, C.NUM_SRPSF_QUESTIONS + 1))
        
        # SRPSF-IPM (Interpersonal Manipulation) - questions 7, 9, 10, 15, 19, 23, 26
        srpsf_ipm_items = [7, 9, 10, 15, 19, 23, 26]
        self.srpsf_ipm_score = sum(getattr(self, f'srpsf_{idx}') for idx in srpsf_ipm_items)
        
        # SRPSF-CA (Callous Affect) - questions 3, 8, 13, 16, 18, 24, 28
        srpsf_ca_items = [3, 8, 13, 16, 18, 24, 28]
        self.srpsf_ca_score = sum(getattr(self, f'srpsf_{idx}') for idx in srpsf_ca_items)
        
        # SRPSF-ELS (Erratic Lifestyle) - questions 1, 4, 11, 14, 17, 21, 27
        srpsf_els_items = [1, 4, 11, 14, 17, 21, 27]
        self.srpsf_els_score = sum(getattr(self, f'srpsf_{idx}') for idx in srpsf_els_items)
        
        # SRPSF-CT (Criminal Tendencies) - questions 2, 5, 6, 12, 22, 25, 29
        # Question 2 is reverse scored in the field definition, so we can include it directly
        srpsf_ct_items = [2, 5, 6, 12, 22, 25, 29]
        self.srpsf_ct_score = sum(getattr(self, f'srpsf_{idx}') for idx in srpsf_ct_items)

    # Calculate SSMS scores (updated for direct 0/1 scoring)
    def calculate_ssms_score(self):
        # Since questions are now directly scored as 0/1 based on their logic, just sum them up
        self.ssms_total_score = sum(getattr(self, f'ssms_{idx}') for idx in range(1, C.NUM_SSMS_QUESTIONS + 1))
        
        # SSMS-CD (Cognitive Disorganization) - questions 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11
        # All CD items are standard scored (Yes=1)
        ssms_cd_items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        self.ssms_cd_score = sum(getattr(self, f'ssms_{idx}') for idx in ssms_cd_items)
        
        # SSMS-IA (Introvertive Anhedonia) - questions 12, 13, 14, 15, 16, 17, 18, 19, 20, 21
        # Questions are already scored correctly in their field definitions
        ssms_ia_items = [12, 13, 14, 15, 16, 17, 18, 19, 20, 21]
        self.ssms_ia_score = sum(getattr(self, f'ssms_{idx}') for idx in ssms_ia_items)


# PAGES
class Instructions(Page):
    """General instructions for the questionnaire battery"""
    pass

# LSAS PAGES
class LSAS1(Page):
    """Liebowitz Social Anxiety Scale - Part 1 (Situations 1-8)"""
    form_model = 'player'
    form_fields = [
        'lsas_anxiety_1', 'lsas_avoidance_1',
        'lsas_anxiety_2', 'lsas_avoidance_2',
        'lsas_anxiety_3', 'lsas_avoidance_3',
        'lsas_anxiety_4', 'lsas_avoidance_4',
        'lsas_anxiety_5', 'lsas_avoidance_5',
        'lsas_anxiety_6', 'lsas_avoidance_6',
        'lsas_anxiety_7', 'lsas_avoidance_7',
        'lsas_anxiety_8', 'lsas_avoidance_8',
    ]

class LSAS2(Page):
    """Liebowitz Social Anxiety Scale - Part 2 (Situations 9-16)"""
    form_model = 'player'
    form_fields = [
        'lsas_anxiety_9', 'lsas_avoidance_9',
        'lsas_anxiety_10', 'lsas_avoidance_10',
        'lsas_anxiety_11', 'lsas_avoidance_11',
        'lsas_anxiety_12', 'lsas_avoidance_12',
        'lsas_anxiety_13', 'lsas_avoidance_13',
        'lsas_anxiety_14', 'lsas_avoidance_14',
        'lsas_anxiety_15', 'lsas_avoidance_15',
        'lsas_anxiety_16', 'lsas_avoidance_16',
    ]

class LSAS3(Page):
    """Liebowitz Social Anxiety Scale - Part 3 (Situations 17-24)"""
    form_model = 'player'
    form_fields = [
        'lsas_anxiety_17', 'lsas_avoidance_17',
        'lsas_anxiety_18', 'lsas_avoidance_18',
        'lsas_anxiety_19', 'lsas_avoidance_19',
        'lsas_anxiety_20', 'lsas_avoidance_20',
        'lsas_anxiety_21', 'lsas_avoidance_21',
        'lsas_anxiety_22', 'lsas_avoidance_22',
        'lsas_anxiety_23', 'lsas_avoidance_23',
        'lsas_anxiety_24', 'lsas_avoidance_24',
    ]
    
    @staticmethod
    def before_next_page(player, timeout_happened):
        # Calculate scores only after all questions are completed
        player.calculate_lsas_scores()

# DASS PAGES
class DASS1(Page):
    """Depression Anxiety Stress Scale - Part 1 (Questions 1-7)"""
    form_model = 'player'
    form_fields = [
        'dass_1', 'dass_2', 'dass_3', 'dass_4', 'dass_5', 'dass_6', 'dass_7'
    ]

class DASS2(Page):
    """Depression Anxiety Stress Scale - Part 2 (Questions 8-14)"""
    form_model = 'player'
    form_fields = [
        'dass_8', 'dass_9', 'dass_10', 'dass_11', 'dass_12', 'dass_13', 'dass_14'
    ]

class DASS3(Page):
    """Depression Anxiety Stress Scale - Part 3 (Questions 15-21)"""
    form_model = 'player'
    form_fields = [
        'dass_15', 'dass_16', 'dass_17', 'dass_18', 'dass_19', 'dass_20', 'dass_21'
    ]
    
    @staticmethod
    def before_next_page(player, timeout_happened):
        # Calculate scores only after all questions are completed
        player.calculate_dass_scores()

# AQ PAGE
class AQ(Page):
    """Autism Quotient-10"""
    form_model = 'player'
    
    @staticmethod
    def get_form_fields(player):
        aq_fields = [f'aq_{idx}' for idx in range(1, C.NUM_AQ_QUESTIONS + 1)]
        check_fields = ['aq_check_1', 'aq_check_2', 'aq_check_3']
        return aq_fields + check_fields
    
    @staticmethod
    def before_next_page(player, timeout_happened):
        player.calculate_aq_scores()

# AMI PAGES
class AMI1(Page):
    """Ambivalent Misogyny Inventory - Part 1 (Questions 1-9)"""
    form_model = 'player'
    form_fields = [
        'ami_1', 'ami_2', 'ami_3', 'ami_4', 'ami_5', 'ami_6', 'ami_7', 'ami_8', 'ami_9'
    ]

class AMI2(Page):
    """Ambivalent Misogyny Inventory - Part 2 (Questions 10-18)"""
    form_model = 'player'
    form_fields = [
        'ami_10', 'ami_11', 'ami_12', 'ami_13', 'ami_14', 'ami_15', 'ami_16', 'ami_17', 'ami_18'
    ]
    
    @staticmethod
    def before_next_page(player, timeout_happened):
        # Calculate scores only after all questions are completed
        player.calculate_ami_score()

# SRP-SF PAGES
class SRPSF1(Page):
    """Self-Report Psychopathy Scale-Short Form - Part 1 (Questions 1-10)"""
    form_model = 'player'
    form_fields = [
        'srpsf_1', 'srpsf_2', 'srpsf_3', 'srpsf_4', 'srpsf_5',
        'srpsf_6', 'srpsf_7', 'srpsf_8', 'srpsf_9', 'srpsf_10'
    ]

class SRPSF2(Page):
    """Self-Report Psychopathy Scale-Short Form - Part 2 (Questions 11-20)"""
    form_model = 'player'
    form_fields = [
        'srpsf_11', 'srpsf_12', 'srpsf_13', 'srpsf_14', 'srpsf_15',
        'srpsf_16', 'srpsf_17', 'srpsf_18', 'srpsf_19', 'srpsf_20'
    ]

class SRPSF3(Page):
    """Self-Report Psychopathy Scale-Short Form - Part 3 (Questions 21-29)"""
    form_model = 'player'
    form_fields = [
        'srpsf_21', 'srpsf_22', 'srpsf_23', 'srpsf_24', 'srpsf_25',
        'srpsf_26', 'srpsf_27', 'srpsf_28', 'srpsf_29'
    ]
    
    @staticmethod
    def before_next_page(player, timeout_happened):
        # Calculate scores only after all questions are completed
        player.calculate_srpsf_score()

# SSMS PAGES
class SSMS1(Page):
    """Schizotypal Symptoms & Mood Scale - Part 1 (Questions 1-11)"""
    form_model = 'player'
    form_fields = [
        'ssms_1', 'ssms_2', 'ssms_3', 'ssms_4', 'ssms_5', 'ssms_6',
        'ssms_7', 'ssms_8', 'ssms_9', 'ssms_10', 'ssms_11'
    ]

class SSMS2(Page):
    """Schizotypal Symptoms & Mood Scale - Part 2 (Questions 12-21)"""
    form_model = 'player'
    form_fields = [
        'ssms_12', 'ssms_13', 'ssms_14', 'ssms_15', 'ssms_16',
        'ssms_17', 'ssms_18', 'ssms_19', 'ssms_20', 'ssms_21'
    ]
    
    @staticmethod
    def before_next_page(player, timeout_happened):
        # Calculate scores only after all questions are completed
        player.calculate_ssms_score()

page_sequence = [
    Instructions,
    LSAS1,
    LSAS2,
    LSAS3,
    DASS1,
    DASS2,
    DASS3,
    AQ,
    AMI1,
    AMI2,
    SRPSF1,
    SRPSF2,
    SRPSF3,
    SSMS1,
    SSMS2
]