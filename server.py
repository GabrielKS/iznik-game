from flask import Flask, render_template
from backend import basic_cli, frontend_prototype
import logging

app = Flask(__name__)
app.debug = True
logging.getLogger("werkzeug").disabled = True
@app.route("/")
def index():
    return render_template("index.html", scriptname="script/components.js")
app.register_blueprint(basic_cli.bp)
app.register_blueprint(frontend_prototype.bp)
app.run()
