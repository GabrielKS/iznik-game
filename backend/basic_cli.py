from flask import Blueprint, render_template, request
from simulation.game import Game

bp = Blueprint("basic CLI", __name__, url_prefix="/basic-cli")

games = [Game.new_game(2, False, random_seed=0)]  # For now, we'll only work with one game instance

@bp.route("/play", methods=("GET", "POST"))
def play():
    if request.method == "GET":
        return render_template("play.html", scriptname="basic-cli.js")
    # elif request.method == "POST":