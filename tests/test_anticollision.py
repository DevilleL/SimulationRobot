"""Tests de l'anticollision (capteurs de proximité simulés)."""
from src.robot import Robot
from src.world import World


def test_glisse_le_long_de_l_obstacle():
    w = World([(1.2, 0.0, 0.25)])          # obstacle droit devant
    r = Robot(world=w)
    t, dt = 0.0, 0.02
    min_clear = 999.0
    avoided = False
    for _ in range(1500):                   # 30 s : on pousse vers l'obstacle en continu
        t += dt
        r.command(0.6, 0.0, t)
        tel = r.step(dt, t)
        dist_surface = ((r.pose[0] - 1.2) ** 2 + r.pose[1] ** 2) ** 0.5 - 0.25
        min_clear = min(min_clear, dist_surface)
        if tel["avoid"]:
            avoided = True
    assert avoided                          # l'évitement s'est déclenché
    assert min_clear > 0.05                 # n'a jamais pénétré l'obstacle (garde la distance)
    assert abs(r.pose[1]) > 0.1             # a glissé latéralement (contournement)


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
