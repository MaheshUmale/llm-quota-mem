@echo off
echo Initializing llm-quota-mem environment...

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    exit /b 1
)

:: Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

:: Install dependencies
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -e .
pip install pytest pytest-asyncio

:: Create .env template if it doesn't exist
if not exist ".env" (
    echo Creating .env template...
    (
    echo # LLM Providers
    echo GROQ_API_KEY=
    echo SAMBANOVA_API_KEY=
    echo TOGETHER_API_KEY=
    echo GOOGLE_API_KEY=
    echo OPENAI_API_KEY=
    echo OPENROUTER_API_KEY=
    echo CEREBRAS_API_KEY=
    echo MISTRAL_API_KEY=
    echo GITHUB_API_KEY=
    echo CLOUDFLARE_API_KEY=
    echo CLOUDFLARE_ACCOUNT_ID=
    echo NVIDIA_API_KEY=
    echo.
    echo # Optional Configurations
    echo DEFAULT_MODEL=gpt-4o-mini
    echo TEMPERATURE=0.7
    ) > .env
    echo .env file created. Please add your API keys.
)

echo.
echo Setup complete!
echo To activate the environment: venv\Scripts\activate
echo To start the server: python -m llm_quota_mem.app
pause
