"""
============================================================
  RESTAURANT INTELLIGENT — Module IA Vision (OpenCV + YOLO)
============================================================
Détecte la présence de personnes ('person') dans des zones
rectangulaires (= tables) puis envoie l'état au serveur Node.

Pipeline :
  webcam/vidéo --> YOLOv8 (détection 'person') --> test d'appartenance
  aux zones tables --> Libre / Occupée --> POST /api/tables/status

Lancement :
  pip install -r requirements.txt
  python table_detector.py            # webcam (source 0)
  python table_detector.py --source video.mp4
============================================================
"""

import argparse
import time

import cv2
import requests
from ultralytics import YOLO

# ---------------------- Configuration ----------------------
NODE_URL = "http://localhost:3000/api/tables/status"
API_KEY = "ai-secret-key"           # doit correspondre à AI_API_KEY côté Node
SEND_INTERVAL = 1.5                 # secondes entre deux envois (anti-spam)
CONF_THRESHOLD = 0.45               # confiance minimale YOLO
PERSON_CLASS_ID = 0                 # 'person' dans le dataset COCO

# Zones des tables : (x1, y1, x2, y2) en pixels sur l'image.
# À ajuster selon le cadrage de votre caméra.
TABLE_ZONES = {
    1: (40, 60, 220, 300),
    2: (240, 60, 420, 300),
    3: (440, 60, 620, 300),
}

# Modèle YOLO pré-entraîné sur COCO (contient déjà la classe 'person').
# 'yolov8n.pt' (nano) = léger/rapide ; téléchargé automatiquement au 1er run.
MODEL_PATH = "yolov8n.pt"


def point_in_zone(px, py, zone):
    """Le point (px, py) est-il dans le rectangle zone ?"""
    x1, y1, x2, y2 = zone
    return x1 <= px <= x2 and y1 <= py <= y2


def send_status(table_states):
    """Envoie l'état des tables au serveur Node.js."""
    payload = {
        "tables": [{"table": t, "status": s} for t, s in table_states.items()]
    }
    try:
        r = requests.post(
            NODE_URL,
            json=payload,
            headers={"x-api-key": API_KEY},
            timeout=2,
        )
        print(f"[Node] {r.status_code} -> {payload['tables']}")
    except requests.RequestException as e:
        print(f"[Node] Erreur d'envoi : {e}")


def main():
    parser = argparse.ArgumentParser(description="Détection d'occupation des tables")
    parser.add_argument("--source", default="0",
                        help="0 = webcam, ou chemin d'une vidéo/RTSP")
    parser.add_argument("--no-window", action="store_true",
                        help="Désactive l'affichage (mode serveur)")
    args = parser.parse_args()

    source = int(args.source) if args.source.isdigit() else args.source

    print("Chargement du modèle YOLO…")
    model = YOLO(MODEL_PATH)

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"❌ Impossible d'ouvrir la source : {source}")
        return

    last_sent = 0.0
    last_states = None

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        # Détection (on filtre sur la classe 'person').
        results = model(frame, classes=[PERSON_CLASS_ID],
                        conf=CONF_THRESHOLD, verbose=False)

        # Par défaut toutes les tables sont libres.
        table_states = {t: "Libre" for t in TABLE_ZONES}

        # Pour chaque personne détectée, on teste le point au sol (bas-centre de la box).
        for box in results[0].boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            foot_x = int((x1 + x2) / 2)
            foot_y = int(y2)  # bas de la box = position au sol

            for table, zone in TABLE_ZONES.items():
                if point_in_zone(foot_x, foot_y, zone):
                    table_states[table] = "Occupée"

            if not args.no_window:
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                cv2.circle(frame, (foot_x, foot_y), 5, (0, 0, 255), -1)

        # Dessin des zones tables.
        if not args.no_window:
            for table, (zx1, zy1, zx2, zy2) in TABLE_ZONES.items():
                occupied = table_states[table] == "Occupée"
                color = (0, 0, 255) if occupied else (0, 200, 0)
                cv2.rectangle(frame, (zx1, zy1), (zx2, zy2), color, 2)
                cv2.putText(frame, f"Table {table}: {table_states[table]}",
                            (zx1, zy1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
            cv2.imshow("Restaurant Intelligent - Vision IA", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        # Envoi temps réel : seulement si l'état change OU toutes les SEND_INTERVAL s.
        now = time.time()
        if table_states != last_states or (now - last_sent) > SEND_INTERVAL:
            send_status(table_states)
            last_sent = now
            last_states = dict(table_states)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
