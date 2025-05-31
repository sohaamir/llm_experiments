#!/bin/bash
# run_tinyllama.sh

# Start llama.cpp server
./run_llama_server.sh --max-tokens 256 --temperature 0.8 &
SERVER_PID=$!

# Wait for server to start
sleep 5

# Run directly with run_botex_experiment.py which has all options
python run_botex_experiment.py \
  --model tinyllama \
  --session-config social_influence_task \
  --sessions 1 \
  --max-tokens 256 \
  --temperature 0.8 \
  --strategy standard

# Clean up
kill $SERVER_PID