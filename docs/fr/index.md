# Auto Soccer Bot — Robot Foot à base d’ESP32 🤖⚽️

[English](../../README.md) · [Español](../es/index.md) · [Français](#)

> Robot à base d’ESP32 qui joue au football en **deux modes** — **manuel** via gestes de la main et **automatique** avec suivi du ballon grâce à la vision sur l’ordinateur.

---

## 🇫🇷 Français

### Introduction
Ce projet est un **robot foot contrôlé par un ESP32**. Il fonctionne en deux modes :

- **Contrôle manuel** — Une webcam sur l’ordinateur détecte les **gestes de la main** ; l’ordinateur interprète le geste et **envoie des commandes à l’ESP32** pour piloter le robot.  
<br>
- **Mode automatique** — L’ESP32-CAM diffuse la vidéo vers un ordinateur qui effectue la **détection d’objets** (ballon, but, adversaire) et **renvoie des commandes de mouvement** (avant, gauche, droite, arrière) au robot.

> **Statut actuel :** Nous avons achevé le **suivi du ballon** (détection + prise de décision) et entraîné un **détecteur d’adversaires**. Nous **n’avons pas** finalisé le **détecteur de but** ni la **fusion décisionnelle multi-objets** (adversaire + but).

---

## Table des matières

- 📚 **Documentation (multilingue)**
  - 🇬🇧 [Docs — EN](../../README.md)
  - 🇪🇸 [Docs — ES](../es/index.md)
  - 🇫🇷 [Docs — FR](#)
- 🧭 [**Fonctionnement**](#fonctionnement)
- 🗂️ **Structure du dépôt**
- 🧪 **Statut du projet**
- 🚀 **Démarrage rapide**
- ⚙️ **Composants**
  - Micrologiciel (ESP32-CAM) : [`/esp32cam_robot`](esp32cam_robot/README.md)
  - Contrôle manuel (gestes) : [`/manual_control`](manual_control/)
  - Mode automatique (vision + contrôle) : [`/auto_soccer_bot`](auto_soccer_bot/)
  - Entraînement du détecteur d’adversaires : [`/opponent-detector`](opponent-detector/README.md)
- 📄 **Licence**

---

## Fonctionnement

<p align="center">
  <img src="src/figure,1.png" alt="Figure 1. Architecture du système" />
</p>

**Figure 1.** Architecture et flux de données de l’Auto Soccer Bot (ESP32) en modes manuel et automatique.
