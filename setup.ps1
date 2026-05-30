$env:PYTHON_EXECUTABLE = "python"
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    if (Get-Command python3 -ErrorAction SilentlyContinue) {
        $env:PYTHON_EXECUTABLE = "python3"
    } else {
        Write-Error "Error: Python is not installed or not in PATH."
        exit 1
    }
}

Write-Host "Initializing llm-quota-mem environment..."

# Create virtual environment if it doesn't exist
if (!(Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    & $env:PYTHON_EXECUTABLE -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..."
. .\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing dependencies..."
python -m pip install --upgrade pip
pip install -e .
pip install pytest pytest-asyncio

# Create .env template if it doesn't exist
if (!(Test-Path ".env")) {
    Write-Host "Creating .env template..."
    $envContent = @"
# LLM Providers
GROQ_API_KEY=
SAMBANOVA_API_KEY=
TOGETHER_API_KEY=
GOOGLE_API_KEY=
OPENAI_API_KEY=
OPENROUTER_API_KEY=

# Optional Configurations
DEFAULT_MODEL=gpt-4o-mini
TEMPERATURE=0.7
"@
    $envContent | Out-File -FilePath ".env" -Encoding utf8
    Write-Host ".env file created. Please add your API keys."
}

Write-Host "`nSetup complete!"
Write-Host "To activate the environment: .\venv\Scripts\Activate.ps1"
Write-Host "To start the server: python -m llm_quota_mem.app"
