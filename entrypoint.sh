#!/bin/sh

# 1. Run the database initialization
# We use 'python -c' to run a snippet of python code to call your function
python -c "from app import init_db; init_db()"

# Finishes script
exec "$@"