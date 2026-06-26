"""Tests de l'anticollision (capteurs de proximité simulés)."""
from src.robot import Robot
from src.world import World


def test_arret_devant_obstacle():
    w = World([(1.2, 0.0, 0.25)])          # obstacle droit devant
    r = Robot(world=w)
    t, dt = 0.0, 0.02
    tel = None
    for _ in range(800):                    # 16 s
        t += dt
        r.command(0.6, 0.0, t)              # on fonce tout droit
        tel = r.step(dt, t)
    surface = 1.2 - 0.25                     # bord de l'obstacle = 0.95 m
    assert r.pose[0] < surface              # n'a pas pénétré l'obstacle
    assert r.pose[0] > 0.3                  # mais a bien avancé avant de s'arrêter
    assert tel["avoid"] is True             # l'évitement s'est déclenché


def test_pas_d_anticollision_sans_monde():
    r = Robot()                             # pas de monde -> capteurs inactifs
    tel = r.step(0.02, 0.02)
    assert tel["avoid"] is False
    assert tel["dmin"] == float("inf")


def test_marche_arriere_autorisee():
    w = World([(0.6, 0.0, 0.2)])            # obstacle proche devant
    r = Robot(world=w)
    t, dt = 0.0, 0.02
    for _ in range(200):                    # 4 s en marche arrière
        t += dt
        r.command(-0.2, 0.0, t)
        r.step(dt, t)
    assert r.pose[0] < 0.0                  # a reculé : l'anticollision n'a pas bloqué
