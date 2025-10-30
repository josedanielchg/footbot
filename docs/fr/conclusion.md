## 🎯 Conclusion, Résultats & Défis

### Conclusion
Ce projet met en œuvre une boucle complète **percevoir → interpréter → commander → agir** en deux modes :
- **Manual Control** — ✅ Entièrement opérationnel. Téléopération gestuelle en temps réel depuis la webcam du portable (MediaPipe + OpenCV) avec envoi de commandes JSON vers `/move` limitées en débit. Voir [`manual_control/`](manual_control.md).
- **Automatic Mode** — 🟡 Fondations en place. La chaîne (intake HTTPX → détection hybride → machine à états → `/move`) fonctionne avec un **suivi de balle**. Les détecteurs **Goal** et **Opponent** sont **entraînés et documentés** dans [`soccer_vision.md`](soccer_vision.md) mais **pas encore intégrés** dans la machine à états. Voir [`auto_soccer_bot/`](auto_soccer_bot.md).

### Résultats actuels
- **Téléop manuelle** : Stable à des fréquences interactives sur des portables standards ; contrôle fluide grâce à la **limitation de débit + anti-rebond**.
- **Autonomie (balle)** : Suivi robuste via un **détecteur hybride** (YOLO planifié + HSV à chaque image) et une **FSM** qui centre et avance avec des virages doux.
- **Streaming** : Faible latence perçue après passage à **HTTPX** avec conservation de **la “dernière image uniquement”** ; MJPEG **QVGA** réduit le coût de décodage.

### Principaux défis & atténuations
- **Latence / buffering du flux** → Bascule vers **HTTPX** avec parsing multipart explicite et rejet des images obsolètes.
- **Robustesse vs vitesse en perception** → **YOLO toutes les _N_ images** + **HSV** à chaque image ; sortie unifiée `(cx, cy, area)`.
- **Saturation de commandes** → **Déduplication + limitation de débit** dans le communicateur pour éviter de saturer l’ESP32.
- **Oscillations du contrôleur** → **Couloir cible**, compteurs de confirmation et délais de grâce dans la FSM pour une alignement plus stable.

### Prochaines étapes
1. **Raccorder les signaux goal/opponent** depuis [`soccer_vision`](soccer_vision.md) dans la boucle temps réel.
2. **Étendre la FSM** avec une **fusion multi-objets** (balle + but + adversaire) pour l’alignement de tir et l’évitement de collisions.
3. **Évaluation quantitative** : tests dédiés (précision/rappel, budgets de latence) et contrôles de régression pour stabiliser le comportement.