#!/usr/bin/env python3
"""IT Help Desk Ticket System: a command-line ticketing tool (Python + SQLite)."""
import argparse
import sqlite3
from datetime import datetime

DB_FILE = "helpdesk.db"
PRIORITIES = ["low", "medium", "high", "critical"]
STATUSES = ["open", "in_progress", "resolved", "closed"]
CATEGORIES = ["hardware", "software", "network", "account", "security", "other"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    requester TEXT NOT NULL,
    assignee TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id),
    author TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def _now():
    return datetime.now().isoformat(timespec="seconds")


def connect(db=DB_FILE):
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def add_ticket(conn, title, description, category, priority, requester):
    now = _now()
    cur = conn.execute(
        "INSERT INTO tickets (title, description, category, priority, status,"
        " requester, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
        (title, description, category, priority, "open", requester, now, now),
    )
    conn.commit()
    return cur.lastrowid


def get_ticket(conn, ticket_id):
    return conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()


def list_tickets(conn, status=None, priority=None, category=None):
    query, params = "SELECT * FROM tickets WHERE 1=1", []
    for column, value in (("status", status), ("priority", priority), ("category", category)):
        if value:
            query += f" AND {column} = ?"  # column names come from the fixed tuple above
            params.append(value)
    query += (" ORDER BY CASE priority WHEN 'critical' THEN 0 WHEN 'high' THEN 1"
              " WHEN 'medium' THEN 2 ELSE 3 END, created_at")
    return conn.execute(query, params).fetchall()


def update_ticket(conn, ticket_id, status=None, priority=None, assignee=None):
    fields = {"status": status, "priority": priority, "assignee": assignee}
    fields = {k: v for k, v in fields.items() if v is not None}
    if not fields or not get_ticket(conn, ticket_id):
        return False
    sets = ", ".join(f"{k} = ?" for k in fields) + ", updated_at = ?"
    conn.execute(f"UPDATE tickets SET {sets} WHERE id = ?",
                 (*fields.values(), _now(), ticket_id))
    conn.commit()
    return True


def add_comment(conn, ticket_id, author, body):
    if not get_ticket(conn, ticket_id):
        return False
    conn.execute("INSERT INTO comments (ticket_id, author, body, created_at) VALUES (?,?,?,?)",
                 (ticket_id, author, body, _now()))
    conn.commit()
    return True


def get_comments(conn, ticket_id):
    return conn.execute("SELECT * FROM comments WHERE ticket_id = ? ORDER BY id",
                        (ticket_id,)).fetchall()


def report(conn):
    result = {}
    for column in ("status", "priority", "category"):
        rows = conn.execute(
            f"SELECT {column} AS k, COUNT(*) AS n FROM tickets GROUP BY {column}").fetchall()
        result[column] = {r["k"]: r["n"] for r in rows}
    return result


def build_parser():
    p = argparse.ArgumentParser(description="IT Help Desk Ticket System")
    p.add_argument("--db", default=DB_FILE, help="SQLite database file")
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("add", help="create a ticket")
    a.add_argument("title")
    a.add_argument("-d", "--description", default="")
    a.add_argument("-c", "--category", choices=CATEGORIES, default="other")
    a.add_argument("-p", "--priority", choices=PRIORITIES, default="medium")
    a.add_argument("-r", "--requester", required=True)

    l = sub.add_parser("list", help="list tickets (most urgent first)")
    l.add_argument("--status", choices=STATUSES)
    l.add_argument("--priority", choices=PRIORITIES)
    l.add_argument("--category", choices=CATEGORIES)

    s = sub.add_parser("show", help="show a ticket with its comments")
    s.add_argument("id", type=int)

    u = sub.add_parser("update", help="change status, priority or assignee")
    u.add_argument("id", type=int)
    u.add_argument("--status", choices=STATUSES)
    u.add_argument("--priority", choices=PRIORITIES)
    u.add_argument("--assignee")

    c = sub.add_parser("comment", help="add a comment to a ticket")
    c.add_argument("id", type=int)
    c.add_argument("-a", "--author", required=True)
    c.add_argument("-m", "--message", required=True)

    sub.add_parser("report", help="summary statistics")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    conn = connect(args.db)

    if args.command == "add":
        tid = add_ticket(conn, args.title, args.description, args.category,
                         args.priority, args.requester)
        print(f"Ticket #{tid} created.")
    elif args.command == "list":
        rows = list_tickets(conn, args.status, args.priority, args.category)
        if not rows:
            print("No tickets found.")
        for r in rows:
            print(f"#{r['id']:<4} {r['priority']:<9} {r['status']:<12} "
                  f"{r['category']:<9} {r['title']}")
    elif args.command == "show":
        t = get_ticket(conn, args.id)
        if not t:
            raise SystemExit(f"Ticket #{args.id} not found.")
        for key in t.keys():
            print(f"{key:<12}: {t[key]}")
        for c in get_comments(conn, args.id):
            print(f"  [{c['created_at']}] {c['author']}: {c['body']}")
    elif args.command == "update":
        ok = update_ticket(conn, args.id, args.status, args.priority, args.assignee)
        print("Updated." if ok else "Nothing updated (check ticket id / options).")
    elif args.command == "comment":
        ok = add_comment(conn, args.id, args.author, args.message)
        print("Comment added." if ok else f"Ticket #{args.id} not found.")
    elif args.command == "report":
        for section, counts in report(conn).items():
            print(f"By {section}:")
            for key, n in counts.items():
                print(f"  {key:<12} {n}")


if __name__ == "__main__":
    main()
