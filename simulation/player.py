import game
from typing import Callable, Tuple, List

class Player:
    def __init__(self, player_id, n_players):
        self.player_id = player_id
        self.n_players = n_players

    def update(self, view: game.GameState) -> None:  # Gets called whenever there is a new game state
        raise NotImplementedError

    def play(self, validator: Callable[[game.Move], Tuple[bool, game.Error]]) -> game.Move:  # Gets called in normal gameplay to determine the player's move
        raise NotImplementedError

    def tile(self, validator: Callable[[game.MoveOver], Tuple[bool, game.Error]]) -> List[game.MoveOver]:  # Gets called in advanced gameplay to determine how the player moves over their tiles onto the panel
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
    
    def play(self, validator):
        assert self.game_state is not None, f"Player {self.player_id} has not been updated yet"
        assert self.game_state.turn == self.player_id, f"It is Player {self.game_state.turn}'s turn, not Player {self.player_id}'s"
        while True:
            source_id = self.prompt_validate("Source (batch number or 0 for bench):  ", int, lambda x: x >= 0 and x <= game.SETTINGS.N_BATCHES[self.n_players])
            tile = self.prompt_validate("Tile type (first letter or full name): ", game.Tile.from_symbol, lambda x: x in game.Tile.color_tiles())
            dest_id = self.prompt_validate("Destination (stage # or 0 for floor):  ", int, lambda x: x >= 0 and x <= game.SETTINGS.ROWS)
            print(f"Proposed move: {tile.name} from {f'Batch {source_id}' if source_id > 0 else 'Bench'} to {f'Stage {dest_id}' if dest_id > 0 else 'Floor'}")
            if validator(game.Move(self.player_id, tile, source_id, dest_id)): print("This move is valid.")
            else:
                print("Invalid move; please try again.")
                continue
            if self.prompt_validate("Confirm move (y for yes or n for no):  ", str, lambda x: x == "y" or x == "n") == "y":
                print()
                return game.Move(self.player_id, tile, source_id, dest_id)
    
    def tile(self, validator):
        raise NotImplementedError("Need to write this part still")

    
    def prompt_validate(self, msg, mutator, validator):
        while True:
            val = self.multiple_input(f"P{self.player_id}: {msg}")
            try:
                val = mutator(val)
            except ValueError:
                print("Invalid input type; please try again:")
                continue
            if validator(val): return val
            else: print("Invalid input value; please try again:")
    
    input_buffer = []  # For testing, we want to be able to enter in a lot of inputs at once and have this input be directed to multiple instances; later, we may want to make this instance-specific
    @classmethod
    def multiple_input(cls, prompt, allow_multiple=True):
        if not allow_multiple:
            return input(prompt)
        if len(cls.input_buffer) > 0:
            print(True)
            result = cls.input_buffer.pop(0)
            print(prompt+"<"+str(result)+">")
            return result
        else:
            cls.input_buffer.extend(input(prompt).split())
            return cls.input_buffer.pop(0)
