import Database from "better-sqlite3";
import path from "path";
import fs from "fs";

const DB_DIR = path.join(process.cwd(), "data");
const DB_PATH = path.join(DB_DIR, "employeeLeave.db");

// Ensure data directory exists
if (!fs.existsSync(DB_DIR)) {
  fs.mkdirSync(DB_DIR, { recursive: true });
}

let db: Database.Database;

function getDb(): Database.Database {
  if (!db) {
    db = new Database(DB_PATH);
    db.pragma("journal_mode = WAL");
    db.pragma("foreign_keys = ON");

    // Initialize tables
    db.exec(`
      CREATE TABLE IF NOT EXISTS employees (
        id TEXT NOT NULL PRIMARY KEY,
        firstName TEXT NOT NULL,
        lastName TEXT NOT NULL,
        startDate TEXT NOT NULL
      )
    `);

    db.exec(`
      CREATE TABLE IF NOT EXISTS annualLeave (
        rowid INTEGER PRIMARY KEY AUTOINCREMENT,
        id TEXT NOT NULL,
        firstName TEXT,
        leaveTaken REAL,
        leaveStart TEXT,
        leaveEnd TEXT,
        comment TEXT,
        FOREIGN KEY (id) REFERENCES employees (id) ON DELETE CASCADE
      )
    `);

    db.exec(`
      CREATE TABLE IF NOT EXISTS sickLeave (
        rowid INTEGER PRIMARY KEY AUTOINCREMENT,
        id TEXT NOT NULL,
        firstName TEXT,
        leaveTaken REAL,
        leaveStart TEXT,
        leaveEnd TEXT,
        comment TEXT,
        FOREIGN KEY (id) REFERENCES employees (id) ON DELETE CASCADE
      )
    `);
  }
  return db;
}

export default getDb;
