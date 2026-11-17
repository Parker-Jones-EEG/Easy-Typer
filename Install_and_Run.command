#!/bin/bash
cd "$(dirname "$0")"

echo "🚀 Setting up Easy Typer..."

# 1. Create isolated Python virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# 2. Install dependencies
echo "⬇️ Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# 3. Check if Ollama is installed & pull model if available
if command -v ollama &> /dev/null; then
    echo "🧠 Ollama detected! Ensuring llama3.2 model is ready..."
    ollama pull llama3.2
else
    echo "⚠️ Ollama not found. Easy Typer will use the built-in offline humanizer."
    echo "👉 For full AI rewriting & prompt generation, install Ollama from https://ollama.com"
fi

# 4. Build standalone macOS .app
echo "🛠️ Building Easy Typer.app..."
rm -rf build dist
python setup.py py2app -A > /dev/null 2>&1

# Copy to main folder for easy access
rm -rf "Easy Typer.app"
cp -R "dist/Easy Typer.app" "./Easy Typer.app"

echo "✅ Done! Launching Easy Typer in your top menu bar..."
open "./Easy Typer.app"
