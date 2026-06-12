#!/bin/sh

# 1. Run the database initialization
# We use 'python -c' to run a snippet of python code to call your function
python -c "from app import init_db; init_db()"

# 2. Start the web server
# 'exec' ensures the signals (like SIGTERM) are passed to the python process
exec gunicorn -b 0.0.0.0:5000 app:app