# -*- coding: utf-8 -*-
"""
Génère le PDF d'explication du code : Restaurant Intelligent.
Sortie : public/docs/restaurant-intelligent-explication-code.pdf
Relancer après une modif du code :  python docs/generate_doc_pdf.py
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    Preformatted, HRFlowable,
)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "..", "public", "docs")
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "restaurant-intelligent-explication-code.pdf")

RED = colors.HexColor("#c0392b")
DARK = colors.HexColor("#7d1f15")
GREY = colors.HexColor("#555555")
LIGHT = colors.HexColor("#faf0ee")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("Cover", parent=styles["Title"], fontSize=30,
                           textColor=RED, alignment=TA_CENTER, spaceAfter=6))
styles.add(ParagraphStyle("CoverSub", parent=styles["Normal"], fontSize=13,
                           textColor=GREY, alignment=TA_CENTER, spaceAfter=4))
styles.add(ParagraphStyle("H1", parent=styles["Heading1"], fontSize=17,
                           textColor=RED, spaceBefore=16, spaceAfter=8))
styles.add(ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13,
                           textColor=DARK, spaceBefore=10, spaceAfter=4))
styles.add(ParagraphStyle("Body", parent=styles["Normal"], fontSize=10.5,
                           leading=15, alignment=TA_LEFT, spaceAfter=6))
styles.add(ParagraphStyle("Puce", parent=styles["Body"], leftIndent=14,
                          bulletIndent=4, spaceAfter=3))
styles.add(ParagraphStyle("CodeBox", parent=styles["Code"], fontSize=8.2,
                          leading=10.5, backColor=colors.HexColor("#f4f4f4"),
                          borderColor=colors.HexColor("#dddddd"), borderWidth=0.6,
                          borderPadding=6, textColor=colors.HexColor("#1d1d1d")))
styles.add(ParagraphStyle("Caption", parent=styles["Body"], fontSize=9,
                          textColor=GREY, spaceBefore=2, spaceAfter=10))


def code(txt):
    return Preformatted(txt.strip("\n"), styles["CodeBox"])


def h1(t): return Paragraph(t, styles["H1"])
def h2(t): return Paragraph(t, styles["H2"])
def p(t): return Paragraph(t, styles["Body"])
def cap(t): return Paragraph(t, styles["Caption"])
def b(t): return Paragraph("• " + t, styles["Puce"])
def hr(): return HRFlowable(width="100%", thickness=0.8, color=RED, spaceBefore=4, spaceAfter=8)


def table(data, col_widths):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), RED),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e0c9c5")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


story = []

# ---------------- PAGE DE GARDE ----------------
story += [
    Spacer(1, 60),
    Paragraph("🍽️", ParagraphStyle("logo", parent=styles["Cover"], fontSize=64)),
    Paragraph("Restaurant Intelligent", styles["Cover"]),
    Paragraph("Explication complète du code", styles["CoverSub"]),
    Spacer(1, 6),
    Paragraph("Node.js · Express · Socket.IO &nbsp;+&nbsp; Vision IA Python (OpenCV / YOLOv8)",
              styles["CoverSub"]),
    Spacer(1, 30),
    hr(),
    Spacer(1, 10),
    p("Ce document explique, fichier par fichier, comment fonctionne l'application "
      "<b>Restaurant Intelligent</b> : un serveur Node.js temps réel relié à un module "
      "de vision par ordinateur Python qui détecte l'occupation des tables, plus trois "
      "interfaces web (client par QR Code, cuisine/serveur, administration)."),
    Spacer(1, 50),
    p("<font color='#888888'>Document généré automatiquement — projet "
      "<font face='Courier'>C:\\wammpp64\\www\\restaurant</font></font>"),
]
story.append(PageBreak())

# ---------------- 1. VUE D'ENSEMBLE ----------------
story += [
    h1("1. Vue d'ensemble"),
    p("L'application met en relation <b>trois mondes</b> :"),
    b("<b>Le client</b> scanne un QR Code posé sur sa table, ouvre le menu sur son "
      "téléphone et passe commande, <b>sans créer de compte</b>."),
    b("<b>Le personnel</b> (cuisine / serveur) reçoit les commandes <b>en temps réel</b> "
      "et visualise le plan de salle (tables libres / occupées)."),
    b("<b>L'IA Python</b> analyse le flux d'une caméra, détecte les personnes assises et "
      "envoie au serveur l'état de chaque table."),
    Spacer(1, 4),
    p("Le tout repose sur <b>un seul serveur Node.js</b> qui sert à la fois l'API REST, "
      "les pages web statiques et le canal temps réel (WebSocket via Socket.IO)."),
    h2("Schéma d'architecture"),
    code(
"""        📷 Caméra
           │
           ▼
   ┌────────────────────────┐
   │ PYTHON — Vision IA      │  table_detector.py
   │ OpenCV + YOLOv8         │  zones tables -> Libre/Occupee
   └───────────┬────────────┘
               │ HTTP POST  /api/tables/status  (x-api-key)
               ▼
   ┌────────────────────────────────────────────┐
   │ NODE.JS — server.js                          │
   │ Express (REST) + JWT + Socket.IO (temps reel)│
   └───────┬───────────────────────────┬──────────┘
           │ WebSocket (room "staff")   │ HTTP
           ▼                            ▼
   👨‍🍳 Cuisine/Serveur            👤 Client (QR /menu?table=X)
   kitchen.html                  menu.html
   📊 Admin (menu/staff/stats) → admin.html"""),
    cap("Figure 1 — La caméra alimente l'IA, l'IA et les clients alimentent le serveur "
        "Node, qui pousse les mises à jour vers le staff en temps réel."),
]

# ---------------- 2. STRUCTURE ----------------
story += [
    h1("2. Structure des fichiers"),
    table([
        ["Fichier", "Rôle"],
        ["server.js", "Serveur principal : API REST, auth JWT, Socket.IO, génération QR"],
        ["data/db.js", "« Base de données » en mémoire (users, menu, orders, tables)"],
        ["public/index.html", "Page d'accueil (portail vers les 4 espaces)"],
        ["public/menu.html", "Espace CLIENT — menu + panier (accès par QR Code)"],
        ["public/kitchen.html", "Espace STAFF — commandes temps réel + plan de salle"],
        ["public/admin.html", "Espace ADMIN — menu, personnel, statistiques"],
        ["public/qrcodes.html", "Génération / impression des QR Codes des tables"],
        ["ai_vision/table_detector.py", "Module IA : détection des personnes par table"],
        ["package.json", "Dépendances Node et scripts (start / dev)"],
        [".env.example", "Variables d'environnement (PORT, secrets)"],
    ], [150, 320]),
]
story.append(PageBreak())

# ---------------- 3. SERVER.JS ----------------
story += [
    h1("3. Le serveur Node.js — server.js"),
    p("C'est le cœur du projet. Il utilise <b>Express</b> pour l'API, <b>Socket.IO</b> "
      "pour le temps réel, <b>jsonwebtoken</b> pour l'authentification et <b>qrcode</b> "
      "pour générer les QR Codes."),
    h2("3.1 Initialisation"),
    code(
"""const app = express();
const server = http.createServer(app);
const io = new Server(server, { cors: { origin: "*" } });

app.use(cors());
app.use(express.json({ limit: "6mb" })); // 6mb : photos en Data URL
app.use(express.static(path.join(__dirname, "public")));"""),
    p("On crée un serveur HTTP commun à Express et à Socket.IO. La limite JSON est "
      "montée à 6 Mo pour accepter les images de plats envoyées en <i>Data URL</i> "
      "depuis l'admin. Le dossier <font face='Courier'>public/</font> est servi en statique."),

    h2("3.2 Authentification &amp; rôles (3 middlewares)"),
    code(
"""function authRequired(req, res, next) {        // 1) Token JWT valide ?
  const token = (req.headers.authorization||"").replace("Bearer ","");
  try { req.user = jwt.verify(token, JWT_SECRET); next(); }
  catch { return res.status(401).json({ error: "Token invalide" }); }
}

function authorize(...roles) {                  // 2) Bon rôle ?
  return (req, res, next) =>
    roles.includes(req.user.role) ? next()
      : res.status(403).json({ error: "Accès interdit" });
}

function aiKeyRequired(req, res, next) {         // 3) Clé API de l'IA ?
  if (req.headers["x-api-key"] !== AI_API_KEY)
    return res.status(401).json({ error: "Clé API IA invalide" });
  next();
}"""),
    b("<b>authRequired</b> : vérifie le jeton JWT envoyé dans l'en-tête "
      "<font face='Courier'>Authorization: Bearer ...</font> et place l'utilisateur "
      "décodé dans <font face='Courier'>req.user</font>."),
    b("<b>authorize(...roles)</b> : autorise seulement certains rôles "
      "(ex. <font face='Courier'>authorize(\"admin\")</font>)."),
    b("<b>aiKeyRequired</b> : protège l'endpoint de l'IA par une clé secrète partagée "
      "(<font face='Courier'>x-api-key</font>), différente du JWT car le script Python "
      "n'est pas un utilisateur connecté."),

    h2("3.3 Connexion — /api/auth/login"),
    code(
"""const user = users.find(u => u.username === username);
if (!user || !bcrypt.compareSync(password, user.passwordHash))
  return res.status(401).json({ error: "Identifiants incorrects" });

const token = jwt.sign({ id, username, role }, JWT_SECRET, { expiresIn: "8h" });
res.json({ token, role, username });"""),
    p("Le mot de passe est comparé à son <b>hash bcrypt</b> (jamais stocké en clair). "
      "Si c'est bon, on signe un JWT valable 8 h contenant l'id, le nom et le rôle."),
]
story.append(PageBreak())

story += [
    h2("3.4 Commande client — POST /api/orders"),
    p("Étape sensible : on ne fait <b>jamais confiance aux prix envoyés par le client</b>. "
      "La commande est reconstruite à partir du menu officiel côté serveur (anti-triche)."),
    code(
"""for (const it of items) {
  const dish = menu.find(m => m.id === it.id && m.available);
  if (!dish) continue;                          // plat inconnu/indispo -> ignoré
  const qty = Math.max(1, parseInt(it.qty) || 1);
  lineItems.push({ id: dish.id, name: dish.name, price: dish.price, qty });
}
const total = lineItems.reduce((s, i) => s + i.price * i.qty, 0);
orders.push(order);
io.to("staff").emit("order:new", order);        // 🔴 temps réel -> cuisine"""),
    p("Une fois la commande créée, <font face='Courier'>io.to(\"staff\").emit(...)</font> "
      "la pousse <b>instantanément</b> à tout le personnel connecté, sans rechargement de page."),

    h2("3.5 État des tables — POST /api/tables/status (appelé par l'IA)"),
    code(
"""app.post("/api/tables/status", aiKeyRequired, (req, res) => {
  for (const t of req.body.tables) {
    tables[t.table].status = t.status === "Occupée" ? "Occupée" : "Libre";
    tables[t.table].updatedAt = new Date().toISOString();
  }
  io.to("staff").emit("tables:update", updated);  // 🔴 plan de salle live
});"""),
    p("Protégé par <font face='Courier'>aiKeyRequired</font>, cet endpoint reçoit la liste "
      "des tables et leur état depuis Python, puis diffuse la mise à jour au staff."),

    h2("3.6 QR Codes — /api/qrcode"),
    code(
"""function getLanIp() { /* cherche l'IPv4 locale non interne */ }

app.get("/api/qrcode", async (req, res) => {
  const url = `${base}/menu?table=${table}`;     // ce qu'encode le QR
  const png = await QRCode.toBuffer(url, { width: 300, margin: 2 });
  res.type("png").send(png);
});"""),
    p("Le serveur détecte son IP sur le réseau local (LAN) pour que les téléphones des "
      "clients puissent l'atteindre, puis génère un PNG de QR Code encodant "
      "<font face='Courier'>/menu?table=X</font>."),

    h2("3.7 Statistiques — GET /api/stats (admin)"),
    code(
"""const revenue = orders.reduce((s, o) => s + o.total, 0);
const occupied = Object.values(tables).filter(t => t.status==="Occupée").length;
// top 5 des plats les plus vendus, agrégés depuis toutes les commandes
res.json({ totalOrders, revenue, tablesOccupied, tablesTotal, topDishes });"""),
    p("Calcule le chiffre d'affaires, le nombre de tables occupées et le classement des "
      "plats les plus commandés."),
]
story.append(PageBreak())

# ---------------- 4. SOCKET.IO ----------------
story += [
    h1("4. Le temps réel — Socket.IO"),
    p("Socket.IO maintient une connexion <b>WebSocket</b> ouverte entre le serveur et "
      "chaque navigateur du personnel. Le serveur peut ainsi « pousser » des événements "
      "sans que le client ait à demander."),
    h2("4.1 Authentification du socket"),
    code(
"""io.use((socket, next) => {                       // garde d'entrée
  const token = socket.handshake.auth?.token;    // JWT passé à la connexion
  try { socket.user = jwt.verify(token, JWT_SECRET); next(); }
  catch { next(new Error("Auth socket refusée")); }
});

io.on("connection", (socket) => {
  if (["admin","serveur"].includes(socket.user.role)) {
    socket.join("staff");                        // rejoint la "room" du staff
    socket.emit("tables:snapshot", tables);      // état initial
    socket.emit("orders:snapshot", orders);
  }
});"""),
    p("Seuls les sockets présentant un JWT valide sont acceptés. Le staff rejoint la "
      "<b>room « staff »</b> ; à la connexion, on lui envoie un <i>snapshot</i> de l'état "
      "courant pour qu'il démarre avec les bonnes données."),
    h2("4.2 Les événements échangés"),
    table([
        ["Événement", "Sens", "Contenu"],
        ["order:new", "serveur → staff", "Nouvelle commande client"],
        ["order:update", "serveur → staff", "Changement de statut d'une commande"],
        ["tables:update", "serveur → staff", "Nouvel état des tables (depuis l'IA)"],
        ["tables:snapshot", "serveur → staff", "État complet des tables à la connexion"],
        ["orders:snapshot", "serveur → staff", "Toutes les commandes à la connexion"],
    ], [120, 130, 220]),
]

# ---------------- 5. DB ----------------
story += [
    h1("5. Les données — data/db.js"),
    p("Pour la démo, les données vivent <b>en mémoire</b> (de simples tableaux JS). "
      "Elles sont réinitialisées à chaque redémarrage du serveur. En production, on "
      "remplacerait ce fichier par PostgreSQL ou MongoDB."),
    code(
"""const users = [   // mots de passe hashés au démarrage avec bcrypt
  { id:1, username:"admin",   role:"admin",   passwordHash: hash("admin123") },
  { id:2, username:"serveur", role:"serveur", passwordHash: hash("serveur123") },
];
const menu   = [ { id:1, name:"Salade César", category:"Entrée", price:6.5, ... } ];
const orders = [];                       // rempli par les clients
const tables = { 1:{status:"Libre"}, 2:{...}, 3:{...} };  // mis à jour par l'IA"""),
    cap("Identifiants de démo : admin / admin123 — serveur / serveur123"),
]
story.append(PageBreak())

# ---------------- 6. IA PYTHON ----------------
story += [
    h1("6. La vision par ordinateur — table_detector.py"),
    p("Ce script Python indépendant lit une caméra (ou une vidéo), détecte les personnes "
      "avec <b>YOLOv8</b> et déduit quelles tables sont occupées."),
    h2("6.1 Configuration"),
    code(
"""NODE_URL = "http://localhost:3000/api/tables/status"
API_KEY  = "ai-secret-key"          # doit = AI_API_KEY côté Node
CONF_THRESHOLD = 0.45               # confiance minimale YOLO
PERSON_CLASS_ID = 0                 # 'person' dans le dataset COCO
TABLE_ZONES = {                     # rectangles (x1,y1,x2,y2) en pixels
    1: (40, 60, 220, 300),
    2: (240, 60, 420, 300),
    3: (440, 60, 620, 300),
}
MODEL_PATH = "yolov8n.pt"           # modèle nano, téléchargé au 1er run"""),
    p("Chaque table est définie par un <b>rectangle de pixels</b> dans l'image. "
      "Le modèle <font face='Courier'>yolov8n.pt</font> est pré-entraîné sur COCO et "
      "contient déjà la classe <i>person</i> : <b>aucun dataset à télécharger</b>."),

    h2("6.2 Boucle principale"),
    code(
"""results = model(frame, classes=[PERSON_CLASS_ID], conf=CONF_THRESHOLD)
table_states = {t: "Libre" for t in TABLE_ZONES}     # tout libre par défaut

for box in results[0].boxes:                          # chaque personne détectée
    x1, y1, x2, y2 = box.xyxy[0].tolist()
    foot_x = int((x1 + x2) / 2)                       # centre horizontal
    foot_y = int(y2)                                  # bas de la box = pieds
    for table, zone in TABLE_ZONES.items():
        if point_in_zone(foot_x, foot_y, zone):
            table_states[table] = "Occupée"           # personne dans la zone"""),
    p("Astuce clé : on teste le <b>point au sol</b> (bas-centre de la boîte englobante = "
      "les pieds), pas le centre du corps. C'est plus fiable pour savoir à quelle table "
      "appartient réellement la personne."),

    h2("6.3 Envoi temps réel (anti-spam)"),
    code(
"""now = time.time()
if table_states != last_states or (now - last_sent) > SEND_INTERVAL:
    send_status(table_states)          # POST vers Node avec x-api-key
    last_sent = now
    last_states = dict(table_states)"""),
    p("On n'envoie au serveur <b>que si l'état a changé</b>, ou au minimum toutes les "
      "1,5 s. Cela évite d'inonder le serveur à chaque image (≈ 30 par seconde)."),
]
story.append(PageBreak())

# ---------------- 7. RÔLES & API ----------------
story += [
    h1("7. Rôles et tableau des routes API"),
    h2("Les trois rôles"),
    table([
        ["Rôle", "Authentification", "Accès"],
        ["Admin", "JWT — admin / admin123", "Menu, personnel, statistiques"],
        ["Serveur / Cuisine", "JWT — serveur / serveur123", "Commandes temps réel + plan de salle"],
        ["Client", "Aucune (QR Code)", "Voir le menu, passer commande"],
    ], [110, 170, 190]),
    h2("Routes principales"),
    table([
        ["Méthode", "Route", "Accès", "Description"],
        ["POST", "/api/auth/login", "public", "Connexion (renvoie un JWT)"],
        ["GET", "/api/menu", "public", "Liste des plats disponibles"],
        ["POST", "/api/orders", "client", "Valider une commande"],
        ["GET", "/api/orders", "staff", "Liste des commandes"],
        ["PATCH", "/api/orders/:id/status", "staff", "Changer le statut"],
        ["POST", "/api/tables/status", "IA (clé)", "Mise à jour des tables"],
        ["GET", "/api/tables", "staff", "État des tables"],
        ["GET", "/api/stats", "admin", "Statistiques"],
        ["GET/POST/PATCH/DELETE", "/api/admin/menu", "admin", "Gérer le menu"],
        ["GET/POST/DELETE", "/api/admin/staff", "admin", "Gérer le personnel"],
        ["GET", "/api/qrcode?table=X", "public", "Image PNG du QR Code"],
    ], [95, 140, 60, 175]),
]

# ---------------- 8. DEMARRAGE ----------------
story += [
    h1("8. Démarrage"),
    h2("Backend Node.js"),
    code(
"""npm install
copy .env.example .env     # Windows — puis ajuster les secrets
npm start                  # -> http://localhost:3000"""),
    h2("Module IA Python"),
    code(
"""cd ai_vision
pip install -r requirements.txt
python table_detector.py             # webcam
python table_detector.py --source demo.mp4
# 'q' pour quitter la fenêtre OpenCV"""),
    h2("Points de sécurité à renforcer en production"),
    b("Remplacer la base en mémoire par une vraie base (PostgreSQL / MongoDB)."),
    b("Mettre <font face='Courier'>JWT_SECRET</font> et <font face='Courier'>AI_API_KEY</font> "
      "dans <font face='Courier'>.env</font> (jamais en dur)."),
    b("Passer en HTTPS et restreindre le CORS."),
    b("Limiter le débit (rate-limit) sur /api/orders et /api/tables/status."),
    Spacer(1, 16),
    hr(),
    Paragraph("Fin du document — Restaurant Intelligent", styles["CoverSub"]),
]


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(RED)
    canvas.setLineWidth(0.6)
    canvas.line(20 * mm, 15 * mm, 190 * mm, 15 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GREY)
    canvas.drawString(20 * mm, 10 * mm, "Restaurant Intelligent — Explication du code")
    canvas.drawRightString(190 * mm, 10 * mm, "Page %d" % doc.page)
    canvas.restoreState()


doc = SimpleDocTemplate(
    OUT, pagesize=A4,
    leftMargin=20 * mm, rightMargin=20 * mm,
    topMargin=18 * mm, bottomMargin=20 * mm,
    title="Restaurant Intelligent — Explication du code",
    author="Restaurant Intelligent",
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("PDF généré :", os.path.abspath(OUT))
