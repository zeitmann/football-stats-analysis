from flask import Flask, jsonify

app = Flask(__name__)


@app.route('/')
def home():
    """Basic route that returns a welcome message."""
    return jsonify({
        'message': 'Welcome to Football Stats Analysis API',
        'status': 'running'
    })


if __name__ == '__main__':
    app.run(debug=True)
