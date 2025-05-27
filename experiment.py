#!/usr/bin/env python3
"""
experiment.py - Social influence task experiment execution

This module contains all the logic for running individual experimental sessions,
configuring bots, managing prompts, and exporting data.
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

# Import prompt functions from separate module
from prompts import (
    get_general_instructions,
    get_questionnaire_instructions,
    get_task_instructions,
    get_questionnaire_role_instructions,
    get_bot_prompts,
    get_tinyllama_prompts
)

logger = logging.getLogger("sit_experiment")


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
    }
    
    additional_params['repetition_penalty'] = 1.1
    
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
        
        # Separate comprehension questions from other responses
        comprehension_responses = []
        task_responses = []
        
        for response in responses:
            question_id = response.get('question_id', '')
            # Identify comprehension questions
            if ('comprehension' in question_id.lower() or 
                question_id.lower().startswith('q') or
                response['round'] == 1):  # Round 1 is typically comprehension checks
                comprehension_responses.append(response)
            else:
                task_responses.append(response)
        
        # Define the desired order of task questions
        order_map = {
            'id_choice1': 1,
            'id_bet1': 2,
            'id_choice2': 3,
            'id_bet2': 4,
        }
        
        # Sort task responses by round and question_id order
        task_responses.sort(key=lambda x: (int(x['round']), order_map.get(x['question_id'], 999)))
        
        # Combine with comprehension questions at the top
        ordered_responses = comprehension_responses + task_responses
        
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


def log_actual_model_used():
    """
    Simple wrapper to log what model is actually being used in API calls.
    Also logs when models fail or are unavailable.
    """
    import litellm
    
    # Store original completion function
    original_completion = litellm.completion
    
    def logged_completion(*args, **kwargs):
        model_requested = kwargs.get('model', 'unknown')
        
        try:
            # Make the API call
            response = original_completion(*args, **kwargs)
            
            # Log what model was actually used (success case)
            actual_model = getattr(response, 'model', model_requested)
            logger.info(f"🤖 ACTUAL MODEL USED: {actual_model} (requested: {model_requested})")
            
            return response
            
        except Exception as e:
            # Log when model fails or is unavailable
            logger.error(f"❌ MODEL NOT AVAILABLE: {model_requested} - Error: {str(e)}")
            
            # Re-raise the exception so normal error handling continues
            raise e
    
    # Replace the completion function
    litellm.completion = logged_completion


def run_session(args, session_number, player_models, is_human_list, available_models):
    """Run a single experimental session using standard botex workflow"""
    try:

        # Enable simple model logging
        log_actual_model_used()

        # Create timestamp for this session
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"session_{session_number}_{timestamp}"
        
        # Calculate derived values
        n_humans_actual = sum(1 for is_human in is_human_list if is_human)
        n_bots = args.participants - n_humans_actual
        
        # Create simplified model suffix
        if player_models and n_bots > 0:
            model_suffix = f"_mixed_nhumans{n_humans_actual}_nbots{n_bots}_qrole{args.q_role}"
        elif n_bots > 0:
            model_suffix = f"_bots_nhumans{n_humans_actual}_nbots{n_bots}_qrole{args.q_role}"
        else:
            model_suffix = f"_humans_only_nhumans{n_humans_actual}_qrole{args.q_role}"
        
        # Create session-specific output directory
        output_dir = os.path.join(args.output_dir, f"session_{session_id}{model_suffix}")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create session-specific database file
        botex_db = os.path.join(output_dir, f"botex_{session_id}{model_suffix}.sqlite3")
        
        logger.info(f"Session {session_number}: Output directory: {output_dir}")
        
        # Pre-calculate model assignments
        initial_session_config_fields = {}

        if player_models:
            for player_id, model_name in player_models.items():
                initial_session_config_fields[f'player_{player_id}_intended_model'] = model_name
                
                # If this player is explicitly a bot, store the bot assignment
                if is_human_list and player_id <= len(is_human_list) and not is_human_list[player_id - 1]:
                    initial_session_config_fields[f'bot_position_{player_id}_model'] = model_name

        # Initialize session with explicit assignment
        session = botex.init_otree_session(
            config_name=args.session_config,
            npart=args.participants,
            is_human=is_human_list,  # Use explicit assignment
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
                    logger.info(f"Session {session_number}: Player {player_position} (participant {participant_code}) -> HUMAN")
                else:
                    if player_position in player_models:
                        assigned_model = player_models[player_position]
                        logger.info(f"Session {session_number}: Player {player_position} (participant {participant_code}) -> {assigned_model}")

        # Get the monitor URL and open browser
        monitor_url = f"{args.otree_url}/SessionMonitor/{otree_session_id}"
        logger.info(f"Session {session_number}: Monitor URL: {monitor_url}")
        
        # Display session info
        if session['human_urls']:
            print(f"\nSession {session_number}: Human participant URLs:")
            for i, url in enumerate(session['human_urls'], 1):
                print(f"  Participant {i}: {url}")
        
        if session['bot_urls']:
            if player_models:
                print(f"\nSession {session_number}: Starting {len(session['bot_urls'])} bots with player-specific models (q-role: {args.q_role})")
            else:
                print(f"\nSession {session_number}: Starting {len(session['bot_urls'])} bots (q-role: {args.q_role})")
        
        if n_bots == 0:
            print(f"\nSession {session_number}: All {args.participants} participants are human")
        
        print(f"Monitor progress at: {monitor_url}")
        
        # Automatically open Chrome with the monitor URL (unless disabled)
        if not getattr(args, 'no_browser', False):
            open_chrome_browser(monitor_url)
        
        # Run bots if there are any
        if session['bot_urls']:
            logger.info(f"Session {session_number}: Running bots with player-specific models")
            
            # Start llama.cpp server if any local models are used
            use_local_model = any(available_models[player_models[player_id]]['provider'] == 'local' 
                                  for player_id in range(1, args.participants + 1) 
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
                        "server_path": args.server_path,
                        "local_llm_path": args.model_path,
                        "server_url": server_url,
                        "maximum_tokens_to_predict": args.max_tokens,
                        "temperature": args.temperature,
                    })
                    logger.info(f"Session {session_number}: llama.cpp server started")
            
            # Run bots individually with assigned models
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
                        
                        # Log bot assignment attempt
                        logger.info(f"🔄 ATTEMPTING TO ASSIGN: Player {player_id} → {model_name}")
                        
                        try:
                            api_key = None
                            if model_info['api_key_env']:
                                api_key = os.environ.get(model_info['api_key_env'])
                            
                            if model_info['provider'] == 'local':
                                user_prompts = get_tinyllama_prompts(args.q_role if args.q_role != "none" else None)
                                modified_prompts, tinyllama_params = configure_tinyllama_params(args, user_prompts)
                                user_prompts = modified_prompts

                            else:
                                user_prompts = get_bot_prompts(args.q_role if args.q_role != "none" else None)
                            
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
                            
                            logger.info(f"✅ BOT STARTED: Player {player_id} with {model_name}")
                            
                        except Exception as e:
                            logger.error(f"❌ BOT ASSIGNMENT FAILED: Player {player_id} → {model_name} - Error: {str(e)}")
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
            f.write(f"Social Influence Task Experiment Summary - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*70 + "\n\n")
            f.write(f"Session ID: {otree_session_id}\n")
            f.write(f"Session Number: {session_number}\n")
            f.write(f"Participants: {args.participants} total ({n_humans_actual} human, {n_bots} bots)\n")
            f.write(f"Questionnaire role: {args.q_role}\n\n")
            
            if session['human_urls']:
                f.write("Human participant URLs:\n")
                for i, url in enumerate(session['human_urls'], 1):
                    f.write(f"  Participant {i}: {url}\n")
            
            if player_models and n_bots > 0:
                f.write("\nBot model assignments:\n")
                bot_idx = 0
                for i, is_human in enumerate(session['is_human']):
                    if not is_human:
                        player_id = i + 1
                        if player_id in player_models:
                            model_name = player_models[player_id]
                            provider = available_models[model_name]['provider']
                            f.write(f"  Player {player_id}: {model_name} ({provider})\n")
                        bot_idx += 1
        
        logger.info(f"Session {session_number}: Session completed successfully")
        return {"success": True, "session_id": otree_session_id, "output_dir": output_dir}
    
    except Exception as e:
        logger.error(f"Session {session_number}: Error: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}