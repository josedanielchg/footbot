# Étapes de foot prévues

Cette feuille de route décrit la direction que prend le stack de foot simulé. La
base stable est intentionnellement déterministe : les topics de perception
alimentent les estimateurs d'état, les estimateurs d'état alimentent les machines
à états finis, et exactement un contrôleur possède `/cmd_vel` dans chaque mode de
lancement.

## Fondations implémentées

### Contrôle de balle

Objectif : prouver qu'un FootBot peut trouver, approcher, toucher et garder la
balle orange dans une zone de contrôle frontale.

Comportement actuel :

- Utilise le détecteur HSV de balle de `footbot_perception`.
- Convertit `Detection2D` en `BallState`.
- Exécute une FSM déterministe avec des états de recherche, alignement, approche,
  contact, contrôle, rotation-avec-balle, récupération et arrêt sûr.
- Fournit des mondes de validation à scénario unique et multi-couloirs.

Focus de validation :

- Le robot ne devrait pas bouger sans un état de balle frais.
- La balle devrait rester assez proche pour un contact contrôlé.
- Les tests multi-couloirs devraient isoler les topics pour que plusieurs
  scénarios puissent s'exécuter dans une seule session Gazebo.

### Reach Goal

Objectif : pousser la balle vers un but visible en utilisant la perception de la
caméra du robot.

Comportement actuel :

- Utilise un détecteur YOLO `ball` + `goal`.
- Convertit `Detection2DArray` en `BallGoalState`.
- Conserve une courte mémoire temporelle du but lorsque celui-ci disparaît près de
  l'entrée.
- Utilise `COMMIT_TO_GOAL` pour maintenir une poussée lente et centrée sur la
  balle après des pertes du but à courte distance, sans utiliser les poses de
  Gazebo pour naviguer.
- Utilise `reach_goal_fsm` comme unique propriétaire de `/cmd_vel`.
- Utilise `reach_goal_score_monitor` comme logique d'arbitre de simulation pour
  s'arrêter après un but.

Focus de validation :

- Le modèle devrait détecter à la fois la balle et le but lors de l'approche
  initiale.
- La mémoire du but devrait couvrir de courtes pertes de YOLO tant que la balle
  reste contrôlée.
- `COMMIT_TO_GOAL` devrait porter la poussée finale lorsque le but disparaît près
  de l'entrée, puis s'arrêter une fois que `/soccer/goal_scored` se déclenche.
- `/soccer/goal_scored` devrait arrêter le robot une fois que la balle entre dans
  la zone de but.

## Ensuite : améliorations du dribble dirigé vers le but

Objectif : rendre Reach Goal plus fiable avant d'ajouter des adversaires.

Idées pour l'implémentation :

- Ajouter plus d'images proches du but au dataset, surtout lorsque les poteaux sont
  partiellement visibles ou que l'entrée du but remplit le cadre.
- Améliorer la réacquisition du but après une perte temporaire en combinant la
  mémoire temporelle avec un comportement de balayage doux qui préserve le contrôle
  de la balle.
- Remplacer le fallback de commit actuel par une perception à courte distance plus
  robuste une fois que le dataset inclut assez d'exemples proches du but.
- Régler la vitesse de dribble, le gain angulaire et la durée de récupération pour
  que le robot pousse la balle au lieu de la dépasser.
- Ajouter des chemins de récupération pour les échecs courants : la balle glisse à
  gauche/droite, la balle se coince près d'un poteau, ou le robot atteint le but
  sans la balle.
- Suivre des métriques simples comme le temps jusqu'au premier contrôle, le temps
  jusqu'au but, la durée de la mémoire du but, le nombre de pertes de contrôle et la
  pose finale de la balle.

Forme de lancement attendue :

- Conserver un lancement dédié de Reach Goal.
- Conserver `/cmd_vel` sous la propriété de `reach_goal_fsm`.
- Conserver le score comme logique d'arbitre de simulation, pas comme perception du
  robot.

## Prévu : interaction avec les adversaires

Objectif : détecter un adversaire avec la balle et disputer la possession sans
déstabiliser les comportements de base.

Idées pour l'implémentation :

- Utiliser le paquet de vision de foot pour détecter les classes `opponent`,
  `robot` ou `teammate` depuis la caméra du robot.
- Ajouter une estimation de possession dérivée de l'image : balle proche de
  l'adversaire, balle proche de soi, ou balle libre.
- Commencer avec des robots adversaires statiques ou scriptés avant d'ajouter des
  adversaires actifs.
- Ajouter des états de FSM pour observer, approcher-l'adversaire, disputer-la-balle,
  récupérer-la-balle et arrêt-sûr.
- Garder le comportement de collision et de sécurité conservateur ; la première
  version devrait disputer lentement et récupérer proprement.

Focus de validation :

- Le robot ne devrait jamais utiliser les poses de l'adversaire de Gazebo pour la
  prise de décision.
- La détection d'adversaire ne devrait pas publier de commandes de mouvement
  directement.
- Les modes de lancement d'adversaires devraient être séparés du Contrôle de balle
  et de Reach Goal.

## Prévu : jeu en équipe

Objectif : prendre en charge trois robots par camp avec des rôles clairs et une
propriété de commande isolée.

Idées pour l'implémentation :

- Définir des rôles comme gardien, défenseur et attaquant.
- Commencer avec des formations fixes autour de la balle centrale et des buts.
- Ajouter des namespaces par robot pour les topics de caméra, détections, état,
  état de FSM et `/cmd_vel`.
- Ne partager au début que des informations de haut niveau, comme « balle
  visible », « but visible », « le robot a le contrôle » ou « cible de rôle ».
- Explorer un comportement de passe simple après que chaque robot peut contrôler et
  approcher la balle de façon indépendante.

Focus de validation :

- Chaque robot devrait avoir exactement un propriétaire de commande.
- Les namespaces doivent empêcher les collisions de topics de caméra, de détection
  et `/cmd_vel`.
- Le comportement d'équipe devrait toujours permettre aux modes à robot unique de
  s'exécuter sans changement.

## Pistes de recherche

Objectif : comparer les méthodes tactiques seulement après que les bases
déterministes sont mesurables.

Approches candidates :

- FSM heuristiques pour des premières tactiques prévisibles.
- Arbres de comportement (behavior trees) si les transitions de FSM deviennent
  difficiles à maintenir.
- Planification de type MCTS ou SPO pour des choix tactiques à court horizon.
- RL ou MARL seulement après que la simulation dispose d'un reset stable, d'un
  score, de métriques et de scénarios reproductibles.

Règles pour les expériences :

- Garder les politiques de recherche dans des modes de lancement séparés.
- Ne pas remplacer les bases déterministes tant qu'une nouvelle méthode n'est pas
  plus facile à déboguer et mesurablement meilleure.
- Journaliser les métriques et les cas d'échec avant d'ajouter du code de politique
  plus complexe.
