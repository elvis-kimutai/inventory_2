from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import os

app = Flask(__name__)

# Configure PostgreSQL connection
DATABASE_URL = "postgresql://inventory_db_dbnj_user:XztJiqM6PGprH34UUIAuQIn4GmYGn7ww@dpg-cs7mfqrv2p9s73f5ei5g-a.oregon-postgres.render.com/inventory_db_dbnj"
db = psycopg2.connect(DATABASE_URL)

# Ensure the inventory table exists
cursor = db.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory (
        id SERIAL PRIMARY KEY,
        item_name VARCHAR(255) NOT NULL,
        category VARCHAR(255),
        quantity INTEGER,
        price DECIMAL(10, 2)
    );
''')
db.commit()
cursor.close()

@app.route('/')
def index():
    try:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM inventory")
        inventory = cursor.fetchall()
        cursor.close()
        return render_template('index.html', inventory=inventory)
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        return "An error occurred"

@app.route('/add_item', methods=['POST'])
def add_item():
    item_name = request.form['item-name']
    category = request.form['category']
    quantity = request.form['quantity']
    price = request.form['price']
    cursor = db.cursor()
    cursor.execute("INSERT INTO inventory (item_name, category, quantity, price) VALUES (%s, %s, %s, %s)",
                   (item_name, category, quantity, price))
    db.commit()
    cursor.close()
    return redirect(url_for('index'))

@app.route('/update_item/<int:id>', methods=['POST'])
def update_item(id):
    item_name = request.form['item-name']
    category = request.form['category']
    quantity = request.form['quantity']
    price = request.form['price']
    cursor = db.cursor()
    cursor.execute("UPDATE inventory SET item_name=%s, category=%s, quantity=%s, price=%s WHERE id=%s",
                   (item_name, category, quantity, price, id))
    db.commit()
    cursor.close()
    return redirect(url_for('index'))

@app.route('/delete_item/<int:id>', methods=['POST'])
def delete_item(id):
    cursor = db.cursor()
    cursor.execute("DELETE FROM inventory WHERE id=%s", (id,))
    db.commit()
    cursor.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
