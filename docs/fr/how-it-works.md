## ⚙️ Comment ça marche

Cette section décrit le flux de données de bout en bout et les boucles de contrôle pour le **Mode Manuel** et le **Mode Automatique**, comme résumé dans la **Figure 1**. L’architecture suit un cycle **percevoir → interpréter → commander → agir**, où le **PC portable** fournit les modules de perception/décision et l’**ESP32** exécute l’actionnement bas niveau.

<p align="center">
  <img src="src/figure,1.png" alt="Figure 1. Architecture et flux de données pour les modes manuel et automatique." />
</p>

**Figure 1.** Architecture système et flux de données de l’Auto Soccer Bot (ESP32) en modes manuel et automatique.

---

## Table des matières

- [1) Contrôle manuel (téléopération par gestes)](#1-contrôle-manuel-téléopération-par-gestes)
- [2) Mode automatique (vision dans la boucle)](#2-mode-automatique-vision-dans-la-boucle)
- [Responsabilités des composants](#responsabilités-des-composants)

---

### 1) Contrôle manuel (téléopération par gestes)

**Objectif.** Permettre à l’utilisateur de piloter le robot avec des gestes de la main capturés par la webcam du PC.

**Chaîne de traitement.**
1. **Acquisition — Webcam du PC.** Des images RGB sont capturées à la résolution native et transmises au processus local.
2. **Perception — Détection & classification de gestes.** Chaque image est prétraitée puis passée dans le pipeline de gestes pour inférer une classe de commande (p. ex. *forward*, *left*, *right*, *backward*, *stop*).
3. **Décision/Encodage — Encodeur de commande.** Le geste prédit est mappé en primitives de mouvement (consignes linéaires/angulaires) et encodé en requêtes HTTP.
4. **Actionnement — Robot ESP32.** Les commandes sont envoyées via **Wi-Fi/HTTP** vers l’ESP32, qui parse la charge utile et met à jour les PWM moteurs via le pont en H.

**Remarques.**
- Cette boucle est **entièrement implémentée** et tourne en temps réel sur des PC grand public.
- Communication sans état (request/response) ; limitation de débit et anti-rebond côté PC pour éviter la saturation.

<p align="center">
  <img src="../src/picture1.jpg" alt="Figure 2. Exemple de points clés de la main et superposition pour le contrôle manuel." />
</p>

**Figure 2.** Superposition issue du pipeline de gestes montrant les points clés détectés pour la téléopération.

---

### 2) Mode automatique (vision dans la boucle)

**Objectif.** Boucler perception→commande à l’aide d’une pile de vision sur le PC alimentée par le flux de l’ESP32-CAM.

**Chaîne de traitement.**
1. **Acquisition — ESP32-CAM (flux vidéo).** L’ESP32-CAM expose un flux MJPEG (ou équivalent) via le Wi-Fi.
2. **Perception — Pipeline de vision sur PC.** Le PC s’abonne au flux et effectue la détection d’objets pour localiser :
   - **Balle** — ✓ implémenté (détecteur opérationnel dans la boucle).
   - **But (Goal)** — **modèle entraîné et disponible** dans [`soccer_vision`](soccer_vision.md), **pas encore câblé** dans la boucle en direct.
   - **Adversaire** — **modèle entraîné et disponible** dans [`soccer_vision`](soccer_vision.md), **pas encore câblé** dans la boucle en direct.
3. **Décision — Contrôleur / automate d’états.**
   - **Suivi de balle** — ✓ implémenté (tourner/avancer selon la pose image de la balle).
   - **Fusion multi-objets** (balle + but + adversaire) — ✗ non implémenté ; l’automate minimal actuel ignore but/adversaire bien que les modèles existent.
4. **Actionnement — Robot ESP32.** Le mouvement choisi est encodé en commandes HTTP et transmis à l’ESP32, qui met à jour les sorties moteur.

**Remarques.**
- L’autonomie actuelle est un **suivi mono-cible** (balle). Les détecteurs de but/adversaire sont entraînés (voir [`soccer_vision.md`](soccer_vision.md)) mais **non intégrés** ; des fonctions comme l’alignement de tir ou l’évitement de collision restent à venir.
- Perception et actionnement sont découplés, ce qui permet d’ajouter plus tard les crochets but/adversaire dans l’automate sans changer le firmware.

<p align="center">
  <img src="../src/picture2.jpg" alt="Figure 3. Détection de la balle et état du contrôleur en mode automatique." />
</p>

**Figure 3.** Instance du détecteur de balle et état du contrôleur en fonctionnement automatique (la ligne verticale gauche marque le centre de l’image ; ‘Cmd’ affiche la commande émise).

---

### Responsabilités des composants

| Couche        | Composant                  | Responsabilité                                                                                           | Statut                      |
|---------------|----------------------------|-----------------------------------------------------------------------------------------------------------|-----------------------------|
| Acquisition   | ESP32-CAM / Webcam du PC   | Capture vidéo                                                                                            | ✓                           |
| Perception    | Pipeline de vision (PC)    | **En direct :** balle (✓). **Modèles disponibles :** but (✓), adversaire (✓) — **intégration À FAIRE**   | Partiel                     |
| Décision      | Contrôleur sur PC          | Suivi de balle (✓). Fusion multi-objets avec but/adversaire (✗, modèles existants non câblés)            | Partiel                     |
| Communication | Wi-Fi/HTTP                 | Transport des commandes (PC → ESP32)                                                                     | ✓                           |
| Actionnement  | Firmware du robot ESP32    | Parser les commandes ; contrôle PWM des moteurs                                                          | ✓                           |

**Légende :** ✓ Terminé ✗ Non implémenté **À FAIRE** À intégrer
