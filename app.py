from flask import Flask
from flask import render_template
from flask import request

import engine

app = Flask(__name__)


@app.route('/search', methods=['GET'])
def search():
    if request.method == 'GET':
        docs = engine.search(request.args.get('query'))
        return render_template('results.html', docs=docs)
    return 'smt'

@app.route('/get_doc', methods=['GET'])
def get_doc():
    if request.method == 'GET':
        return render_template('doc.html', doc=engine.get_doc(request.args.get('docid')))
    return 'smt'

@app.route('/')
def hello_world(name=None):
    return render_template('main.html', name=name)

if __name__ == '__main__':
    app.run()