from flask import Blueprint, render_template
bp = Blueprint("basic CLI", __name__, url_prefix="/basic-cli")

@bp.route("/play")
def play():
    return render_template("play.html", scriptname="basic-cli.js")
