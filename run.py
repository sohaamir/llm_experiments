#!/usr/bin/env python3
"""
run.py - Main script for running multi-app experiments

This script orchestrates the experiment workflow, hosting oTree experiments using botex.
"""

import botex
import sys
import os
import logging
from concurrent.futures import ThreadPoolExecutor

# Import experiment and CLI functions
from experiment import *
from cli import *

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("multi_app_runner")


def validate_environment():
    """Validate that required dependencies are available"""
    try:
        import botex
        logger.info("✓ botex package is available")
        return True
    except ImportError:
        logger.error("✗ botex package not found. Install with: pip install botex")
        return False


def display_configuration_summary(args, player_models, player_roles, human_participants, bot_participants):
    """Display a comprehensive configuration summary"""
    unique_models = set(model for model in player_models.values() if model.lower() != 'human')
    unique_roles = set(player_roles.values()) if player_roles else set()
    
    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           EXPERIMENT CONFIGURATION                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ App:                {args.app:<56} ║
║ Total participants: {len(player_models):<56} ║
║ Human participants: {human_participants:<56} ║
║ Bot participants:   {bot_participants:<56} ║
║ Sessions to run:    {args.sessions:<56} ║
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
    
    if unique_roles:
        print(f"\nRoles assigned:")
        for role in sorted(unique_roles):
            players_with_role = [str(pid) for pid, prole in player_roles.items() if prole == role]
            print(f"  • {role}: players {', '.join(players_with_role)}")
    else:
        print("\nRoles assigned: None (default prompts only)")
    
    print()


def display_participant_assignments(player_models, player_roles, available_models):
    """Display detailed participant assignments"""
    print("Participant Assignments:")
    print("-" * 60)
    
    for player_id in sorted(player_models.keys()):
        model_name = player_models[player_id]
        role = player_roles.get(player_id, 'default') if player_roles else 'default'
        
        if model_name.lower() == "human":
            print(f"  Player {player_id}: HUMAN (role: {role})")
        else:
            if model_name in available_models:
                provider = available_models[model_name]['provider']
                print(f"  Player {player_id}: {model_name} ({provider}, role: {role})")
            else:
                print(f"  Player {player_id}: {model_name} (UNKNOWN PROVIDER, role: {role})")


def handle_dry_run(args, player_models, player_roles, available_models):
    """Handle dry run mode"""
    print("\n" + "="*60)
    print("DRY RUN MODE")
    print("="*60)
    
    display_participant_assignments(player_models, player_roles, available_models)
    
    print(f"\nExperiment would run with:")
    print(f"  • App: {args.app}")
    print(f"  • {args.sessions} session(s)")
    print(f"  • {len(player_models)} participants per session")
    print(f"  • Output directory: {args.output_dir}")
    print(f"  • oTree URL: {args.otree_url}")
    
    if player_roles:
        unique_roles = set(player_roles.values())
        print(f"  • Per-player roles: {', '.join(sorted(unique_roles))}")
    
    print(f"\nTo execute this configuration, run without --dry-run")
    return True


def handle_validation_only(args, player_models, player_roles, available_models):
    """Handle validation-only mode"""
    print("\n" + "="*60)
    print("                 VALIDATION MODE")
    print("="*60)
    
    checks_passed = 0
    total_checks = 6
    
    # Check 1: App configuration
    print("1. App configuration validation...")
    app_dir = os.path.join(args.app)
    required_files = ['__init__.py', 'player_models.csv', 'prompts.py']
    missing_files = [f for f in required_files if not os.path.exists(os.path.join(app_dir, f))]
    
    if not missing_files:
        print("   ✓ App configuration is complete")
        checks_passed += 1
    else:
        print(f"   ✗ Missing files in app '{args.app}': {', '.join(missing_files)}")
    
    # Check 2: Model mapping validation
    print("2. Model mapping validation...")
    if player_models:
        print("   ✓ Model mapping loaded successfully")
        checks_passed += 1
    else:
        print("   ✗ Model mapping validation failed")
    
    # Check 3: Role validation
    print("3. Role assignment validation...")
    if player_roles:
        from experiment import get_available_app_roles
        available_roles = get_available_app_roles(args.app)
        
        if available_roles:
            invalid_roles = [role for role in player_roles.values() if role not in available_roles]
            if not invalid_roles:
                print(f"   ✓ All assigned roles are valid for app '{args.app}'")
                checks_passed += 1
            else:
                print(f"   ✗ Invalid roles found: {invalid_roles}")
                print(f"     Valid roles for {args.app}: {available_roles}")
        else:
            print(f"   ⚠ Could not determine valid roles for app '{args.app}', but roles are assigned")
            checks_passed += 1  # Don't fail for this
    else:
        print("   ✓ No specific roles assigned - will use default prompts")
        checks_passed += 1
    
    # Check 4: All models are available
    print("4. Model availability check...")
    is_valid, error_msg = validate_player_models(player_models, available_models)
    if is_valid:
        print("   ✓ All assigned models are available")
        checks_passed += 1
    else:
        print(f"   ✗ Model validation failed: {error_msg}")
    
    # Check 5: Environment configuration
    print("5. Environment configuration check...")
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
    
    # Check 6: Output directory permissions
    print("6. Output directory check...")
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
    
    print(f"\nValidation Summary: {checks_passed}/{total_checks} checks passed")
    
    if checks_passed == total_checks:
        print("✓ All validation checks passed! Ready to run experiments.")
        return True
    else:
        print("✗ Some validation checks failed. Please fix the issues above.")
        return False


def run_multiple_sessions(args, player_models, player_roles, is_human_list, available_models):
    """Run multiple sessions concurrently"""
    print(f"\nStarting {args.sessions} concurrent sessions...")
    
    with ThreadPoolExecutor(max_workers=args.sessions) as executor:
        futures = [
            executor.submit(run_session, args, i+1, player_models, player_roles, is_human_list, available_models) 
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
║                           MULTI-APP EXPERIMENTS                             ║
║                     with Per-Player Roles (botex)                           ║
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
    
    # Load app-specific participant assignments from CSV (now with roles)
    logger.info(f"Loading participant assignments for app '{args.app}'")
    player_models, player_roles, is_human_list, total_participants = get_app_specific_model_mapping(args.app)
    
    if player_models is None:
        logger.error(f"Failed to load participant assignments for app '{args.app}'")
        print(f"""
ERROR: Could not load participant assignments for app '{args.app}'.

Please ensure the app has a valid player_models.csv file with format:
player_id,model_name,role
1,human,thinker
2,gemini-1.5-flash,non_thinker
3,claude-3-haiku,

Note: The 'role' column is optional. If provided, it assigns per-player roles.

Use --list-apps to see available apps.
""")
        sys.exit(1)
    
    # Calculate derived values
    human_participants = sum(1 for is_human in is_human_list if is_human)
    bot_participants = total_participants - human_participants
    
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
    display_configuration_summary(args, player_models, player_roles, human_participants, bot_participants)
    
    # Handle special modes
    if hasattr(args, 'dry_run') and args.dry_run:
        handle_dry_run(args, player_models, player_roles, available_models)
        return
    
    if hasattr(args, 'validate_only') and args.validate_only:
        success = handle_validation_only(args, player_models, player_roles, available_models)
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
        display_participant_assignments(player_models, player_roles, available_models)
    
    # Start the experiment
    try:
        # Import botex here to ensure environment variables are loaded
        logger.info("Starting oTree server...")
        
        # Start oTree server
        otree_process = botex.start_otree_server(project_path=".", timeout=15)
        logger.info(f"✓ oTree server started at {args.otree_url}")
        
        try:
            # Run sessions
            if args.sessions == 1:
                # Run a single session
                print(f"\nStarting single experimental session for app '{args.app}'...")
                result = run_session(args, 1, player_models, player_roles, is_human_list, available_models)
                
                if result["success"]:
                    print(f"\n✓ Session completed successfully!")
                    print(f"  Session ID: {result['session_id']}")
                    print(f"  Output directory: {result['output_dir']}")
                else:
                    print(f"\n✗ Session failed: {result.get('error', 'Unknown error')}")
                    sys.exit(1)
            else:
                # Run multiple sessions
                success = run_multiple_sessions(args, player_models, player_roles, is_human_list, available_models)
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