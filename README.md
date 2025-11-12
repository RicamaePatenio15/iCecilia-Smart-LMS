# iCecilia Smart Library Management System (Prototype)

Maroon-themed Flask app that works with XAMPP's MySQL (MariaDB). Features:
- Librarian approval workflow for staff
- Inventory management (books)
- Student registry (with RFID/FID code)
- Borrow/Return via book QR + student RFID
- Reports & CSV export
- Branding and login background per provided assets

## 1) Setup (XAMPP + Python)

1. Start **XAMPP** (Apache + MySQL).
2. Open **phpMyAdmin**, run `sql/schema.sql`. This creates DB + tables and seeds:
   - Role: librarian (id=1), staff (id=2)
   - Default librarian: **username `Admin`**, **password `Smartcecilian`** (SHA-256)
3. Create & activate a Python virtual env and install deps:

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

4. Run the app:

```bash
export FLASK_APP=app.py  # Windows: set FLASK_APP=app.py
python app.py
```

5. Visit `http://127.0.0.1:5000/`

## 2) Roles and Flow

- **Librarian** (Admin/Smartcecilian) can:
  - Approve/reject staff registrations
  - Manage books (add/update basic)
  - Register students (assign RFID/FID codes)
  - View reports & export CSV

- **Staff** can:
  - Borrow/Return using Book QR + Student RFID
  - View reports

**Every staff sign-in requires librarian approval first** (`status='active'`).

## 3) QR & RFID

- Book QR uses `tbl_book.qr_code`. For the prototype, type it in manually on the Borrow/Return page.
- Student RFID is `tbl_student.fid_code` (the value that an RFID reader will supply).

To add real camera/QR decoding, plug a browser library (e.g., `html5-qrcode`) and call `/api/library/scan` with:
```json
{ "typ":"BOOK", "qr":"BK-...", "id": 123, "ts": 1730832000, "student_fid":"RF-001" }
```

## 4) File Map

- `app.py` – Flask routes/API
- `config.py` – DB credentials for XAMPP MySQL
- `sql/schema.sql` – DB schema matching your ERD
- `templates/` – Jinja pages
- `static/css/styles.css` – maroon theme
- `static/img/logo.png` – provided logo (top-left)
- `static/img/login_bg.jpg` – provided school photo (login background)

## 5) Security Notes

- Passwords are stored as SHA‑256 hashes (see `schema.sql` seed and `app.py` login).
- For production, switch to salted hash (bcrypt/argon2), HTTPS, and CSRF protection.

cd C:\Users\ride1\Downloads\iCecilia_Smart_Library_Prototype
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python app.py

