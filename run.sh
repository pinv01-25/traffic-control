echo "Killing any process on port 8003..."
lsof -ti:8003 | xargs kill -9

echo "Verificando base de datos..."
python3 auto_init_db.py

if [ $? -ne 0 ]; then
    echo "Error inicializando base de datos"
    exit 1
fi

echo "Starting traffic-control API on port 8003..."
uvicorn api.server:app --reload --port 8003
