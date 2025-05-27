"""
App-specific prompting strategies for single-player Rock Paper Scissors.
Uses the general framework convention with get_prompts() function.
"""

def get_prompts(role=None):
    """
    Get the appropriate prompts for the specified RPS strategy.
    
    Args:
        role (str): One of P1, P2r, P2p, P2s, P3a, P3b, P3c, P4, or None for default
    
    Returns:
        dict: Dictionary containing the prompts for botex
    """
    
    # Base system prompt for all strategies
    base_system = """You are participating in a Rock Paper Scissors experiment. 
    You must make a single choice when prompted. 
    Always respond in valid JSON format only."""
    
    # Base analyze prompt
    base_analyze = """You are playing Rock Paper Scissors.

Page content: {body}
Questions: {questions_json}

Respond with valid JSON only."""
    
    # Strategy-specific modifications based on role
    if role == 'P1':
        strategy_addition = """

Rules: (1) Choose: 'R' (Rock), 'P' (Paper), or 'S' (Scissors) (2) Winning conditions: Rock crushes Scissors, Paper covers Rock, Scissors cuts Paper (3) Analyze the game history to identify patterns (4) Only choose a single letter: 'R', 'P', or 'S'"""

    elif role == 'P2r':
        strategy_addition = """

You are playing Rock Paper Scissors where winning awards 1 point and losing gives 0 points. Paper beats Rock by covering it, Rock beats Scissors by breaking them, and Scissors beats Paper by cutting it. Matching moves result in a tie where both players get 0 points. The payoffs are written as (Player 1 score, Player 2 score) for each possible combination. Only choose a single letter: R, P, or S"""

    elif role == 'P2p':
        strategy_addition = """

You are playing Rock Paper Scissors where winning awards 1 point and losing gives 0 points. Scissors beats Paper by cutting it, Paper beats Rock by covering it, and Rock beats Scissors by breaking them. Matching moves result in a tie where both players get 0 points. Choose one of: 'P' (Paper), 'S' (Scissors), or 'R' (Rock). Only choose a single letter: P, S, or R"""

    elif role == 'P2s':
        strategy_addition = """

You are playing Rock Paper Scissors where winning awards 1 point and losing gives 0 points. Rock beats Scissors by breaking them, Scissors beats Paper by cutting it, and Paper beats Rock by covering it. Matching moves result in a tie where both players get 0 points. Choose one of: 'S' (Scissors), 'R' (Rock), or 'P' (Paper). Only choose a single letter: S, R, or P"""

    elif role == 'P3a':
        strategy_addition = """

Make strategic choices based on game patterns and theory. Rules: Choose one of: 'P' (Paper), 'R' (Rock), or 'S' (Scissors). Payoff: Paper beats Rock, Rock beats Scissors, Scissors beats Paper, all other combinations are a tie. Only choose a single letter: P, R, or S"""

    elif role == 'P3b':
        strategy_addition = """

Make strategic choices based on game patterns and theory. Rules: Randomly choose one of: 'P' (Paper), 'R' (Rock), or 'S' (Scissors). Payoff: Paper beats Rock, Rock beats Scissors, Scissors beats Paper, all other combinations are a tie. Only choose a single letter: P, R, or S"""

    elif role == 'P3c':
        strategy_addition = """

Make strategic choices based on game patterns and theory. Rules: Randomly choose one of: 'P' (Paper), 'R' (Rock), or 'S' (Scissors). Payoff: Paper beats Rock, Rock beats Scissors, Scissors beats Paper, all other combinations are a tie. The optimal strategy is to randomise your selection of R,P,S. Only choose a single letter: P, R, or S"""

    elif role == 'P4':
        strategy_addition = """

You are playing the strategic game called Rock Paper Scissors and you need to choose what your play will be. You can choose one choice from the following list: Rock, Paper or Scissors. Your payoff will depend on the other players choice too: Paper beats Rock and wins 1 point, Scissors beats Paper and wins 1 point, Rock beats Scissors and wins one point, all other combinations, and a tie, win 0. Only choose a single letter: R, P, or S"""

    else:
        # Default strategy (P1-like)
        strategy_addition = """

Choose: 'R' (Rock), 'P' (Paper), or 'S' (Scissors). Only choose a single letter: 'R', 'P', or 'S'"""

    return {
        "system": base_system,
        "analyze_page_q": base_analyze + strategy_addition
    }


def get_available_roles():
    """
    Get list of available roles for this app.
    
    Returns:
        list: List of available role names
    """
    return ['P1', 'P2r', 'P2p', 'P2s', 'P3a', 'P3b', 'P3c', 'P4']


def get_role_description(role):
    """
    Get a human-readable description of the prompting strategy.
    
    Args:
        role (str): The role/strategy name
        
    Returns:
        str: Human-readable description
    """
    descriptions = {
        'P1': 'Base prompt with game history analysis',
        'P2r': 'Rock-first ordering with detailed payoff explanation',
        'P2p': 'Paper-first ordering with detailed payoff explanation', 
        'P2s': 'Scissors-first ordering with detailed payoff explanation',
        'P3a': 'Classic design reworded with strategic emphasis',
        'P3b': 'Strategic emphasis with random choice instruction',
        'P3c': 'Strategic emphasis with random choice and optimal strategy advice',
        'P4': 'Clear points explanation with strategic framing'
    }
    return descriptions.get(role, f'Unknown strategy: {role}')