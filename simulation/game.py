from enum import Enum
import dataclasses
from dataclasses import dataclass, field
import typing
from collections import namedtuple
import random
import hashlib

debug = False

class multiint(int): # Hack to allow my Tiles to asdict properly in dataclasses
    def __new__(cls, *args):
        return int.__new__(cls, args[0])
    
    def __deepcopy__(self, memo):  # Deep copying an int (or an enum) should result in the same thing, as it is not mutable
        return self

class DCounter(typing.Counter):  # Hack to allow my Counters to asdict properly in dataclasses
    def __init__(self, iterable=None, /, **kwds):
        if iterable is not None:
            d = dict(iterable)  # Without this line, line 1112 of dataclasses.py does the wrong thing
            super().__init__(d)
        else: super().__init__(kwds)

class Tile(multiint, Enum):
    def __init__(self, value, name, symbol, iscolor):
        self._value_ = value
        self._name_ = name
        self.symbol = symbol
        self.iscolor = iscolor

    FIRST = (-1, "First player", "-1", False)
    NONE = (0, "NONE", "_", False)
    AZUL = (1, "Azul", "A", True)
    BLAZE = (2, "Blaze", "B", True)
    CRIMSON = (3, "Crimson", "C", True)
    DUSK = (4, "Dusk", "D", True)
    ETHER = (5, "Ether", "E", True)

    @classmethod
    def color_tiles(cls):
        return (tile for tile in cls if tile.iscolor)
    
    @classmethod
    def names(cls):
        return (tile.name for tile in cls)
    
    @classmethod
    def symbols(cls):
        return (tile.symbol for tile in cls)
    
    @classmethod
    def from_symbol(cls, symbol):
        for tile in cls:
            if tile.symbol.casefold() == symbol.casefold():  # casefold to ignore case
                return tile
    
    def __str__(self):  # It does too return a string! pylint:disable=invalid-str-returned
        return self.name
    
class Direction(Enum):
    LEFT = 1
    UP = 2
    RIGHT = 3
    DOWN = 4


Settings = namedtuple("Settings", ("ROWS", "COLS", "INVENTORY", "PENALTIES", "BASIC_PATTERN", "N_BATCHES", "TILES_PER_BATCH", "BONUSES"))
SETTINGS = Settings(
    ROWS=5,
    COLS=5,
    INVENTORY={color: 20 for color in Tile.color_tiles()},
    PENALTIES=(1, 1, 2, 2, 2, 3, 3),
    BASIC_PATTERN=[[Tile.from_symbol(c) for c in row] for row in ["ABCDE", "EABCD", "DEABC", "CDEAB", "BCDEA"]],
    N_BATCHES={2: 5, 3: 7, 4: 9},
    TILES_PER_BATCH=4,
    BONUSES=namedtuple("Bonuses", ("HORIZONTAL", "VERTICAL", "COLOR"))(HORIZONTAL=2, VERTICAL=5, COLOR=10)
    )
Move = namedtuple("Move", ("player_id", "tile", "source_id", "dest_id"))
MoveOver = namedtuple("MoveOver", ("player_id", "source_id", "dest_id"))

class Error(Exception):
    def __init__(self, message):
        self.message = message

class IllegalGameOperationError(Error):
    pass

class ImpossibleGameFlowError(Error):
    pass

@dataclass
class PlayerState:
    advanced: bool
    score: int = 0
    stage_contents: typing.List[Tile] = field(default_factory=lambda: [Tile.NONE for i in range(SETTINGS.ROWS)])
    stage_fullnesses: typing.List[int] = field(default_factory=lambda: [0 for i in range(SETTINGS.ROWS)])
    panel: typing.List[typing.List[Tile]] = field(default_factory=lambda: [[Tile.NONE for j in range(SETTINGS.COLS)] for i in range(SETTINGS.ROWS)])
    floor: typing.List[Tile] = field(default_factory=lambda: [])

    def __str__(self):
        result = f"{self.score}"
        for row in range(SETTINGS.ROWS):
            line = "\n  "
            line += " "*(SETTINGS.ROWS-row-1)
            line += Tile.NONE.symbol*(row+1-self.stage_fullnesses[row])  # pylint: disable=no-member
            line += self.stage_contents[row].symbol*(self.stage_fullnesses[row])
            line += " -> "
            line += "".join([(tile.symbol if tile.iscolor else (str(Tile.NONE) if self.advanced else SETTINGS.BASIC_PATTERN[row][col].symbol.lower())) for col, tile in enumerate(self.panel[row])])
            result += line
        penalties_values = "\n"
        penalties_tiles = "\n"
        for p in range(max(len(SETTINGS.PENALTIES), len(self.floor))):
            if p > 0:
                penalties_values += " "
                penalties_tiles += " "
            penalty_value = str(-SETTINGS.PENALTIES[p]) if p < len(SETTINGS.PENALTIES) else "-0"
            penalty_tile = (self.floor[p] if p < len(self.floor) else Tile.NONE).symbol
            penalties_values += penalty_value
            penalties_tiles += (" "*(len(penalty_value)-len(penalty_tile)))+penalty_tile
        result += penalties_values
        result += penalties_tiles
        return result


@dataclass
class GameState:
    # Public no default
    n_players: int
    advanced: bool

    # Hidden no default
    random_state: typing.Optional[object]

    # Public with default
    turn: int = 0
    player_boards: typing.List[PlayerState] = None
    batches: typing.List[DCounter[Tile]] = None
    bench: DCounter[Tile] = field(default_factory=lambda: DCounter())

    # Hidden with default
    supply: typing.Optional[DCounter[Tile]] = field(default_factory=lambda: DCounter(SETTINGS.INVENTORY))
    discard: typing.Optional[DCounter[Tile]] = field(default_factory=lambda: DCounter())

    def __post_init__(self):
        if self.player_boards is None: self.player_boards = [PlayerState(self.advanced) for i in range(self.n_players)]
        if self.batches is None: self.batches = [DCounter({color: 0 for color in Tile.color_tiles()}) for i in range(SETTINGS.N_BATCHES[self.n_players])]
    
    def copy(self):
        return dataclasses.replace(self)

    def visible(self):
        return dataclasses.replace(self, random_state=None, supply=None, discard=None)
    
    @staticmethod
    def _format_tile_list(tiles, separator=" "):
        tiles = [t for t in tiles]
        tiles.sort(key=(lambda t: t.value))
        return "["+separator.join([t.symbol for t in tiles])+"]"
    
    @staticmethod
    def deterministic_hash(value):
        hasher = hashlib.sha1()
        hasher.update(repr(value).encode("utf-8"))
        return hasher.hexdigest()

    def __str__(self):
        result = ""
        if debug: result += f"Players: {self.n_players}\n"
        if debug: result += "Advanced: "+("yes\n" if self.advanced else "no\n")
        result += f"Turn: Player {self.turn}\n"
        player_strs = []
        for i, p in enumerate(self.player_boards):
            player_strs.append([f"Player {i}:"])
            player_strs[i].extend(str(p).split("\n"))
            width = max([len(line) for line in player_strs[i]])
            for j in range(len(player_strs[i])):
                player_strs[i][j] = player_strs[i][j].ljust(width)
        n_lines = max(len(strs) for strs in player_strs)
        for j in range(n_lines):
            result += "\n"+" | ".join([player_strs[i][j] for i in range(self.n_players)])
        result += "\n"
        for i, b in enumerate(self.batches):
            contents = list(b.elements())
            contents += [Tile.NONE]*(SETTINGS.TILES_PER_BATCH-len(contents))
            result += f"\nBatch {i+1}: "+self._format_tile_list(contents)
        result += "\nBench:   "+self._format_tile_list(self.bench.elements())
        if self.supply is not None or self.discard is not None: result += "\n"
        if self.supply is not None: result += "\nSupply: "+self._format_tile_list(self.supply.elements(), separator="")
        if self.discard is not None: result += "\nDiscard: "+self._format_tile_list(self.discard.elements(), separator="")
        if self.random_state is not None: result += "\n\nHash of random state: "+str(self.deterministic_hash(self.random_state))

        return result
    
    @property
    def winners(self):
        if self.turn >= 0: return []
        scores = [board.score for board in self.player_boards]
        top_score = max(scores)
        return [i for i, score in enumerate(scores) if score == top_score]


class Game:
    def __init__(self, state: GameState):
        self._state = state
    
    @classmethod
    def _empty_game(cls, n_players, advanced, random_seed=None):
        random_state = random.Random(random_seed).getstate()
        state = GameState(n_players, advanced, random_state)
        return cls(state)
    
    @classmethod
    def new_game(cls, n_players, advanced, random_seed=None):
        game = cls._empty_game(n_players, advanced, random_seed)
        game._craft()
        return game
    
    def _resupply(self):
        self._state.supply += self._state.discard
        self._state.discard.clear()
    
    def _draw(self):
        rgen = random.Random()
        rgen.setstate(self._state.random_state)
        supply_elements = list(self._state.supply.elements())
        tile = supply_elements[rgen.randrange(len(supply_elements))]
        self._state.supply[tile] -= 1
        self._state.random_state = rgen.getstate()
        return tile

    def _craft(self):
        self._state.bench[Tile.FIRST] += 1
        for batch in self._state.batches:
            for _ in range(SETTINGS.TILES_PER_BATCH):
                if sum(self._state.supply.values()) == 0:
                    if sum(self._state.discard.values()) == 0:  # Discard is empty -> cannot resupply
                        return
                    else:
                        self._resupply()
                batch[self._draw()] += 1
    
    def play(self, move):
        valid, error = self.check(move)
        if not valid: raise error
        self._state.turn = (self._state.turn + 1) % self._state.n_players
        player = self._state.player_boards[move.player_id]
        source = self._state.bench if move.source_id == 0 else self._state.batches[move.source_id-1]
        n_tiles = source[move.tile]
        source[move.tile] = 0
        if move.source_id == 0:
            if source[Tile.FIRST] > 0:
                source[Tile.FIRST] -= 1
                player.floor.append(Tile.FIRST)
        else:
            self._state.bench += source
            source.clear()
        if move.dest_id == 0:
            player.floor += [move.tile for i in range(n_tiles)]
        else:
            if player.stage_fullnesses[move.dest_id-1]+n_tiles > move.dest_id:
                overflow = player.stage_fullnesses[move.dest_id-1]+n_tiles-move.dest_id
                player.floor += [move.tile for i in range(overflow)]
                n_tiles -= overflow
            player.stage_contents[move.dest_id-1] = move.tile
            player.stage_fullnesses[move.dest_id-1] += n_tiles
        
        if self._tiling_finished():
            self._end_round()
    
    def check(self, move):
        if move.player_id != self._state.turn: return False, IllegalGameOperationError(f"It is player {self._state.turn}'s turn, not Player {move.player_id}'s.")
        if (self._state.bench if move.source_id == 0 else self._state.batches[move.source_id-1])[move.tile] == 0: return False, IllegalGameOperationError(f"No {move.tile} in {self.format_source(move.source_id, capitalize=True)}.")
        if move.dest_id > 0:
            player = self._state.player_boards[move.player_id]
            if move.tile in player.panel[move.dest_id-1]: return False, IllegalGameOperationError(f"Panel row {move.dest_id} already contains {move.tile}.")
            if player.stage_contents[move.dest_id-1] not in (move.tile, Tile.NONE): return False, IllegalGameOperationError(f"Cannot add {move.tile} to {player.stage_contents[move.dest_id-1]} stage.")
        return True, ImpossibleGameFlowError("This error should not be thrown")
    
    def _game_over(self):
        for player in self._state.player_boards:
            for row in player.panel:
                if all([tile.iscolor for tile in row]):
                    return True
        return False
    
    def _tiling_finished(self):
        return all([sum(batch.values()) == 0 for batch in self._state.batches]) and (sum(self._state.bench.values()) == 0)
    
    def _end_round(self):
        first_player = -1
        for i, player in enumerate(self._state.player_boards):
            if Tile.FIRST in player.floor:
                first_player = i
                break
        assert first_player >= 0
        
        self._score_round()
        if self._game_over():
            self._score_bonuses()
            self._state.turn = -1
            return
        self._craft()

        self._state.turn = first_player

    def _score_round(self):  # Move over and discard tiles and score points
        for player in self._state.player_boards:
            # Move tiles over
            for row in range(SETTINGS.ROWS):
                content = player.stage_contents[row]
                fullness = player.stage_fullnesses[row]
                if fullness == row+1:  # Stage is full
                    if player.advanced:
                        raise NotImplementedError("Need to write this part still")
                        # dest_id = something
                    else:
                        dest_id = SETTINGS.BASIC_PATTERN[row].index(content)+1
                    if dest_id == 0:
                        player.floor.extend([content for i in range(fullness)])
                        player.stage_fullnesses[row] = 0
                        player.stage_contents[row] = Tile.NONE
                    else:
                        player.panel[row][dest_id-1] = content
                        player.score += self._score_tile(player.panel, row, dest_id-1)
            
            # Score the floor
            for i in range(min(len(player.floor), len(SETTINGS.PENALTIES))):
                player.score -= SETTINGS.PENALTIES[i]
        
        # Status update (TODO: decide how I want to do this within the Player framework)
        # print("ROUND END AFTER SCORING BEFORE DISCARD:")
        # print(self.view)
            
        # Discard and clear
        for player in self._state.player_boards:
            for row in range(SETTINGS.ROWS):
                fullness = player.stage_fullnesses[row]
                if fullness == row+1:
                    player.stage_fullnesses[row] = 0
                    player.stage_contents[row] = Tile.NONE
                    self._state.discard[content] += fullness-1  # We discard all of the tiles but the one going onto the panel
            for tile in player.floor:
                self._state.discard[tile] += 1
            player.floor = []
    
    @classmethod
    def _score_tile(cls, panel, row, col):
        assert panel[row][col] is not Tile.NONE
        extents = {direction: cls._contiguous(panel, row, col, direction) for direction in Direction}
        horizontal = extents[Direction.LEFT]+extents[Direction.RIGHT]-1  # We count the active tile in each direction and only want it counted once
        vertical = extents[Direction.UP]+extents[Direction.DOWN]-1
        return horizontal+vertical-(1 if (horizontal == 1 or vertical == 1) else 0)  # If there are linkages in both directions, just add them up. If there are linkages in only one or none of the directions, subtract one from this sum.

    @classmethod
    def _contiguous(cls, panel, row, col, direction):  # Recursively determines how many tiles are non-NONE in a particular direction
        if row < 0 or row >= SETTINGS.ROWS or col < 0 or col >= SETTINGS.COLS: return 0
        if panel[row][col] is Tile.NONE: return 0
        movers = {Direction.LEFT: lambda row, col: (row, col-1),
                 Direction.RIGHT: lambda row, col: (row, col+1),
                 Direction.UP: lambda row, col: (row-1, col),
                 Direction.DOWN: lambda row, col: (row+1, col)}
        return 1 + cls._contiguous(panel, *movers[direction](row, col), direction)
    
    def _score_bonuses(self):
        for player in self._state.player_boards:
            for row in player.panel:
                if all([tile is not Tile.NONE for tile in row]):  # player has a horizontal line
                    player.score += SETTINGS.BONUSES.HORIZONTAL
            for col in range(SETTINGS.COLS):
                if all([player.panel[i][col] is not Tile.NONE for i in range(SETTINGS.ROWS)]):  # player has a vertical line
                    player.score += SETTINGS.BONUSES.VERTICAL
            for tile in Tile.color_tiles():
                if sum([row.count(tile) for row in player.panel]) == min(SETTINGS.ROWS, SETTINGS.COLS):  # player has all possible tiles of a given color (in a theoretical game where ROWS!=COLS, the maximum possible amount of each color is min(ROWS, COLS))
                    player.score += SETTINGS.BONUSES.COLOR
    
    @staticmethod
    def format_source(source_id, capitalize=False):
        if source_id > 0:
            return ("Batch " if capitalize else "batch ")+str(source_id)
        else:
            return "Bench" if capitalize else "bench"

    @staticmethod
    def format_dest(dest_id, capitalize=False):
        if dest_id > 0:
            return ("Stage " if capitalize else "stage ")+str(dest_id)
        else:
            return "Floor" if capitalize else "floor"
    
    @property
    def state(self):
        return self._state.copy()

    @property
    def view(self):
        return self._state.visible()

    def __str__(self):
        return str(self._state)

def main():
    g = Game._empty_game(2, False, random_seed=0)
    g._state.supply[Tile.BLAZE] = 0
    g._state.discard[Tile.BLAZE] += 1
    # print(g)
    g._resupply()
    # print(g)
    print(g._draw())
    # print(g)
    g._craft()
    print(g)
    g.play(Move(0, Tile.CRIMSON, 1, 4))
    print(g)
    g.play(Move(1, Tile.CRIMSON, 2, 0))
    print(g)
    g.play(Move(0, Tile.DUSK, 0, 3))
    print(g)
    g.play(Move(1, Tile.CRIMSON, 5, 1))
    print(g)


if __name__ == "__main__":
    main()