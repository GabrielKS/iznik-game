from enum import Enum
import dataclasses
from dataclasses import dataclass, field
import typing
from collections import Counter, namedtuple
import random


class Tile(Enum):
    def __init__(self, value, label, iscolor):
        self._value_ = value
        self.label = label.upper()
        self.iscolor = iscolor

    FIRST = (-1, "-1", False)
    NONE = (0, "_", False)
    AZUL = (1, "A", True)
    BLAZE = (2, "B", True)
    CRIMSON = (3, "C", True)
    DUSK = (4, "D", True)
    ETHER = (5, "E", True)

    @classmethod
    def color_tiles(cls):
        return (tile for tile in cls if tile.iscolor)
    
    @classmethod
    def from_label(cls, label):
        for tile in cls:
            if tile.label == label:
                return tile
    
    def __str__(self):
        return self.label

Settings = namedtuple("Settings", ("ROWS", "COLS", "INVENTORY", "PENALTIES", "BASIC_PATTERN", "N_BATCHES", "TILES_PER_BATCH"))
SETTINGS = Settings(
    ROWS=5,
    COLS=5,
    INVENTORY={color: 20 for color in Tile.color_tiles()},
    PENALTIES=(-1, -1, -2, -2, -2, -3, -3),
    BASIC_PATTERN=[[Tile.from_label(c) for c in row] for row in ["ABCDE", "EABCD", "DEABC", "CDEAB", "BCDEA"]],
    N_BATCHES={2: 5, 3: 7, 4: 9},
    TILES_PER_BATCH=4
    )

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
            line = "\n"
            line += " "*(SETTINGS.ROWS-row+1)
            line += str(self.stage_contents[row])*(row+1)
            line += " -> "
            line += "".join([(str(tile) if tile.iscolor else (str(Tile.NONE) if self.advanced else SETTINGS.BASIC_PATTERN[row][col].label.lower())) for col, tile in enumerate(self.panel[row])])
            result += line
        penalties_values = "\n"
        penalties_tiles = "\n"
        for p in range(max(len(SETTINGS.PENALTIES), len(self.floor))):
            if p > 0:
                penalties_values += " "
                penalties_tiles += " "
            penalty_value = str(SETTINGS.PENALTIES[p]) if p < len(SETTINGS.PENALTIES) else "-0"
            penalty_tile = str(self.floor[p] if p < len(self.floor) else Tile.NONE)
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
    bench: typing.Counter[Tile] = field(default_factory=lambda: Counter({**{color: 0 for color in Tile.color_tiles()}, Tile.FIRST: 1}))

    # Hidden with default
    supply: typing.Optional[typing.Counter[Tile]] = field(default_factory=lambda: Counter(SETTINGS.INVENTORY))
    discard: typing.Optional[typing.Counter[Tile]] = field(default_factory=lambda: Counter({color: 0 for color in Tile.color_tiles()}))

    def __post_init__(self):
        self.player_boards = [PlayerState(self.advanced) for i in range(self.n_players)]
        self.batches = [Counter({color: 0 for color in Tile.color_tiles()}) for i in range(SETTINGS.N_BATCHES[self.n_players])]
    
    @property
    def visible(self):
        print(dataclasses.fields(self)[2])
        return dataclasses.replace(self, random_state=None, supply=None, discard=None)
    
    @staticmethod
    def _format_tile_list(tiles, separator=" "):
        return "["+separator.join([t.label for t in tiles])+"]"

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
            contents = list(self.batches[i].elements())
            contents += [Tile.NONE]*(SETTINGS.TILES_PER_BATCH-len(contents))
            result += f"\nBatch {i+1}: "+self._format_tile_list(contents)
        result += "\nBench: "+self._format_tile_list(self.bench.elements())
        if self.supply is not None or self.discard is not None: result += "\n"
        if self.supply is not None: result += "\nSupply: "+self._format_tile_list(self.supply.elements(), separator="")
        if self.discard is not None: result += "\nDiscard: "+self._format_tile_list(self.discard.elements(), separator="")
        if self.random_state is not None: result += "\n\nHash of random state: "+str(hash(self.random_state))

        return result

class Game:
    def __init__(self, state: GameState):
        self._state = state
    
    @classmethod
    def empty_game(cls, n_players, advanced, random_seed=None):
        random_state = random.Random(random_seed).getstate()
        state = GameState(n_players, advanced, random_state)
        return cls(state)

def main():
    print(Game.empty_game(2, False)._state)

if __name__ == "__main__":
    main()