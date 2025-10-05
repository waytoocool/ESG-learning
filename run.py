# run.py
import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.config['DEBUG'] = True
    host = os.environ.get('FLASK_RUN_HOST', '127.0.0.1')
    app.run(host=host, port=8000, debug=True)
