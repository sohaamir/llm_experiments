#!/usr/bin/env python3
"""
cli.py - Command line interface and configuration for LLM experiments

Author: [Aamir Sohail)
"""

import argparse
import datetime
import logging
import os
import sys
import csv
from pathlib import Path
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

# Load environment variables from botex.env
load_dotenv("botex.env")

# Import experiment execution functions
from experiment import run_session

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("multi_app_cli")

# Custom log filter to exclude noisy HTTP request logs
class LogFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        if "HTTP Request:" in message or "Throttling: Request error:" in message:
            return False
        return True

for handler in logging.getLogger().handlers:
    handler.addFilter(LogFilter())


def get_available_models():
    """
    Get all available models from environment variables.
    
    Returns:
        dict: Dictionary mapping model names to their full model strings and provider
    """
    available_models = {}
    
    # Gemini models
    google_models_str = os.environ.get('GOOGLE_MODELS', 'gemini-1.5-flash')
    google_models = [m.strip() for m in google_models_str.split(',') if m.strip()]
    for model in google_models:
        model_name = model.strip()
        available_models[model_name] = {
            'full_name': f"gemini/{model_name}", 
            'provider': 'gemini',
            'api_key_env': 'GOOGLE_API_KEY'
        }
    
    # OpenAI models
    openai_models_str = os.environ.get('OPENAI_MODELS', '')
    if openai_models_str:
        openai_models = [m.strip() for m in openai_models_str.split(',') if m.strip()]
        for model in openai_models:
            model_name = model.strip()
            available_models[model_name] = {
                'full_name': model_name,
                'provider': 'openai',
                'api_key_env': 'OPENAI_API_KEY'
            }
    
    # Anthropic models
    anthropic_models_str = os.environ.get('ANTHROPIC_MODELS', '')
    if anthropic_models_str:
        anthropic_models = [m.strip() for m in anthropic_models_str.split(',') if m.strip()]
        for model in anthropic_models:
            model_name = model.strip()
            available_models[model_name] = {
                'full_name': f"anthropic/{model_name}",
                'provider': 'anthropic',
                'api_key_env': 'ANTHROPIC_API_KEY'
            }

    # Groq models  
    groq_models_str = os.environ.get('GROQ_MODELS', '')
    if groq_models_str:
        groq_models = [m.strip() for m in groq_models_str.split(',') if m.strip()]
        for model in groq_models:
            model_name = model.strip()
            available_models[model_name] = {
                'full_name': f"groq/{model_name}",
                'provider': 'groq', 
                'api_key_env': 'GROQ_API_KEY'
            }

    # DeepSeek models
    deepseek_models_str = os.environ.get('DEEPSEEK_MODELS', '')
    if deepseek_models_str:
        deepseek_models = [m.strip() for m in deepseek_models_str.split(',') if m.strip()]
        for model in deepseek_models:
            model_name = model.strip()
            available_models[model_name] = {
                'full_name': f"deepseek/{model_name}",
                'provider': 'deepseek',
                'api_key_env': 'DEEPSEEK_API_KEY'
            }
    
    # Local models
    local_models_str = os.environ.get('LOCAL_LLM_MODELS', '')
    if local_models_str:
        local_models = [m.strip() for m in local_models_str.split(',') if m.strip()]
        for model in local_models:
            model_name = model.strip()
            available_models[model_name] = {
                'full_name': 'llamacpp',
                'provider': 'local',
                'api_key_env': None
            }
    
    return available_models


def get_app_specific_model_mapping(app_name):
    """
    Load app-specific player-model mapping with optional role assignments from CSV file.
    
    Args:
        app_name (str): Name of the app (e.g., 'rps', 'rps_repeat')
        
    Returns:
        tuple: (player_models dict, player_roles dict, is_human list, total_participants) or (None, None, None, 0) if file not found
    """
    app_dir = Path(app_name)
    file_path = app_dir / "player_models.csv"
    
    if not file_path.exists():
        logger.error(f"App-specific model mapping file not found at {file_path}")
        return None, None, None, 0
        
    player_models = {}
    player_roles = {}
    participant_assignments = []
    
    try:
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            
            # Check if role column exists
            has_role_column = 'role' in fieldnames
            
            for row in reader:
                player_id = int(row['player_id'])
                model_name = row['model_name'].strip()
                
                # Handle role assignment (optional column)
                role = None
                if has_role_column and row.get('role'):
                    role = row['role'].strip()
                    if role:  # Only assign if not empty
                        player_roles[player_id] = role
                
                participant_assignments.append((player_id, model_name))
                player_models[player_id] = model_name
        
        # Sort by player_id to ensure correct order
        participant_assignments.sort(key=lambda x: x[0])
        
        # Create the is_human boolean list
        is_human_list = [model_name.lower() == "human" for _, model_name in participant_assignments]
        
        total_participants = len(participant_assignments)
        
        logger.info(f"Loaded {total_participants} participant assignments from {file_path}")
        if player_roles:
            logger.info(f"Found role assignments for players: {list(player_roles.keys())}")
        
        return player_models, player_roles, is_human_list, total_participants
        
    except Exception as e:
        logger.error(f"Error loading model mapping: {str(e)}")
        return None, None, None, 0


def validate_player_models(player_models, available_models):
    """
    Validate that all player models are available.
    
    Args:
        player_models (dict): Mapping of player IDs to model names
        available_models (dict): Available models
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not player_models:
        return True, None
        
    for player_id, model_name in player_models.items():
        # Skip validation for human participants
        if model_name.lower() == "human":
            continue
            
        if model_name not in available_models:
            return False, f"Player {player_id} is assigned model '{model_name}' which is not available in botex.env"
    
    return True, None


def get_available_apps():
    """
    Get list of available oTree apps by checking for directories with __init__.py and player_models.csv
    
    Returns:
        list: List of available app names
    """
    available_apps = []
    current_dir = Path('.')
    
    for item in current_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.') and not item.name.startswith('_'):
            # Check if it's a valid oTree app (has __init__.py and player_models.csv)
            if (item / '__init__.py').exists() and (item / 'player_models.csv').exists():
                available_apps.append(item.name)
    
    return sorted(available_apps)


def parse_arguments():
    """Parse command line arguments with comprehensive help and validation"""
    
    parser = argparse.ArgumentParser(
        description="""
Run multi-app experiments with LLM bots using botex.

This method automatically detects available oTree apps and loads app-specific
participant, model, and role assignments from each app's player_models.csv file.

Player roles are now assigned per-participant in the CSV file:
  player_id,model_name,role
  1,human,thinker
  2,gemini-1.5-flash,non_thinker
  3,claude-3-haiku,

Examples:
  # List available apps
  <python run.py --list-apps>
  
  # Run single session with specific app
  <python run.py --app rps_repeat --sessions 1> or <python run.py -a rps_repeat -s 1>
  
  # Run multiple sessions with per-player role assignments
  <python run.py --app rps_repeat --sessions 3>
  
  # Validate app configuration
  <python run.py --app rps_repeat --validate-only>
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # === APP SELECTION ===
    parser.add_argument(
        "-a", "--app", 
        required=False,
        help="""Name of the oTree app to run.
        
        Each app must have:
        - __init__.py (oTree app definition)
        - player_models.csv (participant assignments with optional roles)
        - prompts.py (app-specific prompting strategies)
        
        Use --list-apps to see available apps.
        """
    )

    parser.add_argument(
        "--list-apps", 
        action="store_true",
        help="List all available oTree apps and exit"
    )

    # === ESSENTIAL ARGUMENTS ===
    parser.add_argument(
        "-s", "--sessions", 
        type=int, 
        default=1,
        help="Number of concurrent experimental sessions to run (default: 1)"
    )

    # === OUTPUT CONTROL ===
    parser.add_argument(
        "-o", "--output-dir", 
        default="botex_data",
        help="Directory for storing experiment output (default: botex_data)"
    )

    # === MODEL PARAMETERS ===
    parser.add_argument(
        "-mt", "--max-tokens", 
        type=int, 
        default=1024,
        help="Maximum tokens for LLM responses (default: 1024)"
    )

    parser.add_argument(
        "-t", "--temperature", 
        type=float, 
        default=0.7,
        help="Model temperature for response randomness (default: 0.7)"
    )

    # === TECHNICAL SETTINGS ===
    parser.add_argument(
        "--otree-url", 
        default="http://localhost:8000",
        help="oTree server URL (default: http://localhost:8000)"
    )

    parser.add_argument(
        "-x", "--no-throttle", 
        action="store_true",
        help="Disable API request throttling"
    )

    # === VALIDATION AND TESTING ===
    parser.add_argument(
        "--validate-only", 
        action="store_true",
        help="Validate app configuration without running experiments"
    )

    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Show what would be executed without running"
    )

    # === DEBUGGING ===
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true",
        help="Enable detailed logging output"
    )

    parser.add_argument(
        "--no-browser", 
        action="store_true",
        help="Disable automatic browser opening"
    )

    args = parser.parse_args()
    
    # Handle listing apps
    if args.list_apps:
        apps = get_available_apps()
        print("\nAvailable oTree Apps:")
        print("=" * 40)
        if apps:
            for app in apps:
                app_dir = Path(app)
                try:
                    # Try to get basic info about the app
                    model_file = app_dir / "player_models.csv"
                    if model_file.exists():
                        with open(model_file, 'r') as f:
                            reader = csv.DictReader(f)
                            participants = list(reader)
                            participant_count = len(participants)
                            
                            # Check for role assignments
                            has_roles = any('role' in row and row['role'].strip() for row in participants)
                            role_info = " (with roles)" if has_roles else ""
                            
                        print(f"  {app:<15} ({participant_count} participants{role_info})")
                    else:
                        print(f"  {app:<15} (configuration incomplete)")
                except:
                    print(f"  {app:<15} (configuration error)")
        else:
            print("  No apps found.")
            print("\n  To create an app, ensure it has:")
            print("  - __init__.py (oTree app definition)")
            print("  - player_models.csv (participant assignments)")
            print("  - prompts.py (prompting strategies)")
        print()
        sys.exit(0)
    
    # Validate app selection
    if not args.app:
        available_apps = get_available_apps()
        if not available_apps:
            print("ERROR: No apps found. Use --list-apps to see requirements.")
            sys.exit(1)
        
        print(f"ERROR: Must specify an app. Available apps: {', '.join(available_apps)}")
        print("Use --list-apps for more details.")
        sys.exit(1)
    
    # Validate selected app exists
    available_apps = get_available_apps()
    if args.app not in available_apps:
        print(f"ERROR: App '{args.app}' not found.")
        if available_apps:
            print(f"Available apps: {', '.join(available_apps)}")
        else:
            print("No apps found. Use --list-apps for requirements.")
        sys.exit(1)
    
    return args