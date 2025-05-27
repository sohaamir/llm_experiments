#!/usr/bin/env python3
"""
experiment.py - Multi-app experiment execution

This module contains all the logic for running individual experimental sessions
with app-specific configurations, prompting strategies, and per-player role assignments.
"""

import datetime
import logging
import os
import platform
import subprocess
import time
import webbrowser
import csv
import requests
import botex
import litellm
import importlib.util
from pathlib import Path

logger = logging.getLogger("multi_app_experiment")


def load_app_prompts(app_name, role=None):
    """
    Load app-specific prompts from the app's prompts.py file.
    Works with any app by trying standard function naming conventions.
    
    Args:
        app_name (str): Name of the app
        role (str): Role for prompting strategy (app-specific, can be None)
    
    Returns:
        dict: Prompts dictionary for botex, or None if no prompts can be loaded
    """
    app_dir = Path(app_name)
    prompts_file = app_dir / "prompts.py"
    
    if not prompts_file.exists():
        logger.error(f"App-specific prompts file not found: {prompts_file}")
        return None
    
    try:
        # Load the prompts module dynamically
        spec = importlib.util.spec_from_file_location(f"{app_name}_prompts", prompts_file)
        prompts_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(prompts_module)
        
        prompts = None
        
        # Strategy 1: Try standard generic function names (most flexible)
        if hasattr(prompts_module, 'get_prompts'):
            try:
                prompts = prompts_module.get_prompts(role)
                logger.info(f"Loaded prompts using get_prompts() for app '{app_name}' with role '{role or 'default'}'")
            except Exception as e:
                logger.warning(f"get_prompts() failed for role '{role}': {e}")
                # Try without role
                try:
                    prompts = prompts_module.get_prompts(None)
                    logger.info(f"Loaded default prompts using get_prompts() for app '{app_name}'")
                except Exception as e2:
                    logger.warning(f"get_prompts() failed for default: {e2}")
        
        # Strategy 2: Try app-specific function names by convention
        if prompts is None:
            # Try function named after the app: get_{app_name}_prompts
            app_function_name = f"get_{app_name}_prompts"
            if hasattr(prompts_module, app_function_name):
                try:
                    app_function = getattr(prompts_module, app_function_name)
                    prompts = app_function(role)
                    logger.info(f"Loaded prompts using {app_function_name}() for app '{app_name}' with role '{role or 'default'}'")
                except Exception as e:
                    logger.warning(f"{app_function_name}() failed for role '{role}': {e}")
                    # Try without role
                    try:
                        prompts = app_function(None)
                        logger.info(f"Loaded default prompts using {app_function_name}() for app '{app_name}'")
                    except Exception as e2:
                        logger.warning(f"{app_function_name}() failed for default: {e2}")
        
        # Strategy 3: Try common app-specific function names (for backwards compatibility)
        if prompts is None:
            app_specific_functions = [
                'get_rps_prompts',        # For RPS variants
                'get_rps_repeat_prompts', # For RPS repeat variants
                'get_app_prompts',        # Generic alternative
                'get_bot_prompts',        # Another common name
            ]
            
            for func_name in app_specific_functions:
                if hasattr(prompts_module, func_name):
                    try:
                        func = getattr(prompts_module, func_name)
                        prompts = func(role)
                        logger.info(f"Loaded prompts using {func_name}() for app '{app_name}' with role '{role or 'default'}'")
                        break
                    except Exception as e:
                        logger.warning(f"{func_name}() failed for role '{role}': {e}")
                        # Try without role
                        try:
                            prompts = func(None)
                            logger.info(f"Loaded default prompts using {func_name}() for app '{app_name}'")
                            break
                        except Exception as e2:
                            logger.warning(f"{func_name}() failed for default: {e2}")
        
        # Strategy 4: If we have a role but no prompts, try again without role
        if prompts is None and role is not None:
            logger.warning(f"Role '{role}' not found for app '{app_name}', trying without role")
            return load_app_prompts(app_name, None)  # Recursive call without role
        
        if prompts is not None:
            return prompts
        else:
            logger.error(f"No suitable prompts function found in {prompts_file}")
            return None
            
    except Exception as e:
        logger.error(f"Error loading app prompts: {str(e)}")
        return None


def get_available_app_roles(app_name):
    """
    Get list of available roles for an app by checking its prompts.py file.
    Now works with any app using standard conventions.
    
    Args:
        app_name (str): Name of the app
        
    Returns:
        list: List of available role names, empty if none found
    """
    app_dir = Path(app_name)
    prompts_file = app_dir / "prompts.py"
    
    if not prompts_file.exists():
        return []
    
    try:
        # Load the prompts module dynamically
        spec = importlib.util.spec_from_file_location(f"{app_name}_prompts", prompts_file)
        prompts_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(prompts_module)
        
        available_roles = []
        
        # Strategy 1: Check for get_available_roles() function
        if hasattr(prompts_module, 'get_available_roles'):
            try:
                available_roles = prompts_module.get_available_roles()
                return available_roles
            except Exception as e:
                logger.warning(f"get_available_roles() failed: {e}")
        
        # Strategy 2: Check for role description functions
        role_desc_functions = [
            'get_role_description',
            'get_strategy_description',
            f'get_{app_name}_roles'
        ]
        
        for func_name in role_desc_functions:
            if hasattr(prompts_module, func_name):
                # This indicates the app has roles, but we can't automatically determine them
                # Return empty list but log that roles exist
                logger.info(f"App '{app_name}' has role descriptions ({func_name}) but roles must be determined from documentation")
                break
        
        # Strategy 3: For specific known apps (backwards compatibility)
        if app_name.startswith('rps') and not app_name.startswith('rps_repeat'):
            # Single RPS variants
            available_roles = ['P1', 'P2r', 'P2p', 'P2s', 'P3a', 'P3b', 'P3c', 'P4']
        elif app_name.startswith('rps_repeat'):
            # Multi-round RPS variants
            available_roles = ['non_thinker', 'thinker']
        
        return available_roles
        
    except Exception as e:
        logger.warning(f"Could not determine available roles for {app_name}: {str(e)}")
        return []


def configure_tinyllama_params(args, user_prompts):
    """Configure parameters for TinyLLaMA bots to be used with run_bots_on_session"""
    
    # Add explicit brevity instructions to all prompts
    modified_prompts = {}
    for key, value in user_prompts.items():
        if isinstance(value, str):
            modified_prompts[key] = value + "\n\nIMPORTANT: Your responses must be extremely brief and concise."
    
    # Make sure temperature is high enough to avoid repetition
    temperature = max(args.temperature, 0.8)
    
    # Enforce low max tokens
    max_tokens = min(args.max_tokens, 256)
    
    # Define additional parameters for llamacpp
    additional_params = {
        'temperature': temperature,
        'max_tokens': max_tokens,
        'repetition_penalty': 1.1
    }
    
    return modified_prompts, additional_params


def export_ordered_response_data(csv_file, botex_db, session_id):
    """Export botex response data with comprehension questions at the top and specific ordering"""
    try:
        # Use botex's built-in function to get the raw responses
        responses = botex.read_responses_from_botex_db(botex_db=botex_db, session_id=session_id)
        
        if not responses:
            logger.warning(f"No responses found for session {session_id}")
            with open(csv_file, 'w', newline='') as f:
                f.write("session_id,participant_id,round,question_id,answer,reason\n")
                f.write(f"# No responses found for session {session_id}\n")
            return
            
        logger.info(f"Found {len(responses)} responses for session {session_id}")
        
        # Sort responses by round and participant
        ordered_responses = sorted(responses, key=lambda x: (int(x['round']), x['participant_id'], x['question_id']))
        
        # Write to CSV with the correct order
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['session_id', 'participant_id', 'round', 'question_id', 'answer', 'reason'])
            writer.writeheader()
            writer.writerows(ordered_responses)
            logger.info(f"Successfully wrote {len(ordered_responses)} responses to {csv_file}")
            
    except Exception as e:
        logger.error(f"Error in export_ordered_response_data: {str(e)}")
        
        # Fallback to standard export
        try:
            logger.info(f"Trying standard botex export function...")
            botex.export_response_data(
                csv_file,
                botex_db=botex_db,
                session_id=session_id
            )
            logger.info(f"Standard export successful")
        except Exception as e2:
            logger.warning(f"Standard export also failed: {str(e2)}")
            with open(csv_file, 'w', newline='') as f:
                f.write("session_id,participant_id,round,question_id,answer,reason\n")
                f.write(f"# Error exporting responses: {str(e)}\n")


def open_chrome_browser(url, max_attempts=5):
    """Open the specified URL in a browser with retry logic"""
    
    for attempt in range(max_attempts):
        try:
            # macOS-specific approach for Chrome
            if platform.system() == 'Darwin':
                try:
                    # Try to use Google Chrome specifically
                    subprocess.run(['open', '-a', 'Google Chrome', url], check=True)
                    logger.info(f"Opened Chrome with URL: {url}")
                    return True
                except subprocess.CalledProcessError:
                    # Fall back to default browser if Chrome isn't available
                    webbrowser.open(url)
                    logger.info(f"Opened default browser with URL: {url}")
                    return True
            else:
                # For other platforms use the webbrowser module
                webbrowser.open(url)
                logger.info(f"Opened browser with URL: {url}")
                return True
                
        except Exception as e:
            logger.warning(f"Browser opening attempt {attempt+1}/{max_attempts} failed: {str(e)}")
            if attempt < max_attempts - 1:
                time.sleep(1)  # Wait before retrying
    
    logger.error(f"Failed to open browser after {max_attempts} attempts")
    return False


def run_session(args, session_number, player_models, player_roles, is_human_list, available_models):
    """Run a single experimental session using app-specific configuration with per-player roles"""
    try:
        # Create timestamp for this session
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"session_{session_number}_{timestamp}"
        
        # Calculate derived values
        n_humans_actual = sum(1 for is_human in is_human_list if is_human)
        n_bots = len(is_human_list) - n_humans_actual
        
        # Create session-specific output directory
        app_suffix = f"_{args.app}"
        roles_used = set(player_roles.values()) if player_roles else set()
        roles_suffix = f"_roles{'_'.join(sorted(roles_used))}" if roles_used else ""
        model_suffix = f"{app_suffix}{roles_suffix}_nhumans{n_humans_actual}_nbots{n_bots}"
        
        output_dir = os.path.join(args.output_dir, f"session_{session_id}{model_suffix}")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create session-specific database file
        botex_db = os.path.join(output_dir, f"botex_{session_id}{model_suffix}.sqlite3")
        
        logger.info(f"Session {session_number}: Output directory: {output_dir}")
        
        # Get available roles for this app
        available_app_roles = get_available_app_roles(args.app)
        logger.info(f"Session {session_number}: Available roles for app '{args.app}': {available_app_roles}")
        
        # Validate player roles
        invalid_roles = []
        if player_roles:
            for player_id, role in player_roles.items():
                if available_app_roles and role not in available_app_roles:
                    invalid_roles.append((player_id, role))
        
        if invalid_roles:
            logger.warning(f"Session {session_number}: Invalid roles found: {invalid_roles}")
            logger.warning(f"Session {session_number}: These players will use default prompts")
        
        # Pre-calculate model assignments for session config
        initial_session_config_fields = {}
        if player_models:
            for player_id, model_name in player_models.items():
                initial_session_config_fields[f'player_{player_id}_intended_model'] = model_name
                
                # Store role information if available
                if player_id in player_roles:
                    initial_session_config_fields[f'player_{player_id}_role'] = player_roles[player_id]
                
                # If this player is explicitly a bot, store the bot assignment
                if is_human_list and player_id <= len(is_human_list) and not is_human_list[player_id - 1]:
                    initial_session_config_fields[f'bot_position_{player_id}_model'] = model_name
                    if player_id in player_roles:
                        initial_session_config_fields[f'bot_position_{player_id}_role'] = player_roles[player_id]

        # Initialize session with explicit assignment
        session = botex.init_otree_session(
            config_name=args.app,  # Use app name as session config
            npart=len(is_human_list),
            is_human=is_human_list,
            botex_db=botex_db,
            otree_server_url=args.otree_url,
            otree_rest_key=getattr(args, 'otree_rest_key', None),
            modified_session_config_fields=initial_session_config_fields
        )

        # Get the session ID
        otree_session_id = session['session_id']
        logger.info(f"Session {session_number}: Initialized oTree session with ID: {otree_session_id}")

        # Log the explicit assignments for verification
        if player_models:
            for i, is_human in enumerate(session['is_human']):
                player_position = i + 1
                participant_code = session['participant_code'][i]
                if is_human:
                    role_info = f" (role: {player_roles.get(player_position, 'none')})" if player_position in player_roles else ""
                    logger.info(f"Session {session_number}: Player {player_position} (participant {participant_code}) -> HUMAN{role_info}")
                else:
                    if player_position in player_models:
                        assigned_model = player_models[player_position]
                        role_info = f" (role: {player_roles.get(player_position, 'default')})" if player_position in player_roles else " (role: default)"
                        logger.info(f"Session {session_number}: Player {player_position} (participant {participant_code}) -> {assigned_model}{role_info}")

        # Get the monitor URL and open browser
        monitor_url = f"{args.otree_url}/SessionMonitor/{otree_session_id}"
        logger.info(f"Session {session_number}: Monitor URL: {monitor_url}")
        
        # Display session info
        if session['human_urls']:
            print(f"\nSession {session_number}: Human participant URLs:")
            for i, url in enumerate(session['human_urls'], 1):
                # Find the player position for this human
                human_count = 0
                for j, is_human in enumerate(session['is_human']):
                    if is_human:
                        human_count += 1
                        if human_count == i:
                            player_position = j + 1
                            role_info = f" (role: {player_roles.get(player_position, 'none')})" if player_position in player_roles else ""
                            print(f"  Player {player_position}: {url}{role_info}")
                            break
        
        if session['bot_urls']:
            role_summary = f" with per-player roles" if player_roles else ""
            print(f"\nSession {session_number}: Starting {len(session['bot_urls'])} bots for app '{args.app}'{role_summary}")
            
            # Show bot role assignments
            if player_roles:
                bot_count = 0
                for i, is_human in enumerate(session['is_human']):
                    if not is_human:
                        bot_count += 1
                        player_position = i + 1
                        if player_position in player_models:
                            model_name = player_models[player_position]
                            role = player_roles.get(player_position, 'default')
                            print(f"    Bot {bot_count} (Player {player_position}): {model_name} with role '{role}'")
        
        if n_bots == 0:
            print(f"\nSession {session_number}: All {len(is_human_list)} participants are human")
        
        print(f"Monitor progress at: {monitor_url}")
        
        # Automatically open Chrome with the monitor URL (unless disabled)
        if not getattr(args, 'no_browser', False):
            open_chrome_browser(monitor_url)
        
        # Run bots if there are any
        if session['bot_urls']:
            logger.info(f"Session {session_number}: Running bots with app-specific prompts and per-player roles")
            
            # Start llama.cpp server if any local models are used
            use_local_model = any(available_models[player_models[player_id]]['provider'] == 'local' 
                                  for player_id in range(1, len(is_human_list) + 1) 
                                  if player_id in player_models and not session['is_human'][player_id - 1])
            
            server_process = None
            if use_local_model:
                logger.info(f"Session {session_number}: Starting llama.cpp server for local models")
                server_url = getattr(args, 'server_url', None) or "http://localhost:8080"
                
                try:
                    response = requests.get(f"{server_url}/health", timeout=5)
                    if response.status_code != 200:
                        raise Exception("Server not running")
                    logger.info(f"Session {session_number}: llama.cpp server already running at {server_url}")
                except:
                    server_process = botex.start_llamacpp_server({
                        "server_path": getattr(args, 'server_path', None),
                        "local_llm_path": getattr(args, 'model_path', None),
                        "server_url": server_url,
                        "maximum_tokens_to_predict": args.max_tokens,
                        "temperature": args.temperature,
                    })
                    logger.info(f"Session {session_number}: llama.cpp server started")
            
            # Run bots individually with assigned models and roles
            bot_threads = []
            bot_idx = 0

            for i, is_human in enumerate(session['is_human']):
                if not is_human:
                    player_id = i + 1
                    url = session['bot_urls'][bot_idx]
                    bot_idx += 1
                    
                    if player_id in player_models:
                        model_name = player_models[player_id]
                        model_info = available_models[model_name]
                        player_role = player_roles.get(player_id, None)
                        
                        # Log bot assignment attempt
                        role_info = f" with role '{player_role}'" if player_role else " with default role"
                        logger.info(f"🔄 ATTEMPTING TO ASSIGN: Player {player_id} → {model_name}{role_info}")
                        
                        try:
                            api_key = None
                            if model_info['api_key_env']:
                                api_key = os.environ.get(model_info['api_key_env'])
                            
                            # Load player-specific prompts with better fallback logic
                            user_prompts = None
                            
                            # Try role-specific prompts first
                            if player_role:
                                user_prompts = load_app_prompts(args.app, player_role)
                                if user_prompts is None:
                                    logger.warning(f"Failed to load role-specific prompts for player {player_id} (role: {player_role}), trying default")
                            
                            # Fall back to default prompts if role-specific failed or no role assigned
                            if user_prompts is None:
                                user_prompts = load_app_prompts(args.app, None)
                            
                            # Final fallback - create basic prompts if all else fails
                            if user_prompts is None:
                                logger.warning(f"No app-specific prompts found for {args.app}, using basic prompts")
                                user_prompts = {
                                    "system": "You are participating in an experiment. Always respond in valid JSON format only.",
                                    "analyze_page_q": "Page content: {body}\nQuestions: {questions_json}\nRespond with valid JSON only."
                                }
                            
                            if model_info['provider'] == 'local':
                                modified_prompts, tinyllama_params = configure_tinyllama_params(args, user_prompts)
                                user_prompts = modified_prompts
                            
                            thread = botex.run_single_bot(
                                url=url,
                                session_id=otree_session_id,
                                participant_id=f"P{player_id}",
                                botex_db=botex_db,
                                model=model_info['full_name'],
                                api_key=api_key,
                                user_prompts=user_prompts,
                                temperature=args.temperature,
                                max_tokens=args.max_tokens,
                                throttle=not args.no_throttle,
                                wait=False
                            )
                            bot_threads.append(thread)
                            thread.start()
                            
                            logger.info(f"✅ BOT STARTED: Player {player_id} with {model_name}{role_info}")
                            
                        except Exception as e:
                            logger.error(f"❌ BOT ASSIGNMENT FAILED: Player {player_id} → {model_name}{role_info} - Error: {str(e)}")
                            # Continue with other bots even if this one fails
            
            # Wait for all bots to finish
            for thread in bot_threads:
                thread.join()
            
            # Clean up llama.cpp server if we started it
            if server_process is not None:
                logger.info(f"Session {session_number}: Stopping llama.cpp server")
                botex.stop_llamacpp_server(server_process)
            
            logger.info(f"Session {session_number}: Bots completed")
        
        # Wait for human participants if there are any
        if session['human_urls']:
            logger.info(f"Session {session_number}: Waiting for {len(session['human_urls'])} human participants to complete")
            
            print(f"\nWaiting for {len(session['human_urls'])} human participants to complete the experiment...")
            print(f"You can monitor progress at: {monitor_url}")
            print(f"Press Ctrl+C to stop early and export current data.\n")
            
            try:
                # Wait for human participants to complete
                while True:
                    try:
                        time.sleep(20)  # Check every 20 seconds
                        
                        # Get session status from oTree
                        session_data = botex.call_otree_api(
                            requests.get, 'sessions', otree_session_id,
                            otree_server_url=args.otree_url, 
                            otree_rest_key=getattr(args, 'otree_rest_key', None)
                        )
                        
                        participants = session_data.get('participants', [])
                        
                        # Count completed participants (both human and bot)
                        completed_count = 0
                        human_completed = 0
                        bot_completed = 0
                        
                        for i, p in enumerate(participants):
                            participant_code = p.get('code', 'unknown')
                            finished_flag = p.get('finished', False)
                            current_page = p.get('_current_page_name', 'unknown')
                            current_app = p.get('_current_app_name', 'unknown')
                            
                            # Determine if this participant is human or bot
                            is_human_participant = session['is_human'][i] if i < len(session['is_human']) else True
                            
                            if finished_flag:
                                completed_count += 1
                                if is_human_participant:
                                    human_completed += 1
                                    logger.info(f"  {participant_code} (HUMAN): COMPLETED")
                                else:
                                    bot_completed += 1
                                    logger.info(f"  {participant_code} (BOT): COMPLETED")
                            else:
                                if is_human_participant:
                                    logger.info(f"  {participant_code} (HUMAN): IN PROGRESS ({current_app}.{current_page})")
                                else:
                                    logger.info(f"  {participant_code} (BOT): IN PROGRESS ({current_app}.{current_page})")
                        
                        logger.info(f"Session {session_number}: {completed_count}/{len(participants)} participants completed "
                                   f"({human_completed} humans, {bot_completed} bots)")
                        
                        # Only proceed when ALL participants have finished
                        if completed_count >= len(participants) and len(participants) > 0:
                            logger.info(f"Session {session_number}: All participants completed!")
                            print(f"All participants have completed the experiment. Proceeding to data export...")
                            break
                            
                    except KeyboardInterrupt:
                        logger.info(f"Session {session_number}: Manual interruption - proceeding to data export")
                        print(f"Manual interruption. Exporting current data...")
                        break
                    except Exception as api_error:
                        logger.warning(f"Session {session_number}: Could not check session status: {str(api_error)}")
                        # Continue waiting
                        
            except Exception as e:
                logger.error(f"Session {session_number}: Error while waiting for completion: {str(e)}")
                print(f"Error while waiting. Proceeding to data export...")
        else:
            # All participants were bots and have already completed
            logger.info(f"Session {session_number}: All bot participants have completed")
        
        # Export data using botex standard functions
        logger.info(f"Session {session_number}: Exporting data...")
        
        # Export oTree data
        otree_wide_csv = os.path.join(output_dir, f"otree_{otree_session_id}_wide{model_suffix}.csv")
        try:
            botex.export_otree_data(
                otree_wide_csv,
                server_url=args.otree_url,
                admin_name='admin',
                admin_password=os.environ.get('OTREE_ADMIN_PASSWORD')
            )
            logger.info(f"Session {session_number}: oTree data exported")
        except Exception as e:
            logger.error(f"Session {session_number}: Failed to export oTree data: {str(e)}")
        
        # Normalize oTree data
        try:
            botex.normalize_otree_data(
                otree_wide_csv, 
                store_as_csv=True,
                data_exp_path=output_dir,
                exp_prefix=f"otree_{otree_session_id}{model_suffix}"
            )
            logger.info(f"Session {session_number}: oTree data normalized")
        except Exception as e:
            logger.warning(f"Session {session_number}: Data normalization warning: {str(e)}")
        
        # Export botex data
        if n_bots > 0:
            try:
                botex.export_participant_data(
                    os.path.join(output_dir, f"botex_{otree_session_id}_participants{model_suffix}.csv"),
                    botex_db=botex_db,
                    session_id=otree_session_id
                )
                logger.info(f"Session {session_number}: Botex participant data exported")
            except Exception as e:
                logger.warning(f"Session {session_number}: Could not export botex participant data: {str(e)}")
            
            try:
                export_ordered_response_data(
                    os.path.join(output_dir, f"botex_{otree_session_id}_responses{model_suffix}.csv"),
                    botex_db=botex_db,
                    session_id=otree_session_id
                )
                logger.info(f"Session {session_number}: Botex response data exported")
            except Exception as e:
                logger.warning(f"Session {session_number}: Error exporting botex responses: {str(e)}")
        
        # Create summary file
        summary_file = os.path.join(output_dir, f"experiment_summary_{otree_session_id}{model_suffix}.txt")
        with open(summary_file, 'w') as f:
            f.write(f"Multi-App Experiment Summary - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*70 + "\n\n")
            f.write(f"App: {args.app}\n")
            f.write(f"Session ID: {otree_session_id}\n")
            f.write(f"Session Number: {session_number}\n")
            f.write(f"Participants: {len(is_human_list)} total ({n_humans_actual} human, {n_bots} bots)\n\n")
            
            if session['human_urls']:
                f.write("Human participant URLs:\n")
                human_count = 0
                for i, is_human in enumerate(session['is_human']):
                    if is_human:
                        player_position = i + 1
                        role_info = f" (role: {player_roles.get(player_position, 'none')})" if player_position in player_roles else ""
                        f.write(f"  Player {player_position}: {session['human_urls'][human_count]}{role_info}\n")
                        human_count += 1
            
            if player_models and n_bots > 0:
                f.write("\nBot model and role assignments:\n")
                bot_idx = 0
                for i, is_human in enumerate(session['is_human']):
                    if not is_human:
                        player_id = i + 1
                        if player_id in player_models:
                            model_name = player_models[player_id]
                            provider = available_models[model_name]['provider']
                            role = player_roles.get(player_id, 'default')
                            f.write(f"  Player {player_id}: {model_name} ({provider}) with role '{role}'\n")
                        bot_idx += 1
        
        logger.info(f"Session {session_number}: Session completed successfully")
        return {"success": True, "session_id": otree_session_id, "output_dir": output_dir}
    
    except Exception as e:
        logger.error(f"Session {session_number}: Error: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}