from flask import Blueprint, render_template, request

bp = Blueprint("frontend prototype", __name__, url_prefix="/frontend-prototype")

@bp.route("/", methods=("GET",))
def prototype():
    return render_template("frontend-prototype.html", scriptname="frontend-prototype.js", stylename="css/frontend-prototype.css")