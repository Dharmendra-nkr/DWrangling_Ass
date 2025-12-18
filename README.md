# Data Wrangling Assignment

This repository contains two Flask-based web applications demonstrating database management with different database systems.

## Projects

### 1. [Mongo_nosql](./Mongo_nosql) - MongoDB Implementation
A Flask application with MongoDB backend providing user authentication and dynamic collection management.

**Key Features:**
- User signup/login with password hashing
- Dynamic collection creation
- Document-based storage with flexible schema
- CRUD operations on MongoDB collections
- Web dashboard for managing documents

**Technology Stack:**
- Flask
- MongoDB (PyMongo)
- Jinja2 Templates
- Bootstrap CSS

[View Documentation →](./Mongo_nosql/README.md)

---

### 2. [Postres_sql](./Postres_sql) - PostgreSQL Implementation
A Flask application with PostgreSQL backend providing user authentication and table management.

**Key Features:**
- User signup/login with password hashing
- Dynamic table creation
- Relational database with structured schemas
- CRUD operations on PostgreSQL tables
- Web dashboard for managing records
- RESTful API endpoints

**Technology Stack:**
- Flask
- PostgreSQL (psycopg)
- Jinja2 Templates
- Bootstrap CSS

[View Documentation →](./Postres_sql/README.md)

---

## Quick Comparison

| Feature | MongoDB Version | PostgreSQL Version |
|---------|----------------|-------------------|
| Data Model | Document-based (NoSQL) | Relational (SQL) |
| Schema | Flexible, dynamic | Structured, predefined |
| Primary Key | `_id` (auto-generated) | `id` (serial) |
| Query Language | MongoDB queries | SQL |
| Scalability | Horizontal scaling | Vertical scaling |
| Use Case | Unstructured/semi-structured data | Structured data with relationships |

## Getting Started

Each project has its own setup instructions and dependencies. Navigate to the respective folder and follow the README:

1. **MongoDB Project**: `cd Mongo_nosql` → [Setup Instructions](./Mongo_nosql/README.md)
2. **PostgreSQL Project**: `cd Postres_sql` → [Setup Instructions](./Postres_sql/README.md)

## Prerequisites

- Python 3.8 or higher
- MongoDB Server (for Mongo_nosql project)
- PostgreSQL Server (for Postres_sql project)

## Project Structure

```
DW_ASS/
├── Mongo_nosql/              # MongoDB implementation
│   ├── app.py               # Flask application
│   ├── db.py                # Database operations
│   ├── requirements.txt     # Python dependencies
│   ├── templates/           # HTML templates
│   └── static/              # CSS files
│
├── Postres_sql/             # PostgreSQL implementation
│   ├── app.py               # Flask application
│   ├── db.py                # Database operations
│   ├── requirements.txt     # Python dependencies
│   ├── templates/           # HTML templates
│   └── static/              # CSS files
│
└── README.md                # This file
```

## Features Common to Both Projects

- 🔐 **User Authentication**: Secure signup/login with password hashing
- 📊 **Dashboard Interface**: User-friendly web interface for data management
- ✏️ **CRUD Operations**: Create, Read, Update, Delete functionality
- 🔄 **Dynamic Management**: Create tables/collections on-the-fly
- 🎨 **Responsive Design**: Clean UI with Bootstrap styling
- 🔒 **Session Management**: Secure session handling with Flask

## License

This project is for educational purposes as part of a Data Wrangling assignment.

## Author

Dharmendra N K R

---

**Repository**: https://github.com/Dharmendra-nkr/DWrangling_Ass.git
