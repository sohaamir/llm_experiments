#!/bin/bash
# run_llama_server.sh - Script to run the llama.cpp server binary with configurable options

# Source environment file if it exists
if [ -f "botex.env" ]; then
    source botex.env
fi

# Default values
MODEL_PATH="${LLAMACPP_LOCAL_LLM_PATH:-models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf}"
SERVER_PATH="${LLAMACPP_SERVER_PATH:-./llama_server}"
HOST="127.0.0.1"
PORT="${LLAMACPP_PORT:-8080}"
MAX_TOKENS="${LLAMACPP_MAX_TOKENS:-512}"
TEMPERATURE="${LLAMACPP_TEMPERATURE:-0.7}"
TOP_P="${LLAMACPP_TOP_P:-0.9}"
TOP_K="${LLAMACPP_TOP_K:-40}"
CTX_SIZE="${LLAMACPP_CTX_SIZE:-2048}"
THREADS="${LLAMACPP_THREADS:-4}"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --model)
            MODEL_PATH="$2"
            shift 2
            ;;
        --server)
            SERVER_PATH="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --max-tokens)
            MAX_TOKENS="$2"
            shift 2
            ;;
        --temperature)
            TEMPERATURE="$2"
            shift 2
            ;;
        --top-p)
            TOP_P="$2"
            shift 2
            ;;
        --top-k)
            TOP_K="$2"
            shift 2
            ;;
        --ctx-size)
            CTX_SIZE="$2"
            shift 2
            ;;
        --threads)
            THREADS="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if the server binary exists
if [ ! -f "$SERVER_PATH" ]; then
    echo "Error: llama.cpp server binary not found at $SERVER_PATH"
    echo "Please run ./install_llama_cpp.sh first to install llama.cpp"
    exit 1
fi

# Check if the model exists
if [ ! -f "$MODEL_PATH" ]; then
    echo "Error: Model file not found at $MODEL_PATH"
    echo "Please run ./download_model.sh first to download the model"
    exit 1
fi

echo "Starting llama.cpp server with model: $MODEL_PATH"
echo "Server will be available at http://$HOST:$PORT"
echo "Parameters:"
echo "  Max tokens: $MAX_TOKENS"
echo "  Temperature: $TEMPERATURE"
echo "  Top-P: $TOP_P"
echo "  Top-K: $TOP_K"
echo "  Context Size: $CTX_SIZE"
echo "  Threads: $THREADS"

# Run the server with all parameters on a single line
$SERVER_PATH --model $MODEL_PATH --host $HOST --port $PORT --ctx-size $CTX_SIZE --n-predict $MAX_TOKENS --temp $TEMPERATURE --top-p $TOP_P --top-k $TOP_K --repeat-penalty 1.1 --threads $THREADS --n-gpu-layers 0 --parallel 1 --embedding