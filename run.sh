for x in `cat .env`;do export $x;done
source .venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8888 --reload
