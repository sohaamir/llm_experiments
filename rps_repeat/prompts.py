"""
App-specific prompting strategies for multi-round Rock Paper Scissors.
Uses the general framework convention with get_prompts() function.
"""

def get_prompts(role=None):
    """
    Get the appropriate prompts for the specified role in multi-round RPS.
    
    Args:
        role (str): Either 'non_thinker', 'thinker', or None for default
    
    Returns:
        dict: Dictionary containing the prompts for botex
    """
    
    # Base system prompt for multi-round RPS
    base_system = """You are participating in a multi-round Rock Paper Scissors experiment against another player. 
    You will play multiple rounds and your goal is to maximize your total points.
    Always respond in valid JSON format only."""
    
    # Base analyze prompt
    base_analyze = """You are playing multi-round Rock Paper Scissors against another player.

Game Rules:
- Rock (R) beats Scissors (S)
- Paper (P) beats Rock (R)  
- Scissors (S) beats Paper (P)
- Same choice = tie

Page content: {body}
Questions: {questions_json}

Respond with valid JSON only."""
    
    # Role-specific modifications
    if role == 'thinker':
        # Strategic thinking role
        role_addition = """
        
        STRATEGIC APPROACH:
        To perform well in Rock Paper Scissors, it is useful to predict what the other player might choose and counter that choice.
        
        Key strategic considerations:
        - Analyze your opponent's previous choices for patterns
        - Consider psychological factors (do they repeat choices? do they avoid repeating?)
        - Think about what they might expect you to do
        - Use your knowledge of human behavior and game theory
        
        Your goal is to outthink your opponent by predicting their next move and choosing the counter-move."""
        
        analyze_addition = """

STRATEGIC THINKING REQUIRED: To win, you should predict what your opponent will choose and select the move that beats it.

Analyze any previous rounds and your opponent's patterns. Think strategically about what they might choose next.
Use your strategic thinking to predict your opponent's next move and choose accordingly."""

    elif role == 'non_thinker':
        # Simple/natural play role
        role_addition = """
        
        NATURAL APPROACH:
        Play Rock Paper Scissors naturally as you normally would. Make choices that feel right to you without overthinking strategy.
        
        Simply choose Rock (R), Paper (P), or Scissors (S) as you would in a casual game.
        Don't worry about complex strategies - just play intuitively."""
        
        analyze_addition = """

Play naturally and intuitively. Choose Rock (R), Paper (P), or Scissors (S) as you would in a casual game.
Make your choice naturally without overthinking."""

    else:
        # Default - balanced approach (similar to non_thinker but neutral)
        role_addition = """
        
        BALANCED APPROACH:
        Play Rock Paper Scissors using your best judgment. Consider the game situation and make reasonable choices."""
        
        analyze_addition = """

Make your choice using your best judgment for this Rock Paper Scissors game."""

    return {
        "system": base_system + role_addition,
        "analyze_page_q": base_analyze + analyze_addition
    }


def get_available_roles():
    """
    Get list of available roles for this app.
    
    Returns:
        list: List of available role names
    """
    return ['non_thinker', 'thinker']


def get_role_description(role):
    """
    Get a human-readable description of the role.
    
    Args:
        role (str): The role name
        
    Returns:
        str: Human-readable description
    """
    descriptions = {
        'non_thinker': 'Natural play - choose intuitively without complex strategy',
        'thinker': 'Strategic play - analyze opponent patterns and predict their moves'
    }
    return descriptions.get(role, f'Unknown role: {role}')
