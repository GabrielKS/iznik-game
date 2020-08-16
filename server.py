from flask import Flask, render_template
from backend import basic_cli

app = Flask(__name__)
app.debug = True
@app.route("/")
def index():
    return render_template("index.html", scriptname="components.js")
app.register_blueprint(basic_cli.bp)
app.run()
