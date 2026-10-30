# IT Help Desk Ticket System

A lightweight command-line help desk built with **Python** and **SQLite**. It models the daily workflow of an IT support team: logging issues, prioritising them, assigning technicians, tracking status, and reporting.

## Features
- Create tickets with category (hardware, software, network, account, security) and priority
- List tickets sorted by urgency, with filters by status, priority and category
- Update status / priority / assignee, and add comments to a ticket
- Summary report (tickets by status, priority and category)
- No external dependencies, only the Python standard library

## Requirements
Python 3.8+

## Usage
```bash
python helpdesk.py add "Cannot connect to Wi-Fi" -c network -p high -r sara
python helpdesk.py list --status open
python helpdesk.py update 1 --status in_progress --assignee abdullah
python helpdesk.py comment 1 -a abdullah -m "Replaced the network cable"
python helpdesk.py show 1
python helpdesk.py report
```

## Run the tests
```bash
python -m unittest -v
```

## Skills demonstrated
IT support workflow (incident tracking and prioritisation), relational database design (two related tables, parameterised SQL queries), Python scripting, unit testing.

## Database schema
`tickets(id, title, description, category, priority, status, requester, assignee, created_at, updated_at)`
`comments(id, ticket_id, author, body, created_at)`

## License
MIT
