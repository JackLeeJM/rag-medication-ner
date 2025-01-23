#!/bin/bash

OLLAMA_URL="$OLLAMA_API_HOST:$OLLAMA_API_PORT"

# Wait for Ollama server to be ready
wait_for_server() {
    echo "Waiting for Ollama server to be ready..."
    ollama serve &
    OLLAMA_PID=$!

    while [ "$(ollama list | grep 'NAME')" == "" ]; do
        sleep 1
    done

    echo "Ollama server is ready!"
}

# Check if model exists
check_model() {
    echo "Checking if model exists ..."
    local model_name=$1
    ollama list | grep $model_name > /dev/null
    return $?
}

# Main execution
main() {
    # Ensure OLLAMA_MODEL is set
    if [ -z "$OLLAMA_MODEL" ]; then
        echo "Error: OLLAMA_MODEL environment variable is not set"
        exit 1
    fi

    # Start and wait for server
    wait_for_server

    # Check if model exists, pull if it doesn't
    if ! check_model "$OLLAMA_MODEL"; then
        echo "Model $OLLAMA_MODEL not found. Pulling..."
        ollama pull "$OLLAMA_MODEL"
        if [ $? -ne 0 ]; then
            echo "Error: Failed to pull model $OLLAMA_MODEL"
            exit 1
        fi
        echo "Model $OLLAMA_MODEL successfully pulled!"
    else
        echo "Model $OLLAMA_MODEL already exists"
    fi

    # Keep the container running by waiting for the Ollama process
    wait $OLLAMA_PID
}

# Run main function
main