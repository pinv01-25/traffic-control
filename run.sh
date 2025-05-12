echo "Killing any process on port 8003..."
lsof -ti:8003 | xargs kill -9

echo "Starting traffic-control API on port 8003..."
uvicorn main:app --reload --port 8003
