import game
import player

class Controller:
    def __init__(self, game, players):
        assert len(players) == game.view.n_players
        self.game = game
        self.players = players
        self.game_over = False
        for player in self.players:
            player.update(self.game.view)
    
    def step(self):
        if self.game_over: return
        turn = self.game.view.turn
        if turn < 0:
            print("Game over!")
            print("Player "+max(range(len(self.game.state.player_boards)), [board.score for board in self.game.state.player_boards])+" won!")
            self.game_over = True
            return
        else:
            move = self.players[turn].play(self.game.check)
            assert isinstance(move, game.Move), f"Invalid move: {move}"
            assert move.player_id == turn, f"It is Player {turn}'s turn, not Player {move.player_id}'s"
            self.game.play(move)
            for player in self.players:
                player.update(self.game.view)
