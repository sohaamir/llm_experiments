#!/bin/bash
# download_model.sh

set -e  # Exit on error

# Create models directory
mkdir -p models

echo "Installing llama.cpp dependencies..."
pip install cmake scikit-build setuptools

# Download TinyLLaMA model
MODEL_PATH="models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"

if [ -f "$MODEL_PATH" ]; then
    echo "TinyLLaMA model already exists at $MODEL_PATH"
else
    echo "Downloading TinyLLaMA model (approximately 700MB)..."
    curl -L "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" \
        -o "$MODEL_PATH" --progress-bar
    echo "Model downloaded successfully!"
fi

echo "Setup complete! You can now run experiments with TinyLLaMA."