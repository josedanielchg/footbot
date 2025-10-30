## 🧪 État du projet

- **Contrôle manuel (téléopération par gestes)** — ✅ **Opérationnel de bout en bout.**  
  Tourne en temps réel sur un ordinateur portable avec **OpenCV + MediaPipe** ; commandes JSON via HTTP vers `/move` avec **limitation de débit et anti-rebond**. Stable sur matériel grand public.

- **Mode automatique (vision dans la boucle)** — 🟡 **Couches en place, pas encore entièrement intégrées.**  
  - **Acquisition du flux :** lecteur MJPEG **HTTPX** depuis `http://<ESP32_IP>:81/stream` — **prêt**.  
  - **Perception :**  
    - **Balle** — détecteur **actif** dans la boucle.  
    - **But** et **Adversaire** — modèles **entraînés et disponibles** dans [`soccer_vision.md`](soccer_vision.md), mais **pas encore raccordés** à la boucle en direct.  
  - **Décision :** petite **machine à états** avec **suivi de balle** uniquement (pas de fusion multi-objets pour l’instant).  
  - **Actionnement :** POST HTTP vers `/move` — **prêt**.

- **Limitation actuelle** — L’autonomie est **mono-cible (balle)** ; des fonctions comme **l’alignement de tir** et **l’évitement des adversaires** attendent l’intégration des signaux but/adversaire dans le contrôleur.

- **Prochaines étapes (court terme)**  
  1) Raccorder les détections **but/adversaire** au bus de perception.  
  2) Étendre la machine à états avec **fusion multi-objets** et transitions.  
  3) Ajuster seuils/gains et ajouter des tests de régression en boucle fermée.