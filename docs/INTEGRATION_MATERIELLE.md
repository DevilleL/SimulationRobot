# Check-list d'intégration matérielle — locomotion POCAA (S36)

Procédure à suivre **à la livraison du matériel** pour passer de la simulation au
robot réel, dans l'ordre, en testant à chaque étape. À cocher au fur et à mesure.

Matériel concerné (BOM) : Raspberry Pi 4, ESP32 DevKit v1, contrôleur pont en H,
2 moteurs DC 12 V + encodeurs, régulateurs (12 V→5 V buck, R-78E3.3), alimentation.

---

## 1. Avant tout branchement
- [ ] Vérifier visuellement chaque carte (pas de court-circuit, condensateurs OK).
- [ ] Repérer les broches de l'ESP32 utilisées (voir `firmware/config.py`).
- [ ] Préparer un **bouton d'arrêt d'urgence** coupant l'alim des moteurs.
- [ ] Avoir un **multimètre** sous la main.

## 2. Alimentation (le plus critique)
- [ ] Brancher l'alim 12 V vers le pont en H (moteurs) **uniquement**.
- [ ] Régulateur **12 V → 5 V** (buck) pour le Raspberry Pi ; vérifier 5 V ± 0,1 V **à vide** avant de brancher le Pi.
- [ ] Régulateur **3,3 V** (R-78E3.3) pour l'ESP32 si non alimenté en USB.
- [ ] **Masse commune** entre alim moteurs, ESP32 et Pi (GND relié) — indispensable pour les signaux.
- [ ] Ne **jamais** alimenter les moteurs par les régulateurs logiques.

## 3. Moteurs + ponts en H
- [ ] Câbler moteur gauche/droite sur les sorties du pont en H.
- [ ] Relier `ENA/ENB` (PWM) et `IN1..IN4` (sens) aux GPIO de l'ESP32 selon `config.py` :
  - Gauche : PWM=25, IN1=26, IN2=27
  - Droite : PWM=32, IN1=33, IN2=14
- [ ] Vérifier que le pont en H est bien alimenté en 12 V (et sa logique en 5 V).

## 4. Encodeurs
- [ ] Câbler les voies A/B des encodeurs sur les GPIO de `config.py` :
  - Gauche : A=34, B=35  •  Droite : A=36, B=39
- [ ] Alimenter les encodeurs en 3,3 V (⚠️ ne pas mettre 5 V sur une entrée ESP32).
- [ ] Vérifier `ENCODER_TICKS_PER_REV` (2048) vs la fiche réelle de l'encodeur.

## 5. Liaison Raspberry Pi ↔ ESP32
- [ ] Relier l'ESP32 au Pi en **USB** (le plus simple → série REPL), ou en **UART** (TX/RX croisés + GND).
- [ ] Si UART : adapter `main.py` pour utiliser `machine.UART` au lieu de `sys.stdin`.

## 6. Flash du firmware
- [ ] Installer MicroPython sur l'ESP32 (voir `firmware/README.md`).
- [ ] Copier `config.py`, `pid.py`, `main.py` sur la carte.
- [ ] Vérifier que `main.py` démarre au boot.

## 7. Tests progressifs (sécurité avant tout)
- [ ] **Roues en l'air** (robot sur cale) : envoyer `{"v":0.2,"w":0}` → les deux roues tournent **vers l'avant**.
  - [ ] Si une roue tourne à l'envers → inverser `in1`/`in2` de ce moteur dans `config.py`.
- [ ] Vérifier que les **encodeurs comptent dans le bon sens** (valeur croissante en marche avant).
  - [ ] Sinon, inverser la lecture `b.value()` dans `Encoder._on_edge`.
- [ ] Tester la **rotation** : `{"v":0,"w":1.0}` → roues en sens opposés.
- [ ] Couper l'envoi > 0,5 s → le **watchdog** arrête les moteurs.

## 8. Calibration de l'asservissement
- [ ] Mesurer l'**entraxe réel** des roues et le mettre dans `TRACK_WIDTH`.
- [ ] Mesurer la **vitesse roue max** réelle → ajuster `MOTOR_MAX_SPEED`.
- [ ] Repartir des gains PID de la simulation, puis affiner (`KP`, `KI`, `KD`) en observant la stabilité.
- [ ] Vérifier les **rampes** (pas d'à-coups) et le **bridage marche arrière** (30 %).

## 9. Mise au sol & sécurité
- [ ] Premiers déplacements **au sol, à vitesse réduite**, dans une zone dégagée.
- [ ] Vérifier la **trajectoire en ligne droite** (sinon recaler PID/gauche-droite).
- [ ] Vérifier le **centre de gravité bas** (pas de basculement à l'arrêt brusque).
- [ ] Valider l'**arrêt d'urgence** matériel.

## 10. Intégration avec le reste du système
- [ ] Le Pi envoie les commandes issues du relais/pilotage (même protocole `{"v","w"}`).
- [ ] Brancher le **dashboard de supervision** sur la télémétrie réelle (à terme, remonter les vitesses encodeurs depuis l'ESP32).
- [ ] Re-tester la chaîne complète : pilotage web → Pi → ESP32 → moteurs.
