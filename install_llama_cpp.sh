#!/bin/bash
# install_llama_cpp.sh - Script to install llama.cpp server binary without Metal

set -e  # Exit immediately if a command fails

echo "Installing llama.cpp server without Metal (CPU-only)..."

# Create a directory for llama.cpp
mkdir -p llama_cpp
cd llama_cpp

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Error: git is not installed. Please install git and try again."
    exit 1
fi

# Check if cmake is installed
if ! command -v cmake &> /dev/null; then
    echo "Error: cmake is not installed. Please install cmake and try again."
    exit 1
fi

# Check if a C++ compiler is installed
if ! command -v g++ &> /dev/null && ! command -v clang++ &> /dev/null; then
    echo "Error: No C++ compiler found. Please install g++ or clang++ and try again."
    exit 1
fi

# Clone the llama.cpp repository
echo "Cloning llama.cpp repository..."
if [ -d ".git" ]; then
    git pull
else
    git clone https://github.com/ggml-org/llama.cpp.git .
fi

# Build llama.cpp without Metal
echo "Building llama.cpp without Metal support (CPU-only)..."
mkdir -p build
cd build

# Configure build with Metal explicitly disabled
cmake .. -DBUILD_SHARED_LIBS=ON -DGGML_METAL=OFF

# Build
cmake --build . --config Release

# Verify the server binary exists
if [ -f "bin/llama-server" ]; then
    SERVER_BIN="bin/llama-server"
elif [ -f "bin/server" ]; then
    SERVER_BIN="bin/server"
else
    echo "Error: Could not find server binary. Build may have failed."
    exit 1
fi

echo "llama.cpp server built successfully without Metal support!"
echo "The server binary is located at: llama_cpp/build/$SERVER_BIN"

# Return to the original directory
cd ../../

# Create a symlink to the server binary for easier access
ln -sf "llama_cpp/build/$SERVER_BIN" llama_server

echo "You can now run the server with: ./llama_server"
echo "See also: ./llama_server --help for options"

# Optional: Check if model exists or offer to download one
if [ ! -d "models" ]; then
    mkdir -p models
    echo "Models directory created. You'll need to download a model in GGUF format."
    echo "Example: ./download_model.sh"
fi