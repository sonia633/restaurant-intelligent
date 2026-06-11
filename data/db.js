/**
 * "Base de données" en mémoire pour la démo.
 * En production : remplacer par PostgreSQL / MongoDB.
 *
 * Mots de passe par défaut (hashés au démarrage) :
 *   admin   / admin123
 *   serveur / serveur123
 */
const bcrypt = require("bcryptjs");

// ---- Utilisateurs (rôles : admin, serveur) ----
const users = [
  { id: 1, username: "admin", role: "admin", passwordHash: bcrypt.hashSync("admin123", 10) },
  { id: 2, username: "serveur", role: "serveur", passwordHash: bcrypt.hashSync("serveur123", 10) },
];

// ---- Menu ----
// "image" : URL (https://...) ou Data URL (data:image/...) envoyée depuis l'admin.
// Vide = un visuel par défaut (emoji + couleur) est affiché côté client.
const menu = [
  { id: 1, name: "Salade César", category: "Entrée", price: 6.5, available: true, image: "" },
  { id: 2, name: "Soupe du jour", category: "Entrée", price: 5.0, available: true, image: "" },
  { id: 3, name: "Burger Maison", category: "Plat", price: 12.0, available: true, image: "" },
  { id: 4, name: "Pizza Margherita", category: "Plat", price: 11.0, available: true, image: "" },
  { id: 5, name: "Pâtes Carbonara", category: "Plat", price: 10.5, available: true, image: "" },
  { id: 6, name: "Tiramisu", category: "Dessert", price: 5.5, available: true, image: "" },
  { id: 7, name: "Café gourmand", category: "Dessert", price: 6.0, available: true, image: "" },
  { id: 8, name: "Limonade artisanale", category: "Boisson", price: 3.5, available: true, image: "" },
];

// ---- Commandes (créées par les clients) ----
// { id, table, items:[{id,name,price,qty}], total, status, createdAt }
const orders = [];

// ---- État des tables (mis à jour par l'IA Python) ----
// table -> { status: "Libre"|"Occupée", updatedAt }
const tables = {
  1: { status: "Libre", updatedAt: null },
  2: { status: "Libre", updatedAt: null },
  3: { status: "Libre", updatedAt: null },
};

module.exports = { users, menu, orders, tables };
