import sqlite3
from datetime import datetime

DB_PATH = "invoices.db"


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT NOT NULL,
                read_method TEXT,
                status TEXT NOT NULL,
                status_reason TEXT,
                supplier_name TEXT,
                supplier_vat_number TEXT,
                invoice_number TEXT,
                issue_date TEXT,
                due_date TEXT,
                subtotal TEXT,
                vat_amount TEXT,
                total TEXT,
                currency TEXT,
                data_json TEXT,
                processed_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL REFERENCES invoices(id),
                name TEXT NOT NULL,
                passed INTEGER NOT NULL,
                message TEXT NOT NULL
            );
        """)


def is_duplicate(vat_number, invoice_number):
    with connect() as conn:
        row = conn.execute(
            "SELECT id FROM invoices WHERE supplier_vat_number = ? AND invoice_number = ?",
            (vat_number, invoice_number),
        ).fetchone()
    return row is not None


def save_invoice(invoice, source_file, read_method, status, results):
    now = datetime.now().isoformat(timespec="seconds")
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO invoices (source_file, read_method, status, supplier_name,
                   supplier_vat_number, invoice_number, issue_date, due_date,
                   subtotal, vat_amount, total, currency, data_json, processed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                source_file, read_method, status, invoice.supplier_name,
                invoice.supplier_vat_number, invoice.invoice_number,
                invoice.issue_date.isoformat(),
                invoice.due_date.isoformat() if invoice.due_date else None,
                str(invoice.subtotal), str(invoice.vat_amount), str(invoice.total),
                invoice.currency, invoice.model_dump_json(), now,
            ),
        )
        invoice_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO checks (invoice_id, name, passed, message) VALUES (?, ?, ?, ?)",
            [(invoice_id, r.name, int(r.passed), r.message) for r in results],
        )
    return invoice_id


def save_unread(source_file, read_method, status, reason):
    now = datetime.now().isoformat(timespec="seconds")
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO invoices (source_file, read_method, status, status_reason, processed_at)
               VALUES (?, ?, ?, ?, ?)""",
            (source_file, read_method, status, reason, now),
        )
    return cur.lastrowid


def list_invoices():
    with connect() as conn:
        return conn.execute(
            "SELECT id, source_file, status, supplier_name, invoice_number, total "
            "FROM invoices ORDER BY id"
        ).fetchall()


if __name__ == "__main__":
    init_db()
    rows = list_invoices()
    if not rows:
        print("Database is empty")
    for r in rows:
        print(f"#{r['id']:<3} {r['status']:<13} {r['invoice_number'] or '-':<15} "
              f"{r['total'] or '-':>9}  {r['source_file']}")