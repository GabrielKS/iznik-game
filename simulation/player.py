import game

class Player:
    def __init__(self, player_id, n_players):
        self.player_id = player_id
        self.n_players = n_players

    def update(self, view: game.GameState):
        raise NotImplementedError

    def play(self) -> game.Move:
        raise NotImplementedError

class TextInputPlayer(Player):
    def __init__(self, player_id, n_players, print_updates=True):
        super().__init__(player_id, n_players)
        self.print_updates = print_updates
        self.game_state = None

    def update(self, view):
        self.game_state = view
        if self.print_updates:
            print(f"P{self.player_id}: Game state:")
            print(self.game_state)
            print()
    
    def play(self):
        assert self.game_state is not None, f"Player {self.player_id} has not been updated yet"
        assert self.game_state.turn == self.player_id, f"It is Player {self.game_state.turn}'s turn, not Player {self.player_id}'s"
        while True:
            source_id = self.prompt_validate("Source (batch number or 0 for bench):  ", int, lambda x: x in range(game.SETTINGS.N_BATCHES[self.n_players]))
            tile = self.prompt_validate("Tile type (first letter or full name): ", game.Tile.from_symbol, lambda x: x in game.Tile.color_tiles())
            dest_id = self.prompt_validate("Destination (stage # or 0 for floor):  ", int, lambda x: x in range(game.SETTINGS.ROWS))
            print(f"Proposed move: {tile.name} from {f'Batch {source_id}' if source_id > 0 else 'Bench'} to {f'Stage {dest_id}' if dest_id > 0 else 'Floor'}")
            if self.prompt_validate("Confirm move (y for yes or n for no):  ", str, lambda x: x == "y" or x == "n") == "y":
                print()
                return game.Move(self.player_id, tile, source_id, dest_id)

    
    def prompt_validate(self, msg, mutator, validator):
        while True:
            val = input(f"P{self.player_id}: {msg}")
            try:
                val = mutator(val)
            except ValueError:
                print("Invalid input type; please try again:")
                continue
            if validator(val): return val
            else: print("Invalid input value; please try again:")

