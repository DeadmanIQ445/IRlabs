from flask import Flask
from flask import render_template
from flask import request

import engine

app = Flask(__name__)


@app.route('/search', methods=['GET'])
def search():
    if request.method == 'GET':
        docs = engine.search(engine.index, request.args.get('query'))
        return render_template('results.html', docs=docs)
    return 'smt'


@app.route('/')
def hello_world(name=None):
    return render_template('main.html', name=name)
