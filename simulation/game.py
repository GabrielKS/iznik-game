from enum import Enum
import dataclasses
from dataclasses import dataclass, field
import typing
from collections import Counter, namedtuple
import random
import hashlib


class Tile(Enum):
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
    
    def __str__(self):
        return self.name


Settings = namedtuple("Settings", ("ROWS", "COLS", "INVENTORY", "PENALTIES", "BASIC_PATTERN", "N_BATCHES", "TILES_PER_BATCH"))
SETTINGS = Settings(
    ROWS=5,
    COLS=5,
    INVENTORY={color: 20 for color in Tile.color_tiles()},
    PENALTIES=(-1, -1, -2, -2, -2, -3, -3),
    BASIC_PATTERN=[[Tile.from_symbol(c) for c in row] for row in ["ABCDE", "EABCD", "DEABC", "CDEAB", "BCDEA"]],
    N_BATCHES={2: 5, 3: 7, 4: 9},
    TILES_PER_BATCH=4
    )
Move = namedtuple("Move", ("player_id", "tile", "source_id", "dest_id"))

class Error(Exception):
    pass

class IllegalGameOperationError(Exception):
    def __init__(self, message):
        self.message = message

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
            line += "".join([(str(tile) if tile.iscolor else (str(Tile.NONE) if self.advanced else SETTINGS.BASIC_PATTERN[row][col].symbol.lower())) for col, tile in enumerate(self.panel[row])])
            result += line
        penalties_values = "\n"
        penalties_tiles = "\n"
        for p in range(max(len(SETTINGS.PENALTIES), len(self.floor))):
            if p > 0:
                penalties_values += " "
                penalties_tiles += " "
            penalty_value = str(SETTINGS.PENALTIES[p]) if p < len(SETTINGS.PENALTIES) else "-0"
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
    batches: typing.List[typing.Counter[Tile]] = None
    bench: typing.Counter[Tile] = field(default_factory=lambda: Counter())

    # Hidden with default
    supply: typing.Optional[typing.Counter[Tile]] = field(default_factory=lambda: Counter(SETTINGS.INVENTORY))
    discard: typing.Optional[typing.Counter[Tile]] = field(default_factory=lambda: Counter())

    def __post_init__(self):
        if self.player_boards is None: self.player_boards = [PlayerState(self.advanced) for i in range(self.n_players)]
        if self.batches is None: self.batches = [Counter({color: 0 for color in Tile.color_tiles()}) for i in range(SETTINGS.N_BATCHES[self.n_players])]
    
    def copy(self):
        return dataclasses.replace(self)

    def visible(self):
        return dataclasses.replace(self, random_state=None, supply=None, discard=None)
    
    @staticmethod
    def _format_tile_list(tiles, separator=" "):
        return "["+separator.join([t.symbol for t in tiles])+"]"
    
    @staticmethod
    def deterministic_hash(value):
        hasher = hashlib.sha1()
        hasher.update(repr(value).encode("utf-8"))
        return hasher.hexdigest()

    def __str__(self):
        result = f"Players: {self.n_players}"
        result += f"\nAdvanced: "+("yes" if self.advanced else "no")
        result += f"\nTurn: Player {self.turn}\n"
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
        for batch in self._state.batches:
            for _ in range(SETTINGS.TILES_PER_BATCH):
                if sum(self._state.supply.values()) <= 0:
                    print("Resupplying!")
                    self._resupply()
                batch[self._draw()] += 1
        self._state.bench[Tile.FIRST] += 1
    
    def play(self, player_id, tile, source_id, dest_id):
        if player_id != self._state.turn: raise IllegalGameOperationError(f"It is not Player {player_id}'s turn, it is Player {self._state.turn}'s turn'")
        self._state.turn = (self._state.turn + 1) % self._state.n_players
        player = self._state.player_boards[player_id]
        source = self._state.bench if source_id == 0 else self._state.batches[source_id-1]
        n_tiles = source[tile]
        if n_tiles == 0: raise IllegalGameOperationError("No tiles to take from "+("bench" if source_id == 0 else f"batch {source_id+1}"))
        source[tile] = 0
        if source_id == 0:
            if Tile.FIRST in source:
                source[Tile.FIRST] -= 1
                player.floor.append(Tile.FIRST)
        else:
            self._state.bench += source
            source.clear()
        if dest_id == 0:
            player.floor += [tile for i in range(n_tiles)]
        else:
            if player.stage_contents[dest_id-1] not in (tile, Tile.NONE): raise IllegalGameOperationError("Cannot add {tile} to stage of type {player.stage_contents[dest_id-1]}")
            if player.stage_fullnesses[dest_id-1]+n_tiles > dest_id:
                overflow = player.stage_fullnesses[dest_id-1]+n_tiles-dest_id
                player.floor += [tile for i in range(overflow)]
                n_tiles -= overflow
            player.stage_contents[dest_id-1] = tile
            player.stage_fullnesses[dest_id-1] += n_tiles
    
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
    g.play(0, Tile.CRIMSON, 1, 4)
    print(g)
    g.play(1, Tile.CRIMSON, 2, 0)
    print(g)
    g.play(0, Tile.DUSK, 0, 3)
    print(g)
    g.play(1, Tile.CRIMSON, 5, 1)
    print(g)



if __name__ == "__main__":
    main()