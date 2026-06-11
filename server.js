/**
 * ============================================================
 *  RESTAURANT INTELLIGENT — Serveur principal Node.js
 * ============================================================
 *  - Auth par rôles (Admin / Serveur)               -> JWT
 *  - Menu client via QR Code  GET /menu?table=X
 *  - Commandes temps réel (Socket.IO)               -> cuisine
 *  - Réception de l'état des tables depuis l'IA      -> POST /api/tables/status
 * ============================================================
 */
require("dotenv").config();

const express = require("express");
const http = require("http");
const cors = require("cors");
const path = require("path");
const jwt = require("jsonwebtoken");
const bcrypt = require("bcryptjs");
const QRCode = require("qrcode");
const os = require("os");
const { Server } = require("socket.io");

const { users, menu, orders, tables } = require("./data/db");

const app = express();
const server = http.createServer(app);
const io = new Server(server, { cors: { origin: "*" } });

const PORT = process.env.PORT || 3000;
const JWT_SECRET = process.env.JWT_SECRET || "change-me-in-production";
// Clé partagée avec le script Python pour sécuriser l'endpoint de l'IA.
const AI_API_KEY = process.env.AI_API_KEY || "ai-secret-key";

app.use(cors());
app.use(express.json({ limit: "6mb" })); // 6mb pour accepter les photos uploadées (Data URL)
app.use(express.static(path.join(__dirname, "public")));

/* ============================================================
 *  MIDDLEWARES D'AUTHENTIFICATION
 * ============================================================ */
function authRequired(req, res, next) {
  const header = req.headers.authorization || "";
  const token = header.startsWith("Bearer ") ? header.slice(7) : null;
  if (!token) return res.status(401).json({ error: "Token manquant" });
  try {
    req.user = jwt.verify(token, JWT_SECRET);
    next();
  } catch {
    return res.status(401).json({ error: "Token invalide ou expiré" });
  }
}

// Restreint l'accès à certains rôles : authorize("admin"), authorize("admin","serveur")
function authorize(...roles) {
  return (req, res, next) => {
    if (!roles.includes(req.user.role)) {
      return res.status(403).json({ error: "Accès interdit pour ce rôle" });
    }
    next();
  };
}

// Protège l'endpoint appelé par l'IA Python via une clé API.
function aiKeyRequired(req, res, next) {
  if (req.headers["x-api-key"] !== AI_API_KEY) {
    return res.status(401).json({ error: "Clé API IA invalide" });
  }
  next();
}

/* ============================================================
 *  AUTHENTIFICATION (Admin / Serveur)
 * ============================================================ */
app.post("/api/auth/login", (req, res) => {
  const { username, password } = req.body || {};
  const user = users.find((u) => u.username === username);
  if (!user || !bcrypt.compareSync(password || "", user.passwordHash)) {
    return res.status(401).json({ error: "Identifiants incorrects" });
  }
  const token = jwt.sign(
    { id: user.id, username: user.username, role: user.role },
    JWT_SECRET,
    { expiresIn: "8h" }
  );
  res.json({ token, role: user.role, username: user.username });
});

app.get("/api/auth/me", authRequired, (req, res) => res.json(req.user));

/* ============================================================
 *  ESPACE CLIENT (sans compte) — accès via QR Code
 *  Le QR Code encode : http://<serveur>/menu?table=3
 * ============================================================ */
app.get("/menu", (req, res) => {
  // La page récupère ?table=X côté navigateur. On sert simplement le HTML.
  res.sendFile(path.join(__dirname, "public", "menu.html"));
});

// Liste du menu (consommée par menu.html)
app.get("/api/menu", (req, res) => {
  res.json(menu.filter((m) => m.available));
});

/* ============================================================
 *  QR CODES — à imprimer et poser sur les tables
 * ============================================================ */
// Détecte l'IP locale (LAN) pour que les téléphones puissent se connecter.
function getLanIp() {
  const ifaces = os.networkInterfaces();
  for (const name of Object.keys(ifaces)) {
    for (const iface of ifaces[name]) {
      if (iface.family === "IPv4" && !iface.internal) return iface.address;
    }
  }
  return "localhost";
}

// Page d'admin qui affiche/imprime les QR Codes des tables.
app.get("/qrcodes", (req, res) => {
  res.sendFile(path.join(__dirname, "public", "qrcodes.html"));
});

// Renvoie l'IP LAN détectée + la liste des tables (consommé par qrcodes.html).
app.get("/api/server-info", (req, res) => {
  res.json({ lanIp: getLanIp(), port: PORT, tables: Object.keys(tables).map(Number) });
});

// Génère une image PNG du QR Code pour une table donnée.
// /api/qrcode?table=3&base=http://192.168.1.10:3000
app.get("/api/qrcode", async (req, res) => {
  const table = parseInt(req.query.table, 10);
  if (!table) return res.status(400).json({ error: "Paramètre 'table' requis" });
  const base = req.query.base || `http://${getLanIp()}:${PORT}`;
  const url = `${base}/menu?table=${table}`;
  try {
    const png = await QRCode.toBuffer(url, { width: 300, margin: 2 });
    res.type("png").send(png);
  } catch (e) {
    res.status(500).json({ error: "Génération QR échouée" });
  }
});

/* ============================================================
 *  COMMANDES
 * ============================================================ */
// Le client valide sa commande pour sa table.
app.post("/api/orders", (req, res) => {
  const { table, items } = req.body || {};
  const tableNum = parseInt(table, 10);

  if (!tableNum || !Array.isArray(items) || items.length === 0) {
    return res.status(400).json({ error: "Table ou plats manquants" });
  }

  // On reconstruit la commande à partir du menu officiel (anti-triche prix).
  const lineItems = [];
  for (const it of items) {
    const dish = menu.find((m) => m.id === it.id && m.available);
    if (!dish) continue;
    const qty = Math.max(1, parseInt(it.qty, 10) || 1);
    lineItems.push({ id: dish.id, name: dish.name, price: dish.price, qty });
  }
  if (lineItems.length === 0) {
    return res.status(400).json({ error: "Aucun plat valide dans la commande" });
  }

  const total = lineItems.reduce((s, i) => s + i.price * i.qty, 0);
  const order = {
    id: orders.length + 1,
    table: tableNum,
    items: lineItems,
    total: Number(total.toFixed(2)),
    status: "Nouvelle", // Nouvelle -> En préparation -> Prête -> Servie
    createdAt: new Date().toISOString(),
  };
  orders.push(order);

  // 🔴 TEMPS RÉEL : on pousse la commande vers la cuisine / les serveurs.
  io.to("staff").emit("order:new", order);

  res.status(201).json({ message: "Commande envoyée en cuisine", order });
});

// Liste des commandes (staff uniquement)
app.get("/api/orders", authRequired, authorize("admin", "serveur"), (req, res) => {
  res.json(orders);
});

// Mise à jour du statut d'une commande (staff)
app.patch("/api/orders/:id/status", authRequired, authorize("admin", "serveur"), (req, res) => {
  const order = orders.find((o) => o.id === parseInt(req.params.id, 10));
  if (!order) return res.status(404).json({ error: "Commande introuvable" });
  order.status = req.body.status || order.status;
  io.to("staff").emit("order:update", order);
  res.json(order);
});

/* ============================================================
 *  ÉTAT DES TABLES — reçu depuis l'IA Python (OpenCV/YOLO)
 * ============================================================ */
app.post("/api/tables/status", aiKeyRequired, (req, res) => {
  // Body attendu : { tables: [ { table: 1, status: "Occupée" }, ... ] }
  const payload = req.body?.tables;
  if (!Array.isArray(payload)) {
    return res.status(400).json({ error: "Format attendu : { tables: [...] }" });
  }

  const updated = [];
  for (const t of payload) {
    const num = parseInt(t.table, 10);
    if (!tables[num]) tables[num] = { status: "Libre", updatedAt: null };
    tables[num].status = t.status === "Occupée" ? "Occupée" : "Libre";
    tables[num].updatedAt = new Date().toISOString();
    updated.push({ table: num, ...tables[num] });
  }

  // 🔴 TEMPS RÉEL : on diffuse l'état des tables au staff (plan de salle).
  io.to("staff").emit("tables:update", updated);

  res.json({ message: "État des tables mis à jour", updated });
});

// Lecture de l'état des tables (staff)
app.get("/api/tables", authRequired, authorize("admin", "serveur"), (req, res) => {
  res.json(tables);
});

/* ============================================================
 *  STATISTIQUES (Admin)
 * ============================================================ */
app.get("/api/stats", authRequired, authorize("admin"), (req, res) => {
  const revenue = orders.reduce((s, o) => s + o.total, 0);
  const occupied = Object.values(tables).filter((t) => t.status === "Occupée").length;
  // Top plats vendus
  const counter = {};
  for (const o of orders) for (const it of o.items) counter[it.name] = (counter[it.name] || 0) + it.qty;
  const topDishes = Object.entries(counter)
    .map(([name, qty]) => ({ name, qty }))
    .sort((a, b) => b.qty - a.qty)
    .slice(0, 5);
  res.json({
    totalOrders: orders.length,
    revenue: Number(revenue.toFixed(2)),
    tablesOccupied: occupied,
    tablesTotal: Object.keys(tables).length,
    topDishes,
  });
});

/* ============================================================
 *  ADMIN — Gestion du MENU
 * ============================================================ */
// Liste complète (y compris plats indisponibles)
app.get("/api/admin/menu", authRequired, authorize("admin"), (req, res) => {
  res.json(menu);
});

// Ajouter un plat
app.post("/api/admin/menu", authRequired, authorize("admin"), (req, res) => {
  const { name, category, price, image } = req.body || {};
  if (!name || !category || price == null) {
    return res.status(400).json({ error: "name, category et price sont requis" });
  }
  const id = menu.reduce((max, m) => Math.max(max, m.id), 0) + 1;
  const dish = { id, name, category, price: Number(price), available: true, image: image || "" };
  menu.push(dish);
  res.status(201).json(dish);
});

// Modifier un plat (prix, dispo, etc.)
app.patch("/api/admin/menu/:id", authRequired, authorize("admin"), (req, res) => {
  const dish = menu.find((m) => m.id === parseInt(req.params.id, 10));
  if (!dish) return res.status(404).json({ error: "Plat introuvable" });
  const { name, category, price, available, image } = req.body || {};
  if (name != null) dish.name = name;
  if (category != null) dish.category = category;
  if (price != null) dish.price = Number(price);
  if (available != null) dish.available = !!available;
  if (image != null) dish.image = image;
  res.json(dish);
});

// Supprimer un plat
app.delete("/api/admin/menu/:id", authRequired, authorize("admin"), (req, res) => {
  const idx = menu.findIndex((m) => m.id === parseInt(req.params.id, 10));
  if (idx === -1) return res.status(404).json({ error: "Plat introuvable" });
  const [removed] = menu.splice(idx, 1);
  res.json({ message: "Plat supprimé", removed });
});

/* ============================================================
 *  ADMIN — Gestion du PERSONNEL
 * ============================================================ */
// Liste du personnel (sans les hash de mot de passe)
app.get("/api/admin/staff", authRequired, authorize("admin"), (req, res) => {
  res.json(users.map((u) => ({ id: u.id, username: u.username, role: u.role })));
});

// Créer un compte (serveur ou admin)
app.post("/api/admin/staff", authRequired, authorize("admin"), (req, res) => {
  const { username, password, role } = req.body || {};
  if (!username || !password) {
    return res.status(400).json({ error: "username et password requis" });
  }
  if (users.some((u) => u.username === username)) {
    return res.status(409).json({ error: "Ce nom d'utilisateur existe déjà" });
  }
  const id = users.reduce((max, u) => Math.max(max, u.id), 0) + 1;
  const user = {
    id,
    username,
    role: role === "admin" ? "admin" : "serveur",
    passwordHash: bcrypt.hashSync(password, 10),
  };
  users.push(user);
  res.status(201).json({ id: user.id, username: user.username, role: user.role });
});

// Supprimer un compte (on protège l'admin connecté)
app.delete("/api/admin/staff/:id", authRequired, authorize("admin"), (req, res) => {
  const id = parseInt(req.params.id, 10);
  if (id === req.user.id) return res.status(400).json({ error: "Impossible de se supprimer soi-même" });
  const idx = users.findIndex((u) => u.id === id);
  if (idx === -1) return res.status(404).json({ error: "Utilisateur introuvable" });
  const [removed] = users.splice(idx, 1);
  res.json({ message: "Compte supprimé", removed: { id: removed.id, username: removed.username } });
});

/* ============================================================
 *  SOCKET.IO — le staff rejoint la room "staff"
 * ============================================================ */
io.use((socket, next) => {
  // Auth du socket via le token JWT passé dans handshake.auth.token
  const token = socket.handshake.auth?.token;
  try {
    socket.user = jwt.verify(token, JWT_SECRET);
    next();
  } catch {
    next(new Error("Auth socket refusée"));
  }
});

io.on("connection", (socket) => {
  if (["admin", "serveur"].includes(socket.user.role)) {
    socket.join("staff");
    // On envoie l'état courant à la connexion.
    socket.emit("tables:snapshot", tables);
    socket.emit("orders:snapshot", orders);
  }
  socket.on("disconnect", () => {});
});

server.listen(PORT, () => {
  console.log(`✅ Restaurant Intelligent en écoute sur http://localhost:${PORT}`);
  console.log(`   Client (QR Code) : http://localhost:${PORT}/menu?table=3`);
  console.log(`   Cuisine/Staff    : http://localhost:${PORT}/kitchen.html`);
});
