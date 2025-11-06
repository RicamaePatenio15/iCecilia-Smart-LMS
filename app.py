from flask import Flask, request, render_template, redirect, url_for, session, send_file, Response
from datetime import datetime, date
import csv, io, hashlib, hmac, base64
import mysql.connector
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, SECRET_KEY, QR_HMAC_SECRET

app = Flask(__name__)
app.secret_key = SECRET_KEY

def db():
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )

def sha256(s:str)->str:
    return hashlib.sha256(s.encode()).hexdigest()

def valid_sig(qr, book_id, ts, sig):
    msg = f"{qr}|{book_id}|{ts}".encode()
    mac = hmac.new(QR_HMAC_SECRET, msg, hashlib.sha256).digest()
    return base64.b64encode(mac).decode()==sig

@app.route('/')
def login():
    return render_template('login.html')

@app.post('/login')
def do_login():
    role = request.form.get('as') or 'librarian'
    username = request.form.get('username')
    password = request.form.get('password')
    con = db(); cur = con.cursor(dictionary=True)
    cur.execute("""
        SELECT u.*, r.role_name FROM tbl_user u
        JOIN tbl_role r ON r.role_id=u.role_id
        WHERE username=%s AND password=%s
    """, (username, sha256(password)))
    u = cur.fetchone()
    if not u:
        return render_template('login.html', error='Invalid credentials')
    if role=='librarian' and u['role_name']!='librarian':
        return render_template('login.html', error='Not a librarian account')
    if role=='staff' and u['role_name']!='staff':
        return render_template('login.html', error='Not a staff account')
    if u['status']!='active':
        return render_template('login.html', error='Account is not active. Librarian approval required.')
    session['user']=u['user_id']
    session['user_name']=u['first_name']
    session['role']=u['role_name']
    return redirect(url_for('librarian_dashboard' if u['role_name']=='librarian' else 'staff_dashboard'))

@app.get('/logout-confirm')
def logout_confirm():
    if not session.get('user'): return redirect(url_for('login'))
    return render_template('logout_confirm.html')

@app.get('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))

# Registration (staff)
@app.route('/register-staff', methods=['GET','POST'])
def staff_register():
    created=False
    if request.method=='POST':
        f = request.form
        con = db(); cur = con.cursor()
        # staff role id = 2
        cur.execute("""INSERT INTO tbl_user (role_id, first_name, last_name, username, password, status)
                      VALUES (2,%s,%s,%s,%s,'pending')""",
                      (f['first_name'], f.get('last_name'), f['username'], sha256(f['password'])))
        con.commit()
        created=True
    return render_template('staff_register.html', created=created)

# Librarian-only views
def require_librarian():
    return session.get('role')=='librarian'

@app.get('/librarian')
def librarian_dashboard():
    if not require_librarian(): return redirect(url_for('login'))
    return render_template('librarian_dashboard.html')

@app.route('/librarian/staff-management', methods=['GET'])
def staff_management():
    if not require_librarian(): return redirect(url_for('login'))
    con=db(); cur=con.cursor(dictionary=True)
    cur.execute("SELECT * FROM tbl_user WHERE role_id=2 AND status='pending' ORDER BY user_id DESC")
    pending = cur.fetchall()
    cur.execute("SELECT * FROM tbl_user WHERE role_id=2 AND status='active' ORDER BY user_id DESC")
    staff = cur.fetchall()
    return render_template('staff_management.html', pending=pending, staff=staff)

@app.post('/librarian/staff/approve/<int:user_id>')
def approve_staff(user_id):
    if not require_librarian(): return redirect(url_for('login'))
    con=db(); cur=con.cursor()
    cur.execute("UPDATE tbl_user SET status='active' WHERE user_id=%s",(user_id,))
    con.commit()
    return redirect(url_for('staff_management'))

@app.post('/librarian/staff/deactivate/<int:user_id>')
def deactivate_staff(user_id):
    if not require_librarian(): return redirect(url_for('login'))
    con=db(); cur=con.cursor()
    cur.execute("UPDATE tbl_user SET status='inactive' WHERE user_id=%s",(user_id,))
    con.commit()
    return redirect(url_for('staff_management'))

@app.route('/librarian/inventory', methods=['GET','POST'])
def inventory_management():
    if not require_librarian(): return redirect(url_for('login'))
    con=db(); cur=con.cursor(dictionary=True)
    if request.method=='POST':
        f=request.form
        cur.execute("INSERT INTO tbl_book (qr_code,title,author,category_id,publisher,year_published) VALUES (%s,%s,%s,%s,%s,%s)",
                    (f.get('qr_code') or f"BK-{int(datetime.now().timestamp())}", f['title'], f.get('author'),
                     f['category_id'], f.get('publisher'), f.get('year') or None))
        con.commit()
    # ensure some categories exist
    cur.execute("INSERT IGNORE INTO tbl_category (category_id, category_name) VALUES (1,'MIS'),(2,'IOT'),(3,'Software Engineering')")
    con.commit()
    cur.execute("SELECT * FROM tbl_category ORDER BY category_name"); categories = cur.fetchall()
    cur.execute("""SELECT b.*, c.category_name FROM tbl_book b JOIN tbl_category c ON c.category_id=b.category_id ORDER BY b.book_id DESC""")
    books = cur.fetchall()
    return render_template('inventory.html', categories=categories, books=books)

@app.route('/librarian/students', methods=['GET','POST'])
def students():
    if not require_librarian(): return redirect(url_for('login'))
    con=db(); cur=con.cursor(dictionary=True)
    if request.method=='POST':
        f=request.form
        cur.execute("""INSERT INTO tbl_student (fid_code, first_name, last_name, year_level, contact_no, status)
                      VALUES (%s,%s,%s,%s,%s,%s)""", (f['fid_code'], f['first_name'], f.get('last_name'),
                              f.get('year_level'), f.get('contact_no'), f.get('status')))
        con.commit()
    cur.execute("SELECT * FROM tbl_student ORDER BY student_id DESC")
    students = cur.fetchall()
    return render_template('students.html', students=students)

# Staff routes
def require_staff():
    return session.get('role')=='staff'

@app.get('/staff')
def staff_dashboard():
    if not require_staff(): return redirect(url_for('login'))
    return render_template('staff_dashboard.html')

@app.get('/staff/borrow-return')
def borrow_return():
    if not require_staff(): return redirect(url_for('login'))
    return render_template('borrow_return.html')

# Scan API (borrow/return)
@app.post('/api/library/scan')
def scan_api():
    if not session.get('user'): return ("Unauthorized", 401)
    data = request.get_json(force=True)
    qr = data.get('qr'); book_id = data.get('id'); ts = data.get('ts')
    con=db(); cur=con.cursor(dictionary=True)

    # Find book by qr or id
    if book_id:
        cur.execute("SELECT * FROM tbl_book WHERE book_id=%s",(book_id,))
    else:
        cur.execute("SELECT * FROM tbl_book WHERE qr_code=%s",(qr,))
    book = cur.fetchone()
    if not book:
        return {"ok":False, "error":"Book not found"}, 404

    # Find student by fid_code
    cur.execute("SELECT * FROM tbl_student WHERE fid_code=%s",(data['student_fid'],))
    student = cur.fetchone()
    if not student:
        return {"ok":False, "error":"Student not found"}, 404

    # Check active borrow
    cur.execute("SELECT * FROM tbl_borrow WHERE book_id=%s AND returned_date IS NULL ORDER BY borrowed_date DESC LIMIT 1",(book['book_id'],))
    active = cur.fetchone()
    now = datetime.now()

    if active:
        # Return
        cur.execute("UPDATE tbl_borrow SET returned_date=%s, processed_by=%s WHERE borrow_id=%s",
                    (now, session['user'], active['borrow_id']))
        cur.execute("UPDATE tbl_book SET status='available' WHERE book_id=%s", (book['book_id'],))
        cur.execute("INSERT INTO tbl_inventory_log (user_id, book_id, action, action_date) VALUES (%s,%s,%s,%s)",
                    (session['user'], book['book_id'], 'return', now))
        con.commit()
        return {"ok":True, "action":"return", "book":book['title'], "student":student['first_name']}

    else:
        # Borrow
        cur.execute("INSERT INTO tbl_borrow (student_id, book_id, borrowed_date, processed_by) VALUES (%s,%s,%s,%s)",
                    (student['student_id'], book['book_id'], now, session['user']))
        cur.execute("UPDATE tbl_book SET status='borrowed' WHERE book_id=%s", (book['book_id'],))
        cur.execute("INSERT INTO tbl_inventory_log (user_id, book_id, action, action_date) VALUES (%s,%s,%s,%s)",
                    (session['user'], book['book_id'], 'borrow', now))
        con.commit()
        return {"ok":True, "action":"borrow", "book":book['title'], "student":student['first_name']}

# Reports
@app.get('/reports')
def reports():
    if not session.get('user'): return redirect(url_for('login'))
    con=db(); cur=con.cursor(dictionary=True)
    cur.execute("""
      SELECT s.first_name, s.last_name, s.fid_code, b.title, b.qr_code, br.borrowed_date, br.returned_date
      FROM tbl_borrow br
      JOIN tbl_student s ON s.student_id=br.student_id
      JOIN tbl_book b ON b.book_id=br.book_id
      ORDER BY br.borrowed_date DESC
    """)
    records = cur.fetchall()
    return render_template('reports.html', records=records)

@app.get('/export/csv')
def export_csv():
    if not session.get('user'): return redirect(url_for('login'))
    con=db(); cur=con.cursor()
    cur.execute("""
      SELECT s.first_name, s.last_name, s.fid_code, b.title, b.qr_code, br.borrowed_date, br.returned_date
      FROM tbl_borrow br
      JOIN tbl_student s ON s.student_id=br.student_id
      JOIN tbl_book b ON b.book_id=br.book_id
      ORDER BY br.borrowed_date DESC
    """)
    headers=[d[0] for d in cur.description]
    rows=cur.fetchall()
    si=io.StringIO(); cw=csv.writer(si)
    cw.writerow(headers); cw.writerows(rows)
    out=io.BytesIO(si.getvalue().encode())
    return send_file(out, mimetype='text/csv', as_attachment=True, download_name='borrow_records.csv')

# Placeholder for settings route
@app.get('/settings')
def settings():
    if not require_librarian(): return redirect(url_for('login'))
    return render_template('settings.html')

# Routes shortcuts for forms
app.add_url_rule('/librarian/staff-management/approve/<int:user_id>', view_func=approve_staff, methods=['POST'], endpoint='approve_staff')
app.add_url_rule('/librarian/staff-management/deactivate/<int:user_id>', view_func=deactivate_staff, methods=['POST'], endpoint='deactivate_staff')

@app.get('/login/librarian')
def librarian_login():
    return render_template('login_librarian.html')

@app.get('/login/staff')
def staff_login():
    return render_template('login_staff.html')

if __name__=='__main__':
    app.run(debug=True)
