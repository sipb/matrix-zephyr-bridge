from matrix_receive import app
from config import config

# TODO: call both parts of the bridge

# The built-in Flask server is only for debugging

if __name__ == '__main__':
    app.run(debug=True, port=config.listen_port)
    
