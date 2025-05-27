#!/usr/bin/env python3
"""
run.py - Main script for running Social Influence Task experiments

This script orchestrates the entire experiment workflow by using:
- cli.py for argument parsing and configuration management
- experiment.py for actual experiment execution

Usage:
    python run.py --sessions 1 --max-tokens 2048
    python run.py --sessions 3 --model-mapping custom_players.csv --q-role patient
    python run.py --validate-only
    python run.py --dry-run
"""
# Import the instructor patch for Groq models
# import groq_instructor_patch

# Import the DeepSeek patch
# import deepseek_patch

import sys
import os
import logging
from concurrent.futures import ThreadPoolExecutor

# Import configuration and CLI functions
from cli import (
    parse_arguments,
    load_model_mapping,
    get_available_models,
    validate_player_models
)

# Import experiment execution functions
from experiment import run_session

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("sit_runner")


def validate_environment():
    """Validate that required dependencies are available"""
    try:
        import botex
        logger.info("✓ botex package is available")
        return True
    except ImportError:
        logger.error("✗ botex package not found. Install with: pip install botex")
        return False


def display_configuration_summary(args, player_models, human_participants, bot_participants):
    """Display a comprehensive configuration summary"""
    unique_models = set(model for model in player_models.values() if model.lower() != 'human')
    
    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           EXPERIMENT CONFIGURATION                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Model mapping file: {args.model_mapping:<56} ║
║ Total participants: {args.participants:<56} ║
║ Human participants: {human_participants:<56} ║
║ Bot participants:   {bot_participants:<56} ║
║ Sessions to run:    {args.sessions:<56} ║
║ Questionnaire role: {args.q_role:<56} ║
║ Max tokens:         {args.max_tokens:<56} ║
║ Temperature:        {args.temperature:<56} ║
║ Output directory:   {args.output_dir:<56} ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    if unique_models:
        print("Models in use:")
        for model in sorted(unique_models):
            print(f"  • {model}")
    else:
        print("Models in use: None (humans only)")
    
    print()


def display_participant_assignments(player_models, available_models):
    """Display detailed participant assignments"""
    print("Participant Assignments:")
    print("-" * 50)
    
    for player_id in sorted(player_models.keys()):
        model_name = player_models[player_id]
        if model_name.lower() == "human":
            print(f"  Player {player_id}: HUMAN")
        else:
            if model_name in available_models:
                provider = available_models[model_name]['provider']
                print(f"  Player {player_id}: {model_name} ({provider})")
            else:
                print(f"  Player {player_id}: {model_name} (UNKNOWN PROVIDER)")


def handle_dry_run(args, player_models, available_models):
    """Handle dry run mode"""
    print("\n" + "="*60)
    print("                    DRY RUN MODE")
    print("="*60)
    
    display_participant_assignments(player_models, available_models)
    
    print(f"\nExperiment would run with:")
    print(f"  • {args.sessions} session(s)")
    print(f"  • {args.participants} participants per session")
    print(f"  • Output directory: {args.output_dir}")
    print(f"  • oTree URL: {args.otree_url}")
    
    if hasattr(args, 'experiment_name') and args.experiment_name:
        print(f"  • Experiment name: {args.experiment_name}")
    
    if hasattr(args, 'notes') and args.notes:
        print(f"  • Notes: {args.notes}")
    
    print(f"\nTo execute this configuration, run without --dry-run")
    return True


def handle_validation_only(args, player_models, available_models):
    """Handle validation-only mode"""
    print("\n" + "="*60)
    print("                 VALIDATION MODE")
    print("="*60)
    
    checks_passed = 0
    total_checks = 5
    
    # Check 1: Model mapping file exists and is valid
    print("1. Model mapping file validation...")
    if player_models:
        print("   ✓ Model mapping file loaded successfully")
        checks_passed += 1
    else:
        print("   ✗ Model mapping file validation failed")
    
    # Check 2: All models are available
    print("2. Model availability check...")
    is_valid, error_msg = validate_player_models(player_models, available_models)
    if is_valid:
        print("   ✓ All assigned models are available")
        checks_passed += 1
    else:
        print(f"   ✗ Model validation failed: {error_msg}")
    
    # Check 3: Environment configuration
    print("3. Environment configuration check...")
    config_issues = []
    
    # Check for required API keys based on models used
    unique_models = set(model for model in player_models.values() if model.lower() != 'human')
    for model_name in unique_models:
        if model_name in available_models:
            model_info = available_models[model_name]
            if model_info['api_key_env']:
                api_key = os.environ.get(model_info['api_key_env'])
                if not api_key:
                    config_issues.append(f"Missing API key: {model_info['api_key_env']}")
    
    if not config_issues:
        print("   ✓ Environment configuration is valid")
        checks_passed += 1
    else:
        print("   ✗ Environment configuration issues:")
        for issue in config_issues:
            print(f"     - {issue}")
    
    # Check 4: Output directory permissions
    print("4. Output directory check...")
    try:
        os.makedirs(args.output_dir, exist_ok=True)
        test_file = os.path.join(args.output_dir, ".test_write")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print("   ✓ Output directory is writable")
        checks_passed += 1
    except Exception as e:
        print(f"   ✗ Output directory issue: {str(e)}")
    
    # Check 5: Dependencies
    print("5. Dependencies check...")
    if validate_environment():
        checks_passed += 1
    
    print(f"\nValidation Summary: {checks_passed}/{total_checks} checks passed")
    
    if checks_passed == total_checks:
        print("✓ All validation checks passed! Ready to run experiments.")
        return True
    else:
        print("✗ Some validation checks failed. Please fix the issues above.")
        return False


def run_multiple_sessions(args, player_models, is_human_list, available_models):
    """Run multiple sessions concurrently"""
    print(f"\nStarting {args.sessions} concurrent sessions...")
    
    with ThreadPoolExecutor(max_workers=args.sessions) as executor:
        futures = [
            executor.submit(run_session, args, i+1, player_models, is_human_list, available_models) 
            for i in range(args.sessions)
        ]
        
        # Wait for all sessions to complete
        results = []
        for i, future in enumerate(futures, 1):
            try:
                result = future.result()
                results.append(result)
                if result["success"]:
                    print(f"✓ Session {i} completed successfully: {result['session_id']}")
                else:
                    print(f"✗ Session {i} failed: {result.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"✗ Session {i} failed with exception: {str(e)}")
                results.append({"success": False, "error": str(e)})
        
        # Print final summary
        successes = sum(1 for r in results if r.get("success", False))
        print(f"\n" + "="*60)
        print(f"EXPERIMENT COMPLETED: {successes}/{args.sessions} sessions successful")
        print("="*60)
        
        if successes > 0:
            print("✓ Successful sessions:")
            for i, result in enumerate(results, 1):
                if result.get("success", False):
                    print(f"  Session {i}: {result['session_id']}")
                    print(f"    Output: {result['output_dir']}")
        
        if successes < args.sessions:
            print("✗ Failed sessions:")
            for i, result in enumerate(results, 1):
                if not result.get("success", False):
                    print(f"  Session {i}: {result.get('error', 'Unknown error')}")
        
        return successes > 0


def main():
    """Main function to orchestrate the entire experiment workflow"""
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      SOCIAL INFLUENCE TASK EXPERIMENT                       ║
║                           with LLM Bots (botex)                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    # Parse command line arguments
    try:
        args = parse_arguments()
    except SystemExit as e:
        # Handle help or argument errors gracefully
        sys.exit(e.code)
    
    # Set up logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("Verbose logging enabled")
    
    # Validate environment and dependencies
    if not validate_environment():
        print("\nPlease install required dependencies and try again.")
        sys.exit(1)
    
    # Load participant assignments from CSV - this is REQUIRED
    if not os.path.exists(args.model_mapping):
        logger.error(f"Model mapping file not found: {args.model_mapping}")
        print(f"""
ERROR: Model mapping file '{args.model_mapping}' not found.

Please create a CSV file with the following format:
player_id,model_name
1,human
2,gemini-1.5-flash
3,claude-3-haiku

Available models: human, gemini-1.5-flash, gemini-1.5-pro, gpt-4o-mini, gpt-4o, 
                 claude-3-haiku, claude-3-sonnet, claude-3-opus, tinyllama
""")
        sys.exit(1)
    
    # Load model mapping
    logger.info(f"Loading participant assignments from: {args.model_mapping}")
    player_models, is_human_list, total_participants = load_model_mapping(args.model_mapping)
    
    if player_models is None:
        logger.error("Failed to load participant assignments")
        sys.exit(1)
    
    # Calculate derived values
    human_participants = sum(1 for is_human in is_human_list if is_human)
    bot_participants = total_participants - human_participants
    
    # Override args with values from CSV
    args.participants = total_participants
    args.humans = human_participants
    
    # Load available models from environment
    available_models = get_available_models()
    logger.info(f"Available models: {list(available_models.keys())}")
    
    # Validate the player model assignments
    is_valid, error_msg = validate_player_models(player_models, available_models)
    
    if not is_valid:
        logger.error(error_msg)
        print(f"\nERROR: {error_msg}")
        print("Please correct the model mapping file and try again.")
        sys.exit(1)
    
    # Display configuration summary
    display_configuration_summary(args, player_models, human_participants, bot_participants)
    
    # Handle special modes
    if hasattr(args, 'dry_run') and args.dry_run:
        handle_dry_run(args, player_models, available_models)
        return
    
    if hasattr(args, 'validate_only') and args.validate_only:
        success = handle_validation_only(args, player_models, available_models)
        sys.exit(0 if success else 1)
    
    # Create output directory
    try:
        os.makedirs(args.output_dir, exist_ok=True)
        logger.info(f"Output directory created/verified: {args.output_dir}")
    except Exception as e:
        logger.error(f"Failed to create output directory: {str(e)}")
        sys.exit(1)
    
    # Display participant assignments for verification
    if bot_participants > 0:
        display_participant_assignments(player_models, available_models)
    
    # Start the experiment
    try:
        # Import botex here to ensure environment variables are loaded
        import botex
        logger.info("Starting oTree server...")
        
        # Start oTree server
        otree_process = botex.start_otree_server(project_path=".", timeout=15)
        logger.info(f"✓ oTree server started at {args.otree_url}")
        
        try:
            # Run sessions
            if args.sessions == 1:
                # Run a single session
                print(f"\nStarting single experimental session...")
                result = run_session(args, 1, player_models, is_human_list, available_models)
                
                if result["success"]:
                    print(f"\n✓ Session completed successfully!")
                    print(f"  Session ID: {result['session_id']}")
                    print(f"  Output directory: {result['output_dir']}")
                else:
                    print(f"\n✗ Session failed: {result.get('error', 'Unknown error')}")
                    sys.exit(1)
            else:
                # Run multiple sessions
                success = run_multiple_sessions(args, player_models, is_human_list, available_models)
                if not success:
                    sys.exit(1)
        
        finally:
            # Always stop oTree server
            logger.info("Stopping oTree server...")
            botex.stop_otree_server(otree_process)
            logger.info("✓ oTree server stopped")
    
    except KeyboardInterrupt:
        print("\n\nExperiment interrupted by user")
        logger.info("Experiment interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during experiment: {str(e)}", exc_info=True)
        print(f"\nUnexpected error: {str(e)}")
        sys.exit(1)
    
    print(f"\n✓ Experiment completed successfully!")
    print(f"Results saved to: {args.output_dir}")


if __name__ == "__main__":
    main()