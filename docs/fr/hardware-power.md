# 🔌 Matériel & Alimentation — Guide d’électronique et de câblage

---

## Table des matières
- [Liste des composants](#list-of-components)
- [Schéma du circuit](#circuit-design-layout)
- [Connexions & topologie](#connections--topology)
- [Notes d’alimentation & sécurité](#power-notes--safety)
- [Éléments à compléter ultérieurement](#placeholders-to-fill-later)

---

## Liste des composants

### ESP32-CAM (AI-Thinker)
- **Rôle :** Caméra embarquée + Wi-Fi ; héberge les serveurs HTTP et les endpoints moteur.
- **Alimentation :** Entrée **5 V** (broche **5V**) ; pics typiques **~300–500 mA** avec caméra/LED.
<p align="center">
  <img src="../src/Pinlayout_ESPCam.jpg" alt="Brochage ESP32-CAM" width="520" />
</p>

### Pont en H double L298N (driver moteur)
- **Rôle :** Étape de puissance/niveau qui pilote deux moteurs DC et distribue l’énergie de la batterie.
- **Alimentation (Vs) :** **3.3 V lithium** (voir notes d’alimentation ci-dessous).
- **Logique :** 5 V (depuis le régulateur intégré du L298N ou une source 5 V externe).

> **Remarque :** De nombreuses cartes L298N attendent **Vs ≥ 5–7 V** pour une fiabilité correcte. Si vous devez rester en **3.3 V**, envisagez un **convertisseur boost** vers 5–7.4 V **ou** un **driver basse tension** (ex. TB6612FNG) à la place du L298N.

### Deux moteurs DC avec réducteur
- **Tension nominale :** **6 V**
- **Vitesse à vide :** **≈ 360 rpm**
- **Ø arbre :** **3 mm**
- **Ø moteur :** **12 mm**
- **Longueur du corps (sans arbre) :** **≈ 26 mm**
- **Longueur axiale de l’arbre de sortie :** **≈ 10 mm** (méplat ~**4.4 mm**)
- **Couple de blocage (stall) :** **≈ 16 kgf·cm**
- **Couple en fonctionnement :** **≈ 2 kgf·cm**
- **Poids du produit :** **≈ 0.010 kg**
- **Taille du moteur :** **≈ 36 × 12 mm**
- **Taille de l’arbre :** **≈ 3 × 2.5 mm** (D × L)

### Bloc batterie
- **Chimie / Tension :** **Lithium, 3.3 V** (capacité inconnue / non spécifiée)
- **Interrupteur général :** **Interrupteur en ligne** commandant l’**entrée d’alimentation (Vs) du L298N**.

---

## Schéma du circuit

<p align="center">
  <img src="../src/circuit_overview.png" alt="Vue d’ensemble : ESP32-CAM, L298N, batterie, moteurs" width="640" />
  <br><em>Figure A — Vue d’ensemble du circuit</em>
</p>

<p align="center">
  <img src="../src/wiring_diagram.jpeg" alt="Schéma de câblage : connexions broche à broche et rails d’alimentation" width="640" />
  <br><em>Figure B — Schéma de câblage</em>
</p>

---

## Connexions & topologie

- La **batterie (3.3 V lithium)** alimente le **Vs du L298N** via l’**interrupteur général**.
- Les **deux moteurs DC** se connectent sur **OUT1/OUT2** et **OUT3/OUT4** du L298N.
- L’**ESP32-CAM** relie ses **GPIO de contrôle moteur** aux **IN1…IN4** du L298N (et **ENA/ENB** si PWM activé).
- **Masses :** Une **masse commune (GND)** doit être partagée entre **batterie, L298N et ESP32-CAM**.
- L’**ESP32-CAM** est alimentée en **5 V** via sa **broche 5V**.

---

## Notes d’alimentation & sécurité

- **Batterie 3.3 V → L298N :** Le L298N est généralement peu performant sous 5 V. Pour de meilleurs résultats :
  - Utilisez un **convertisseur boost** (3.3 V → 5–7.4 V) pour **Vs**, **ou**
  - Remplacez par un **driver basse tension/faible chute** (ex. **TB6612FNG**, DRV8833).
- **Rail 5 V de l’ESP32-CAM :** Assurez une **alimentation 5 V stable** capable de fournir **≥ 500 mA** en pics (caméra + Wi-Fi + LED).
- La **masse commune** est indispensable pour éviter un pilotage moteur erratique.
- Ajoutez un **fusible en ligne** et une **section de câble** adaptée sur la ligne batterie si vous passez plus tard à des packs à plus forte intensité.