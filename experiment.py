#!/usr/bin/env python3
"""
experiment.py - Multi-app experiment execution

This module contains all the logic for running individual experimental sessions
with app-specific configurations, prompting strategies, and per-player role assignments.
"""

from threading import Thread
from pathlib import Path
import datetime
import logging
import os
import re
import platform
import subprocess
import time
import webbrowser
import csv
import requests
import botex
import litellm
import sqlite3
import json
import importlib.util

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
            
    except Exception as e:
        logger.error(f"Error loading app prompts: {str(e)}")
        return None


def get_available_app_roles(app_name):
    """
    Get list of available roles for an app by checking its prompts.py file.
    
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


def export_response_data(csv_file, botex_db, session_id):
    """Export botex response data with proper round and question tracking"""
    try:
        # Connect to botex database
        conn = sqlite3.connect(botex_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get conversations for this session
        cursor.execute("SELECT * FROM conversations")
        conversations = [dict(row) for row in cursor.fetchall()]
        
        # Filter by session_id if provided
        if session_id:
            conversations = [
                c for c in conversations 
                if json.loads(c['bot_parms'])['session_id'] == session_id
            ]
        
        enhanced_responses = []
        
        for conversation in conversations:
            try:
                bot_parms = json.loads(conversation['bot_parms'])
                participant_id = conversation['id']
                
                # Parse the conversation messages
                messages = json.loads(conversation['conversation'])
                
                # Track rounds and questions more systematically
                current_round = 1
                questions_answered_in_round = 0
                previous_prompt = ""
                
                for i, message in enumerate(messages):
                    if message.get('role') == 'user':
                        # This is a prompt to the bot
                        current_prompt = message.get('content', '')
                        
                        # Detect round transitions by looking for round indicators in prompts
                        round_match = re.search(r'[Rr]ound\s*(\d+)', current_prompt)
                        if round_match:
                            detected_round = int(round_match.group(1))
                            if detected_round != current_round:
                                current_round = detected_round
                                questions_answered_in_round = 0
                        
                        previous_prompt = current_prompt
                    
                    elif message.get('role') == 'assistant':
                        # This is a bot response
                        try:
                            response_data = json.loads(message.get('content', '{}'))
                            
                            # Extract summary if available
                            summary = response_data.get('summary', '')
                            
                            # Extract answers
                            answers = response_data.get('answers', {})
                            
                            # If we have answers, process them
                            if answers:
                                # Check if this looks like a new round based on question patterns
                                # If we see questions that suggest round restart, increment round
                                question_ids = list(answers.keys())
                                
                                # Simple heuristic: if we've answered questions and now see 
                                # what looks like initial questions again, it might be a new round
                                initial_question_patterns = ['choice', 'decision', 'select', 'pick', 'vote']
                                looks_like_initial = any(pattern in str(qid).lower() for qid in question_ids 
                                                       for pattern in initial_question_patterns)
                                
                                if looks_like_initial and questions_answered_in_round > 2:
                                    current_round += 1
                                    questions_answered_in_round = 0
                                
                                for question_id, answer_data in answers.items():
                                    if question_id == 'round':
                                        continue
                                    
                                    enhanced_responses.append({
                                        'session_id': bot_parms.get('session_id', ''),
                                        'participant_id': participant_id,
                                        'round': current_round,
                                        'question_id': question_id,
                                        'answer': answer_data.get('answer', ''),
                                        'reason': answer_data.get('reason', ''),
                                        'summary': summary,
                                        'prompt': previous_prompt[:500] + '...' if len(previous_prompt) > 500 else previous_prompt
                                    })
                                    
                                    questions_answered_in_round += 1
                            
                        except json.JSONDecodeError:
                            # Skip malformed responses
                            continue
                            
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Error processing conversation {conversation.get('id', 'unknown')}: {str(e)}")
                continue
        
        # Sort responses by participant, round, and question order
        def extract_question_number(question_id):
            """Extract question number for sorting"""
            # Look for numbers in question_id
            numbers = re.findall(r'\d+', str(question_id))
            return int(numbers[0]) if numbers else 999
        
        enhanced_responses.sort(key=lambda x: (
            x['participant_id'], 
            int(x['round']), 
            extract_question_number(x['question_id']),
            x['question_id']
        ))
        
        # Write to CSV
        fieldnames = ['session_id', 'participant_id', 'round', 'question_id', 'answer', 'reason', 'summary', 'prompt']
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(enhanced_responses)
        
        if enhanced_responses:
            logger.info(f"Successfully wrote {len(enhanced_responses)} enhanced responses to {csv_file}")
        else:
            logger.warning(f"No enhanced responses found for session {session_id}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error in export_response_data: {str(e)}")
        
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
            fieldnames = ['session_id', 'participant_id', 'round', 'question_id', 'answer', 'reason', 'summary', 'prompt']
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow({
                    'session_id': session_id or 'unknown',
                    'participant_id': 'error',
                    'round': 1,
                    'question_id': 'export_error',
                    'answer': f'Export failed: {str(e)}',
                    'reason': 'System error during data export',
                    'summary': 'Error occurred during data export process',
                    'prompt': 'N/A'
                })


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

        # Remove the roles from file naming
        model_suffix = f"{app_suffix}_nhumans{n_humans_actual}_nbots{n_bots}"

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
            
            # Run bots in parallel threads with assigned models and roles
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
                            
                            # IMPORTANT: Use run_bot directly instead of run_single_bot to avoid duplicate insertion
                            thread = Thread(
                                target=botex.run_bot,
                                kwargs={
                                    'url': url,
                                    'session_id': otree_session_id,
                                    'botex_db': botex_db,
                                    'model': model_info['full_name'],
                                    'api_key': api_key,
                                    'user_prompts': user_prompts,
                                    'temperature': args.temperature,
                                    'max_tokens': args.max_tokens,
                                    'throttle': not args.no_throttle,
                                    'full_conv_history': False
                                }
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
        
        # Export data using botex standard functions with comprehensive coverage
        logger.info(f"Session {session_number}: Exporting comprehensive data...")

        # Export oTree wide data
        otree_wide_csv = os.path.join(output_dir, f"otree_{otree_session_id}_wide{model_suffix}.csv")
        try:
            botex.export_otree_data(
                otree_wide_csv,
                server_url=args.otree_url,
                admin_name='admin',
                admin_password=os.environ.get('OTREE_ADMIN_PASSWORD')
            )
            logger.info(f"Session {session_number}: oTree wide data exported")
        except Exception as e:
            logger.error(f"Session {session_number}: Failed to export oTree wide data: {str(e)}")

        # Normalize oTree data to get all levels (session, participant, group, player)
        try:
            normalized_data = botex.normalize_otree_data(
                otree_wide_csv, 
                store_as_csv=True,
                data_exp_path=output_dir,
                exp_prefix=f"otree_{otree_session_id}{model_suffix}"
            )
            logger.info(f"Session {session_number}: oTree data normalized into separate files")
            
            # Log what data files were created
            expected_files = ['session', 'participant', 'group', 'player']
            for data_type in expected_files:
                file_path = os.path.join(output_dir, f"otree_{otree_session_id}{model_suffix}_{data_type}.csv")
                if os.path.exists(file_path):
                    logger.info(f"  ✓ Created {data_type} data: {file_path}")
                else:
                    logger.warning(f"  ✗ Missing {data_type} data file")
                    
        except Exception as e:
            logger.warning(f"Session {session_number}: Data normalization warning: {str(e)}")

        # Export botex data if there were bots
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
                # Use enhanced export function
                export_response_data(
                    os.path.join(output_dir, f"botex_{otree_session_id}_responses{model_suffix}.csv"),
                    botex_db=botex_db,
                    session_id=otree_session_id
                )
                logger.info(f"Session {session_number}: Enhanced botex response data exported")
            except Exception as e:
                logger.warning(f"Session {session_number}: Error exporting enhanced botex responses: {str(e)}")

        # Create comprehensive data summary
        summary_file = os.path.join(output_dir, f"data_export_summary_{otree_session_id}{model_suffix}.txt")
        with open(summary_file, 'w') as f:
            f.write(f"Data Export Summary - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*70 + "\n\n")
            
            f.write("FILES EXPORTED:\n")
            f.write("-" * 20 + "\n")
            
            # List all files in output directory
            for file_name in sorted(os.listdir(output_dir)):
                if file_name.endswith('.csv'):
                    file_path = os.path.join(output_dir, file_name)
                    file_size = os.path.getsize(file_path)
                    f.write(f"  {file_name} ({file_size:,} bytes)\n")
            
            f.write(f"\nEXPERIMENT DETAILS:\n")
            f.write("-" * 20 + "\n")
            f.write(f"App: {args.app}\n")
            f.write(f"Session ID: {otree_session_id}\n")
            f.write(f"Total Participants: {len(is_human_list)}\n")
            f.write(f"Human Participants: {n_humans_actual}\n")
            f.write(f"Bot Participants: {n_bots}\n")
            
            if player_roles:
                f.write(f"\nROLE ASSIGNMENTS:\n")
                f.write("-" * 20 + "\n")
                for player_id, role in player_roles.items():
                    participant_type = "HUMAN" if session['is_human'][player_id - 1] else "BOT"
                    model_info = f" ({player_models.get(player_id, 'N/A')})" if participant_type == "BOT" else ""
                    f.write(f"  Player {player_id}: {role} ({participant_type}){model_info}\n")

        logger.info(f"Session {session_number}: Comprehensive data export completed")
        return {"success": True, "session_id": otree_session_id, "output_dir": output_dir}
    
    except Exception as e:
        logger.error(f"Session {session_number}: Error: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}