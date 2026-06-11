# 🍽️ Restaurant Intelligent

Application connectant un serveur **Node.js (Express + Socket.IO)** à un module de
**vision par ordinateur Python (OpenCV + YOLOv8)** pour gérer commandes et occupation
des tables en temps réel.

## 🏛️ Architecture

```
                         ┌──────────────────────────────┐
   📷 Caméra ─────────▶  │  PYTHON — Vision IA           │
                         │  table_detector.py            │
                         │  OpenCV + Ultralytics YOLOv8  │
                         │  zones tables -> Libre/Occupée│
                         └──────────────┬───────────────┘
                                        │ HTTP POST (requests)
                                        │ /api/tables/status  (x-api-key)
                                        ▼
   ┌────────────┐   QR /menu?table=X   ┌──────────────────────────────┐
   │  👤 CLIENT │ ───────────────────▶ │  NODE.JS — server.js          │
   │  menu.html │   POST /api/orders   │  Express (REST) + JWT          │
   └────────────┘ ◀─────────────────── │  Socket.IO (temps réel)        │
                                        └──────────────┬───────────────┘
                                                       │ WebSocket (room "staff")
                                          ┌────────────┴────────────┐
                                          ▼                         ▼
                               ┌───────────────────┐   ┌───────────────────┐
                               │ 👨‍🍳 SERVEUR/CUISINE │   │   📊 ADMIN          │
                               │ kitchen.html       │   │  menu, staff, stats│
                               │ commandes + plan   │   │  /api/stats        │
                               └───────────────────┘   └───────────────────┘
```

## 📁 Structure des fichiers

```
restaurant/
├── server.js                 # Serveur principal Node.js (REST + Socket.IO)
├── package.json
├── .env.example
├── data/
│   └── db.js                 # Données en mémoire (users, menu, orders, tables)
├── public/
│   ├── menu.html             # Page CLIENT (accès QR Code)
│   └── kitchen.html          # Page STAFF temps réel (cuisine + plan de salle)
└── ai_vision/
    ├── table_detector.py     # Script IA (OpenCV + YOLO)
    └── requirements.txt
```

## 👥 Rôles

| Rôle              | Authentification        | Accès                                   |
|-------------------|-------------------------|-----------------------------------------|
| **Admin**         | JWT (`admin`/`admin123`)   | Menu, personnel, statistiques `/api/stats` |
| **Serveur/Cuisine** | JWT (`serveur`/`serveur123`) | Commandes temps réel + plan de salle    |
| **Client**        | Aucune (QR Code)        | `/menu?table=X`, passe commande         |

## 🔌 API principale

| Méthode | Route                     | Accès        | Description                          |
|---------|---------------------------|--------------|--------------------------------------|
| POST    | `/api/auth/login`         | public       | Connexion Admin / Serveur (JWT)      |
| GET     | `/menu?table=X`           | client       | Page menu de la table X              |
| GET     | `/api/menu`               | public       | Liste des plats                      |
| POST    | `/api/orders`             | client       | Valider une commande                 |
| GET     | `/api/orders`             | staff        | Liste des commandes                  |
| PATCH   | `/api/orders/:id/status`  | staff        | Changer le statut d'une commande     |
| POST    | `/api/tables/status`      | IA (x-api-key) | Mise à jour de l'état des tables   |
| GET     | `/api/tables`             | staff        | État courant des tables              |
| GET     | `/api/stats`              | admin        | Statistiques                         |

## 🚀 Démarrage

### 1. Backend Node.js
```bash
npm install
copy .env.example .env      # (Windows) puis ajuster les secrets
npm start
```
- Client  : http://localhost:3000/menu?table=3
- Staff    : http://localhost:3000/kitchen.html

> ⚠️ Node.js n'est pas détecté sur cette machine. Installez-le depuis
> https://nodejs.org (LTS) puis relancez `npm install`.

### 2. Module IA Python
```bash
cd ai_vision
pip install -r requirements.txt
python table_detector.py                # webcam
python table_detector.py --source demo.mp4
```
Appuyez sur **q** pour quitter la fenêtre OpenCV.

## 🧠 Modèle & Dataset (YOLO)

Pour détecter une **personne**, vous n'avez **pas besoin d'un dataset Kaggle** :
le modèle pré-entraîné **`yolov8n.pt`** (entraîné sur **COCO**) contient déjà la
classe `person` (id `0`). Il est téléchargé automatiquement au premier lancement.

Si vous souhaitez tout de même un dataset orienté restaurant (entraînement custom :
détecter chaises occupées, assiettes, etc.), pistes sur Kaggle / Roboflow :
- COCO 2017 (référence, classe `person`) — base du modèle fourni.
- « Restaurant / Dining table object detection » (Roboflow Universe).
- « People detection / crowd counting » (Kaggle) pour affiner la classe personne.

Pour entraîner un modèle custom :
```bash
yolo detect train data=dataset.yaml model=yolov8n.pt epochs=50 imgsz=640
```
puis remplacez `MODEL_PATH = "yolov8n.pt"` par `runs/detect/train/weights/best.pt`.

## 🔒 Sécurité (à renforcer en production)
- Remplacer la base en mémoire (`data/db.js`) par PostgreSQL/MongoDB.
- Stocker `JWT_SECRET` et `AI_API_KEY` dans `.env` (jamais en dur).
- Passer en HTTPS et restreindre le CORS.
- Limiter le débit (rate-limit) sur `/api/orders` et `/api/tables/status`.
