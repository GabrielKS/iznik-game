from flask import Blueprint, render_template, request
from simulation.game import Game, Move
from simulation.player import Player
from simulation.controller import Controller

bp = Blueprint("basic CLI", __name__, url_prefix="/basic-cli")

games = []  # To be filled later

def create_game():
    game = Game.new_game(2, False, random_seed=0)
    p0 = CLIPlayer(0, 2)
    p1 = CLIPlayer(1, 2)
    return Controller(game, (p0, p1))

@bp.route("/play", methods=("GET", "POST"))
def play():
    if len(games) == 0: games.append(create_game())  # For now, we'll only work with one game instance
    body = request.get_json()
    print(body)
    if request.method == "GET":
        return render_template("play.html", scriptname="basic-cli.js")
    elif request.method == "POST":
        if body is not None:
            if "requestType" in body:
                if body["requestType"] == "stateText":
                    if body["player"] is None:
                        return {"stateText": "Set your player ID first!"}
                    else:
                        return {"stateText": games[0].players[int(body["player"])].state_text}
        return "Move acknowledged: "+str(body)

class CLIPlayer(Player):
    def __init__(self, player_id, n_players):
        super().__init__(player_id, n_players)
        self._game_state = None
        self._state_text = ""
        self._next_move = None
        self._error_text = None
        self._success = False
        
    def update(self, view):
        self._game_state = view
        self._state_text = str(view)
        if view.turn < 0:
            self._state_text += "\nGame over!"
            self._state_text += "\nPlayer "+max(range(len(view.player_boards)), [board.score for board in self.game.state.player_boards])+" won!"
            

    def play(self, validator):
        if self._next_move is None:
            self._error_text = f"Player {self.player_id} did not submit a move."
        if self.player_id != self._next_move.player_id:
            self._error_text = f"It is {self.player_id}'s turn, not {self._next_move.player_id}'s"
        if not validator(self._next_move):
            self._error_text = f"Invalid move; please try again."
        else:
            self._success = True
            return self._next_move
        print(self._error_text)
    
    @property
    def state_text(self):
        return self._state_text

    def set_next_move(self, next_move):
        self._next_move = next_move
    
    def test_move_success(self):
        result = (self.success, "Success!" if self.success else self.error_text)
        self.success = False
        self.error_text = None
        return result