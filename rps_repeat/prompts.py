"""
App-specific prompting strategies for multi-round Rock Paper Scissors.
Uses the general framework convention with get_prompts() function.
"""

def get_prompts(role=None):
    """
    Get the appropriate prompts for the specified role in multi-round RPS.
    
    Args:
        role (str): Either 'P2', 'P3c', 'P4', or None for default
    
    Returns:
        dict: Dictionary containing the prompts for botex
    """
    
    if role == 'P2':
        return {
            "system": """You are participating in a multi-round Rock Paper Scissors experiment against another player. You will play multiple rounds and your goal is to maximize your total points. Always respond in valid JSON format only.""",
            "analyze_page_q": """You are playing Rock Paper Scissors where winning awards points and losing gives fewer points. Paper beats Rock by covering it, Rock beats Scissors by breaking them, and Scissors beats Paper by cutting it. Matching moves result in a tie where both players get tie points. The payoffs are written as (Player 1 score, Player 2 score) for each possible combination. Only choose a single letter: R, P, or S

Page content: {body}
Questions: {questions_json}

Respond with valid JSON only."""
        }

    elif role == 'P3c':
        return {
            "system": """You are participating in a multi-round Rock Paper Scissors experiment against another player. You will play multiple rounds and your goal is to maximize your total points. Always respond in valid JSON format only.""",
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
    return ['P2', 'P3c', 'P4']


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
        'P4': 'Clear points explanation with strategic framing and outcome focus'
    }
    return descriptions.get(role, f'Unknown role: {role}')