#!/bin/bash
set -e

echo "🚀 Starting RecoverOS Services..."

# Ensure dataset and model exist
if [ ! -f "data/payments.csv" ]; then
    echo "📊 Generating synthetic payments dataset..."
    python3 data/generate_data.py
fi

if [ ! -f "models/recovery_model.pkl" ]; then
    echo "🤖 Training ML recovery model..."
    python3 models/train_model.py
fi

# Start FastAPI backend server in background on port 8000
echo "⚡ Starting FastAPI Policy Engine on port 8000..."
PYTHONPATH=/app/backend python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &

# Start Streamlit application on port 8501
echo "💳 Starting Streamlit AI Revenue Recovery Agent on port 8501..."
exec python3 -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --browser.gatherUsageStats=false
