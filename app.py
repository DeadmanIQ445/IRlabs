from multiprocessing import Process

from flask import Flask
from flask import render_template
from flask import request

import cache
import eng_class
import engine
import red_search

app = Flask(__name__)


@app.route('/search', methods=['GET'])
def search():
    if request.method == 'GET':
        docs = red_search.search(request.args.get('query'), engine_obj)
        return render_template('results.html', docs=docs)
    return 'smt'

@app.route('/get_doc', methods=['GET'])
def get_doc():
    if request.method == 'GET':
        return render_template('doc.html', doc=engine.get_doc(request.args.get('docid'), engine_obj))
    return 'smt'


@app.route('/')
def hello_world(name=None):
    return render_template('main.html', name=name)


@app.route("/new_doc", methods=['GET', 'POST'])
def new_doc():
    if request.method == 'GET':
        return render_template("new_doc.html")
    elif request.method == "POST":
        engine_obj.update(request.form['text'])
        return render_template("main.html", name=None)


engine_obj = eng_class.Engine()

if __name__ == '__main__':
    thread = Process(target=cache.run)
    thread.run()
    app.run()