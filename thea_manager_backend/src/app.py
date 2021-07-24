#!/usr/bin/env python

# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# Flask imports
from flask import Flask, jsonify

# Declare app
app = Flask(__name__)

# ---------------------------------------------------------------
#                   Error handling and Test
# ---------------------------------------------------------------

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"data": "Bad request"})

@app.errorhandler(404)
def not_found(error):
    return jsonify({"data": "Not found"})

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"data": "Health Check"})

# ---------------------------------------------------------------
#                       Entrypoint
# ---------------------------------------------------------------

if __name__ == '__main__':
    # port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=5000)