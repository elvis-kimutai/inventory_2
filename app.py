from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import os
from transformers import pipeline

app = Flask(__name__)

# Configure PostgreSQL connection
DATABASE_URL = "postgresql://inventory_db_dbnj_user:XztJiqM6PGprH34UUIAuQIn4GmYGn7ww@dpg-cs7mfqrv2p9s73f5ei5g-a.oregon-postgres.render.com/inventory_db_dbnj"
db = psycopg2.connect(DATABASE_URL)

# Ensure the inventory table exists and add 'description' column if it is missing
cursor = db.cursor()

# Check if 'description' column exists
cursor.execute("""
    SELECT column_name
    FROM information_schema.columns 
    WHERE table_name='inventory' AND column_name='description';
""")

# If description column does not exist, alter the table to add it
if cursor.fetchone() is None:
    cursor.execute("ALTER TABLE inventory ADD COLUMN description TEXT;")
    db.commit()

# Create table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory (
        id SERIAL PRIMARY KEY,
        item_name VARCHAR(255) NOT NULL,
        category VARCHAR(255),
        quantity INTEGER,
        price DECIMAL(10, 2),
        description TEXT
    );
''')
db.commit()
cursor.close()

# Initialize the Hugging Face pipeline for text generation with a smaller model
description_generator = pipeline("text-generation", model="distilgpt2")  # Using distilgpt2 for lower memory consumption

# Function to generate item description using Hugging Face
def generate_description(item_name, category, quantity):
    prompt = (
        f"Please write a simple yet detailed description of an inventory item. "
        f"The item is called '{item_name}', it belongs to the '{category}' category, "
        f"and there are {quantity} available. "
        f"Include its purpose, features, and any other relevant details that would inform potential buyers."
    )
    response = description_generator(prompt, max_length=150, num_return_sequences=1)
    return response[0]['generated_text'].strip()
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
    
    # Generate description using Hugging Face model
    description = generate_description(item_name, category, quantity)
    
    cursor = db.cursor()
    cursor.execute("INSERT INTO inventory (item_name, category, quantity, price, description) VALUES (%s, %s, %s, %s, %s)",
                   (item_name, category, quantity, price, description))
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

