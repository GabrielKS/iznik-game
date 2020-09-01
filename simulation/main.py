from simulation import game
from simulation import player
from simulation import controller
import dataclasses
import collections


def main():
    g = game.Game.new_game(2, False, random_seed=0)
    p0 = player.TextInputPlayer(0, 2, True)
    p1 = player.TextInputPlayer(1, 2, False)
    c = controller.Controller(g, [p0, p1])
    while not c.game_over:
        c.step()


if __name__ == "__main__":
    main()