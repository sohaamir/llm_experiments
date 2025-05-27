#!/usr/bin/env python3
"""
cli.py - Command line interface and configuration for social influence task experiments

This module handles argument parsing, configuration validation, and orchestration
of experiment execution using the experiment.py module.
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
logger = logging.getLogger("sit_cli")

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
    google_models_str = os.environ.get('GOOGLE_MODELS', 'gemini-1.5-flash')  # Default fallback
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

    # In get_available_models() function, add:
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


def load_model_mapping(file_path):
    """
    Load player-model mapping from a CSV file.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        tuple: (player_models dict, is_human list, total_participants) or (None, None, 0) if file not found
    """
    if not os.path.exists(file_path):
        logger.error(f"Model mapping file not found at {file_path}")
        return None, None, 0
        
    player_models = {}
    participant_assignments = []
    
    try:
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                player_id = int(row['player_id'])
                model_name = row['model_name'].strip()
                
                participant_assignments.append((player_id, model_name))
                player_models[player_id] = model_name
        
        # Sort by player_id to ensure correct order
        participant_assignments.sort(key=lambda x: x[0])
        
        # Create the is_human boolean list
        is_human_list = [model_name.lower() == "human" for _, model_name in participant_assignments]
        
        total_participants = len(participant_assignments)
        
        logger.info(f"Loaded {total_participants} participant assignments from {file_path}")
        
        return player_models, is_human_list, total_participants
        
    except Exception as e:
        logger.error(f"Error loading model mapping: {str(e)}")
        return None, None, 0


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


def parse_arguments():
    """Parse command line arguments with comprehensive help and validation"""
    
    parser = argparse.ArgumentParser(
        description="""
Run Social Influence Task experiments with LLM bots using botex.

This script automatically loads participant and model assignments from a CSV file,
eliminating the need to specify models, participant counts, or human/bot ratios
via command line arguments.

Examples:
  # Run a single session with default settings
  python run.py --sessions 1
  
  # Run multiple sessions with custom token limit
  python run.py --sessions 3 -m 1024
  
  # Run with custom CSV file and specific questionnaire role
  python run.py --sessions 2 --model-mapping custom_players.csv -q patient
  
  # Validate configuration without running
  python run.py --validate-only
  
  # Run with detailed logging and custom output directory
  python run.py --sessions 1 --verbose --output-dir results/pilot_study
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # === ESSENTIAL ARGUMENTS ===
    parser.add_argument(
        "-s", "--sessions", 
        type=int, 
        default=1,
        help="""Number of concurrent experimental sessions to run.
        
        Each session creates an independent oTree session with participants as defined 
        in the model mapping CSV. Sessions run in parallel when > 1.
        
        Values: Any positive integer
        Default: 1
        Use cases:
          -s 1     # Single session for testing/piloting
          -s 5     # Multiple sessions for data collection
          -s 10    # Large-scale data collection
        """
    )

    parser.add_argument(
        "--model-mapping", 
        default="player_models.csv",
        help="""Path to CSV file defining participant-model assignments.
        
        CSV format: player_id,model_name
        - player_id: Integer position (1, 2, 3, ...)
        - model_name: Either 'human' or a model identifier
        
        Supported models:
          'human'                    # Human participant
          'gemini-1.5-flash'        # Google Gemini (fast)
          'gemini-1.5-pro'          # Google Gemini (advanced)
          'gpt-4o-mini'             # OpenAI GPT-4o Mini
          'gpt-4o'                  # OpenAI GPT-4o
          'claude-3-haiku'          # Anthropic Claude Haiku (fast)
          'claude-3-sonnet'         # Anthropic Claude Sonnet
          'claude-3-opus'           # Anthropic Claude Opus (advanced)
          'tinyllama'               # Local TinyLLaMA model
        
        Default: player_models.csv
        Use cases:
          --model-mapping pilot_study.csv      # Custom pilot configuration
          --model-mapping all_bots.csv         # Bot-only sessions
          --model-mapping mixed_models.csv     # Multi-model comparison
        """
    )

    # === CONFIGURATION FILES ===
    parser.add_argument(
        "-c", "--config", 
        default="botex.env",
        help="""Path to environment configuration file.
        
        Contains API keys, model settings, and oTree configuration.
        See botex.env.example for required variables.
        
        Default: botex.env
        Use cases:
          -c production.env    # Production API keys
          -c testing.env       # Testing/development setup
          -c local.env         # Local-only models
        """
    )

    # === OUTPUT CONTROL ===
    parser.add_argument(
        "-o", "--output-dir", 
        default="botex_data",
        help="""Directory for storing experiment output.
        
        Creates subdirectories for each session containing:
        - oTree data (wide and normalized CSV)
        - Botex conversation logs and responses
        - Experiment summary and metadata
        
        Default: botex_data
        Use cases:
          -o results/study1           # Organized by study
          -o /shared/experiments      # Shared storage
          -o output_$(date +%%Y%%m%%d)  # Date-stamped folders
        """
    )

    # === MODEL PARAMETERS ===
    parser.add_argument(
        "-m", "--max-tokens", 
        type=int, 
        default=None,
        help="""Maximum tokens for LLM responses.
        
        Higher values allow more detailed reasoning but increase costs.
        Some models have specific limits.
        
        Recommended values:
          256-512     # TinyLLaMA (local models)
          1024-2048   # Most API models (balanced)
          4096        # Complex reasoning tasks
        
        Default: Model-specific (from botex.env)
        Use cases:
          -m 512     # Cost-conscious experiments
          -m 2048    # Standard social tasks
          -m 4096    # Complex decision tasks
        """
    )

    parser.add_argument(
        "--temperature", 
        type=float, 
        default=None,
        help="""Model temperature for response randomness.
        
        Lower values = more consistent/predictable responses
        Higher values = more varied/creative responses
        
        Values: 0.0 to 2.0
          0.0-0.3   # Highly consistent responses
          0.5-0.8   # Balanced (recommended for social tasks)
          1.0-2.0   # High variability
        
        Default: 0.7
        Use cases:
          --temperature 0.1    # Reproducible responses
          --temperature 0.7    # Natural social behavior
          --temperature 1.2    # Explore response diversity
        """
    )

    # === EXPERIMENT DESIGN ===
    parser.add_argument(
        "-q", "--q-role", 
        default="none",
        choices=["none", "typical", "patient"],
        help="""Role assignment for questionnaire responses.
        
        Affects how bots respond to psychological questionnaires/scales.
        
        Options:
          'none'     # No specific role instructions
          'typical'  # Neurotypical/healthy individual responses
          'patient'  # Responses reflecting psychological difficulties
        
        Default: none
        Use cases:
          -q typical     # Healthy population simulation
          -q patient     # Clinical population simulation
          -q none        # Pure task behavior (no questionnaires)
        """
    )

    parser.add_argument(
        "--session-config", 
        default="social_influence_task",
        help="""oTree session configuration name.
        
        Must match a configuration defined in settings.py.
        Different configs can run different experimental variants.
        
        Default: social_influence_task
        Use cases:
          --session-config social_influence_task    # Standard version
          --session-config social_influence_short   # Shortened version
          --session-config pilot_version            # Pilot configuration
        """
    )

    # === TECHNICAL SETTINGS ===
    parser.add_argument(
        "--otree-url", 
        default="http://localhost:8000",
        help="""oTree server URL.
        
        Use localhost for local development, or specify remote server.
        Must be accessible from where bots are running.
        
        Default: http://localhost:8000
        Use cases:
          --otree-url http://localhost:8000        # Local development
          --otree-url https://myserver.com:8000    # Remote server
          --otree-url http://192.168.1.100:8000    # Network server
        """
    )

    parser.add_argument(
        "--botex-db", 
        default="botex.sqlite3",
        help="""Base name for botex SQLite database files.
        
        Actual files will be session-specific with timestamps.
        Stores LLM conversation logs and response data.
        
        Default: botex.sqlite3
        Use cases:
          --botex-db experiment1.sqlite3    # Experiment-specific naming
          --botex-db /data/botex.sqlite3     # Custom storage location
        """
    )

    parser.add_argument(
        "-x", "--no-throttle", 
        action="store_true",
        help="""Disable API request throttling.
        
        By default, botex throttles requests to avoid rate limits.
        Disabling may cause failures with free API tiers.
        
        Default: False (throttling enabled)
        Use cases:
          -x    # When using paid API tiers with high limits
        """
    )

    # === VALIDATION AND TESTING ===
    parser.add_argument(
        "--validate-only", 
        action="store_true",
        help="""Validate configuration without running experiments.
        
        Checks:
        - CSV file format and model availability
        - API keys and model access
        - oTree configuration
        - File permissions and paths
        
        Use cases:
          --validate-only    # Test setup before running
        """
    )

    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="""Show what would be executed without running.
        
        Displays:
        - Participant assignments from CSV
        - Model configurations
        - Session parameters
        - Output locations
        
        Use cases:
          --dry-run    # Preview experiment setup
        """
    )

    # === DEBUGGING AND MONITORING ===
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true",
        help="""Enable detailed logging output.
        
        Shows:
        - Bot conversation details
        - API request/response info
        - oTree session progress
        - Detailed error messages
        
        Default: False
        Use cases:
          -v    # Debugging experiments
          -v    # Monitoring long-running sessions
        """
    )

    parser.add_argument(
        "--no-browser", 
        action="store_true",
        help="""Disable automatic browser opening.
        
        By default, opens session monitor in browser automatically.
        Useful for headless/automated execution.
        
        Default: False (browser opens automatically)
        Use cases:
          --no-browser    # Server/automated execution
          --no-browser    # Multiple sessions (avoid browser spam)
        """
    )

    # === EXPERIMENTAL CONTROL ===
    parser.add_argument(
        "--wait-timeout", 
        type=int, 
        default=7200,  # 2 hours
        help="""Timeout in seconds for waiting for human participants.
        
        How long to wait for human participants to complete.
        Affects mixed human-bot sessions.
        
        Values: Time in seconds
          1800    # 30 minutes
          3600    # 1 hour  
          7200    # 2 hours (default)
          0       # No timeout (wait indefinitely)
        
        Default: 7200 (2 hours)
        Use cases:
          --wait-timeout 1800    # Quick pilot sessions
          --wait-timeout 0       # Flexible timing
        """
    )

    parser.add_argument(
        "--experiment-name", 
        default=None,
        help="""Custom name for this experiment run.
        
        Added to output files and summary reports.
        Useful for organizing multiple experiment variants.
        
        Use cases:
          --experiment-name pilot_study_v1    # Version tracking
          --experiment-name condition_A       # Experimental conditions
          --experiment-name replication_1     # Replication studies
        """
    )

    parser.add_argument(
        "--notes", 
        default="",
        help="""Additional notes about this experiment run.
        
        Added to experiment summary files.
        Useful for documenting experimental conditions or hypotheses.
        
        Use cases:
          --notes "Testing new prompt strategy"
          --notes "Baseline condition for comparison"
          --notes "Pilot run before main data collection"
        """
    )

    # === LOCAL MODEL SETTINGS ===
    local_group = parser.add_argument_group('Local Model Settings (TinyLLaMA)')
    
    local_group.add_argument(
        "--model-path", 
        default=None,
        help="""Path to local model file for TinyLLaMA.
        
        Only needed if using local models and not set in botex.env.
        Should point to a .gguf format model file.
        
        Use cases:
          --model-path models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
          --model-path /shared/models/custom_model.gguf
        """
    )

    local_group.add_argument(
        "--server-path", 
        default=None,
        help="""Path to llama.cpp server executable.
        
        Only needed if using local models and not set in botex.env.
        
        Use cases:
          --server-path ./llama_server
          --server-path /usr/local/bin/llama-server
        """
    )

    args = parser.parse_args()
    
    # Load environment configuration
    if os.path.exists(args.config):
        load_dotenv(args.config)
        logger.info(f"Loaded configuration from {args.config}")
    else:
        logger.warning(f"Configuration file {args.config} not found, using environment variables")

    # Set defaults from environment if not specified
    if args.max_tokens is None:
        args.max_tokens = int(os.environ.get("MAX_TOKENS_DEFAULT", "1024"))
    
    if args.temperature is None:
        args.temperature = 0.7
    
    # Set model paths from environment if not specified
    if args.model_path is None:
        args.model_path = os.environ.get("LLAMACPP_LOCAL_LLM_PATH")
    
    if args.server_path is None:
        args.server_path = os.environ.get("LLAMACPP_SERVER_PATH")

    return args