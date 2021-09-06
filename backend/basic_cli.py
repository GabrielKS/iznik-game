from flask import Blueprint, render_template, request
import simulation.game
from simulation.game import Game, Move, Tile
from simulation.player import Player
import time
import dataclasses
from collections import namedtuple
import json

debug = False
simulation.game.debug = debug

bp = Blueprint("basic CLI", __name__, url_prefix="/basic-cli")

games = []  # To be filled later
GameResponse = namedtuple("GameResponse", ("stateText", "status", "statusType", "gameState"))

def create_game():
    game = Game.new_game(2, False, random_seed=1)
    p0 = CLIPlayer(0, 2)
    p1 = CLIPlayer(1, 2)
    return GameContainer(game, (p0, p1))

@bp.route("/play", methods=("GET", "POST"))
def play():
    if len(games) == 0: games.append(create_game())  # For now, we'll only work with one game instance
    body = request.get_json()
    if request.method == "GET":
        # Requesting the page
        return render_template("play.html", scriptname="basic-cli.js", stylename="css/basic-cli.css")
    elif request.method == "POST":
        if body is not None:
            if "requestType" in body:
                if body["requestType"] == "stateText":
                    # Requesting game state
                    if body["player"] is None:
                        return GameResponse(stateText=timestamp()+"\nSet your player ID first!", status="Please select your Player ID above", statusType="error", gameState="{}")._asdict()
                    else:
                        clientPlayer = games[0].players[int(body["player"])]
                        return GameResponse(stateText=timestamp()+"\n"+clientPlayer.state_text, status=clientPlayer.status_text, statusType=clientPlayer.status_type, gameState=clientPlayer.state_json)._asdict()
        # Sending in a move
        player_id = int(body["player"])
        move = Move(player_id, Tile.from_symbol(body["tile"]), int(body["source"]), int(body["dest"]))
        games[0].process_input(move)
        return {"success": games[0].players[player_id].move_success}

def timestamp():
    return f"{time.asctime()} .{round((time.time()%1)*1000)}" if debug else time.strftime("Updated: %I:%M:%S %p")
    # str(["|", "/", "-", "\\"][round(time.time() % 4)])
    # time.strftime("Updated: %I:%M:%S %p")

class CLIPlayer(Player):
    def __init__(self, player_id, n_players):
        super().__init__(player_id, n_players)
        self._game_state = None
        self._state_text = ""
        self._state_json = ""
        self._next_move = None
        self._status_text = None
        self._status_type = "note"
        self._move_success = False
        
    def update(self, view):
        self._game_state = view
        self._state_text = str(view)
        self._state_json = json.dumps(dataclasses.asdict(view), default = lambda x: x.value)
        if view.turn == self.player_id:
            self._status_text = f"Your turn, Player {self.player_id}!"
            self._status_type = "prompt"
        elif view.turn < 0:
            a = "Game over!"
            winners = view.winners
            if len(winners) == 1: b = "Player "+str(winners[0])+" won!"
            else:
                winners_str = ["Player "+str(w) for w in winners]
                winners_str[len(winners)-1] = "and "+winners_str[len(winners)-1]
                b = "Tie between "+(" " if len(winners) == 2 else ", ").join(winners_str)+"!"
            self._status_text = a+" "+b
            self._status_type = "prompt"
            self._state_text += "\n\n"+a+"\n"+b
        else:
            self._status_text = f"It is Player {view.turn}'s turn."
            self._status_type = "note"

    def play(self, validator):
        self._move_success = False
        if self._next_move is None:
            self._status_text = f"Player {self.player_id} did not submit a move."
            self._status_type = "error"
        if self.player_id != self._next_move.player_id:
            self._status_text = f"This is {self.player_id}'s turn, not {self._next_move.player_id}."
            self._status_type = "error"
        valid, error = validator(self._next_move)
        if not valid:
            self._status_text = "Invalid move! "+error.message
            self._status_type = "error"
        else:
            self._status_text = "Successful move!"
            self._status_type = "note"
            self._move_success = True
            return self._next_move
    
    @property
    def state_text(self):
        return self._state_text

    @property
    def state_json(self):
        return self._state_json
    
    @property
    def status_text(self):
        return self._status_text
    
    @property
    def status_type(self):
        return self._status_type

    @property
    def move_success(self):
        success = self._move_success
        self._move_success = False
        return success

    def set_next_move(self, next_move):
        self._next_move = next_move

class GameContainer:  # A replacement for simulation.controller that works better for this application
    def __init__(self, game, players):
        assert len(players) == game.view.n_players
        self.game = game
        self.players = players
        self.game_over = False
        for player in self.players:
            player.update(self.game.view)
    
    def process_input(self, move):
        clientPlayer = self.players[move.player_id]
        clientPlayer.set_next_move(move)
        validated_move = clientPlayer.play(self.game.check)
        if validated_move is not None:
            self.game.play(validated_move)
            for player in self.players:
                player.update(self.game.view)