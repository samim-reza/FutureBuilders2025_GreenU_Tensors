#!/bin/bash
# WeCare Quick Setup Script

echo "🏥 WeCare Setup Script"
echo "======================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Please create one first: python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "✓ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "✓ Installing Python dependencies..."
pip install -q -r requirements.txt

# Check MySQL
echo "✓ Checking MySQL..."
if ! command -v mysql &> /dev/null; then
    echo "❌ MySQL not found! Please install: sudo apt install mysql-server"
    exit 1
fi

# Setup database
echo "✓ Setting up MySQL database..."
mysql -u root -p'S@mim101' -e "CREATE DATABASE IF NOT EXISTS wecare_db;" 2>/dev/null

# Run seed script
echo "✓ Initializing database and seeding data..."
python seed_data.py

# Check Ollama
echo "✓ Checking Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollama not found!"
    echo "   Install from: https://ollama.ai"
    echo "   Then run: ollama pull qwen3-vl:2b"
    echo ""
fi

# Check if Ollama model is downloaded
if command -v ollama &> /dev/null; then
    if ollama list | grep -q "qwen3-vl:2b"; then
        echo "✓ Ollama model qwen3-vl:2b is ready"
    else
        echo "⚠️  Model not found. Pulling qwen3-vl:2b..."
        echo "   This may take a while..."
        ollama pull qwen3-vl:2b
    fi
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Start Ollama: ollama serve"
echo "   2. Start WeCare: uvicorn app:app --host 0.0.0.0 --port 8000"
echo "   3. Open browser: http://localhost:8000"
echo ""
