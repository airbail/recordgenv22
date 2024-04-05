from flask import Flask, render_template, request, redirect, send_from_directory, url_for, flash
from werkzeug.utils import secure_filename
import sqlite3
import os
import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Define upload folder inside templates directory
UPLOAD_FOLDER = os.path.join('templates', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure Flask serves the static files correctly
@app.route('/templates/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Initialize database
conn = sqlite3.connect('outward_management.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS letters
             (id INTEGER PRIMARY KEY AUTOINCREMENT, doc_number TEXT UNIQUE, date TEXT, sender TEXT, recipient TEXT, subject TEXT, file_path TEXT, is_deleted INTEGER)''')
conn.commit()

class LetterManagementSystem:
    def generate_document_number(self, record_id):
        return f"DOC-{record_id}"

letter_system = LetterManagementSystem()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        sender = request.form.get('sender')
        recipient = request.form.get('recipient')
        subject = request.form.get('subject')
        if not sender or not recipient or not subject:
            flash('Sender, recipient, and subject are required fields.')
            return redirect(request.url)
        
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Save record to database
        c.execute("INSERT INTO letters (date, sender, recipient, subject) VALUES (?, ?, ?, ?)", (date, sender, recipient, subject))
        conn.commit()

        record_id = c.lastrowid
        document_number = letter_system.generate_document_number(record_id)
        records = get_all_records()
        return render_template('index.html', document_number=document_number, records=records)

    records = get_all_records()
    return render_template('index.html', records=records)


@app.route('/upload/<document_number>', methods=['POST'])
def upload_pdf(document_number):
    if request.method == 'POST':
        if 'pdf' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['pdf']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        # Save file to uploads folder
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Parse the record ID from the document number
        try:
            record_id = int(document_number.split('-')[1])
        except IndexError:
            flash('Invalid document number format')
            return redirect(url_for('index'))

        # Update record in the database with file path
        c.execute("UPDATE letters SET file_path=? WHERE id=?", (file_path, record_id))
        conn.commit()

        flash(f'PDF uploaded successfully. File path: {file_path}')
        return redirect(url_for('index'))
    
@app.route('/view-files')
def view_files():
    # Get all file names in the uploads folder
    file_names = os.listdir(app.config['UPLOAD_FOLDER'])
    file_names.sort(reverse=True)  # Sort files in reverse order (latest first)
    return render_template('view_files.html', file_names=file_names)
    

@app.route('/delete/<int:record_id>')
def delete_record(record_id):
    c.execute("UPDATE letters SET is_deleted=1 WHERE id=?", (record_id,))
    conn.commit()
    flash('Record deleted successfully')
    return redirect(url_for('index'))

def get_all_records():
    c.execute("SELECT * FROM letters WHERE is_deleted = 0 ORDER BY id DESC")
    return c.fetchall()

if __name__ == '__main__':
    app.run(debug=True)
