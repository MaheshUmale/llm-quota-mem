#!/bin/bash

# llm-quota-mem setup script

echo "Initializing llm-quota-mem environment..."

# Check for Python 3.11+
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if (( $(echo "$PYTHON_VERSION < 3.11" | bc -l) )); then
    echo "Error: Python 3.11 or higher is required. Found $PYTHON_VERSION"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -e .
pip install pytest pytest-asyncio

# Create .env template if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env template..."
    cat <<EOT >> .env
# LLM Providers
GROQ_API_KEY=
SAMBANOVA_API_KEY=
TOGETHER_API_KEY=
GOOGLE_API_KEY=
OPENAI_API_KEY=
OPENROUTER_API_KEY=
CEREBRAS_API_KEY=
MISTRAL_API_KEY=
GITHUB_API_KEY=
CLOUDFLARE_API_KEY=
CLOUDFLARE_ACCOUNT_ID=
NVIDIA_API_KEY=

# Optional Configurations
DEFAULT_MODEL=gpt-4o-mini
TEMPERATURE=0.7
EOT
    echo ".env file created. Please add your API keys."
fi

echo "Setup complete! Activate your environment with: source venv/bin/activate"
