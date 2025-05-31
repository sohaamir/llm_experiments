"""
App-specific prompting strategies for multi-round Rock Paper Scissors.
Uses the general framework convention with get_prompts() function.

'system' prompt is used to set the context for the bot,
'analyze_page_q' is used to provide the bot with the game history and questions to answer.

The specific prompts are those used by Vidler and Walsh (2025) https://arxiv.org/pdf/2503.02582 with the exception of P5 which is explicitly designed to elicit theory-of-mind reasoning about the game.
"""

def get_prompts(role=None):
    """
    Get the appropriate prompts for the specified role in multi-round RPS.
    
    Args:
        role (str): Either 'P2', 'P3c', 'P4', 'P5', or None for default
    
    Returns:
        dict: Dictionary containing the prompts for botex
    """
    
    if role == 'P2':
        return {
            "system": """You are participating in an experiment against another player. You are playing a game where in each round you will have three options to choose from; A, B and C. B beats A, A beats C, and C beats B. Matching moves result in a tie where both players get tie points. You will play multiple rounds and your goal is to maximize your total points.""",
            "analyze_page_q": """Only choose a single letter: A, B, or C in each round.

Page content: {body}
Questions: {questions_json}

Respond with valid JSON only."""
        }

    elif role == 'P3c':
        return {
            "system": """You are participating in a multi-round experiment against another player. You will play multiple rounds and your goal is to maximize your total points. Always respond in valid JSON format only.""",
            "analyze_page_q": """Make strategic choices based on game patterns and theory. Rules: Randomly choose one of: 'P' (Paper), 'R' (Rock), or 'S' (Scissors). Payoff: Paper beats Rock, Rock beats Scissors, Scissors beats Paper, all other combinations are a tie. The optimal strategy is to randomise your selection of R,P,S. Only choose a single letter: P, R, or S

Page content: {body}
Questions: {questions_json}

Respond with valid JSON only."""
        }

    elif role == 'P4':
        return {
            "system": """You are participating in a multi-round Rock Paper Scissors experiment against another player. You will play multiple rounds and your goal is to maximize your total points. Always respond in valid JSON format only.""",
            "analyze_page_q": """You are playing the strategic game called Rock Paper Scissors and you need to choose what your play will be. You can choose one choice from the following list: Rock, Paper or Scissors. Your payoff will depend on the other players choice too: Paper beats Rock and wins points, Scissors beats Paper and wins points, Rock beats Scissors and wins points, all other combinations, and a tie, win fewer points. Only choose a single letter: R, P, or S

Page content: {body}
Questions: {questions_json}

Respond with valid JSON only."""
        }

    elif role == 'P5':
        return {
            "system": """You are participating in a multi-round Rock Paper Scissors experiment against another player. You will play multiple rounds and your goal is to maximize your total points. Always respond in valid JSON format only.""",
            "analyze_page_q": """You are playing the strategic game called Rock Paper Scissors and you need to choose what your play will be. You can choose one choice from the following list: Rock, Paper or Scissors. Your payoff will depend on the other players choice too: Paper beats Rock and wins points, Scissors beats Paper and wins points, Rock beats Scissors and wins points, all other combinations, and a tie, win fewer points. Remember that the other player will likely try to predict your choice based on your previous moves and patterns, so you should try to adjust your choice accordingly to stay unpredictable and maximize your chances of winning. Only choose a single letter: R, P, or S

Page content: {body}
Questions: {questions_json}

Respond with valid JSON only."""
        }

    else:
        # Default strategy - only used when no role is specified
        return {
            "system": """You are participating in a multi-round Rock Paper Scissors experiment against another player. You will play multiple rounds and your goal is to maximize your total points. Always respond in valid JSON format only.""",
            "analyze_page_q": """You are playing multi-round Rock Paper Scissors against another player.

Game Rules:
- Rock (R) beats Scissors (S)
- Paper (P) beats Rock (R)  
- Scissors (S) beats Paper (P)
- Same choice = tie

Page content: {body}
Questions: {questions_json}

Make your choice using your best judgment for this Rock Paper Scissors game.

Respond with valid JSON only."""
        }


def get_available_roles():
    """
    Get list of available roles for this app.
    
    Returns:
        list: List of available role names
    """
    return ['P2', 'P3c', 'P4', 'P5']


def get_role_description(role):
    """
    Get a human-readable description of the role.
    
    Args:
        role (str): The role name
        
    Returns:
        str: Human-readable description
    """
    descriptions = {
        'P2': 'Detailed payoff explanation with explicit scoring structure',
        'P3c': 'Strategic emphasis with randomization advice and optimal strategy guidance',
        'P4': 'Clear points explanation with strategic framing and outcome focus',
        'P5': 'Strategic framing with explicit opponent prediction awareness and counter-strategy advice'
    }
    return descriptions.get(role, f'Unknown role: {role}')