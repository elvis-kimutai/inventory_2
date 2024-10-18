
from flask import Flask, render_template, request, redirect, url_for, jsonify
import psycopg2
import os
import requests
import json

app = Flask(__name__)

# Configure PostgreSQL connection
DATABASE_URL = "postgresql://inventory_db_dbnj_user:XztJiqM6PGprH34UUIAuQIn4GmYGn7ww@dpg-cs7mfqrv2p9s73f5ei5g-a.oregon-postgres.render.com/inventory_db_dbnj"
db = psycopg2.connect(DATABASE_URL)

# API Configuration
API_KEY = "721c2dc789msh25c5eea0129653dp11e829jsn3b70dbeda388"
API_HOST = "chat-gpt26.p.rapidapi.com"
API_URL = "https://rapidapi.com"

# Database initialization
def init_db():
    cursor = db.cursor()
    
    # Check if 'description' column exists
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns 
        WHERE table_name='inventory' AND column_name='description';
    """)
    
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

# Initialize database
init_db()

def generate_product_description(item_name, category, quantity):
    """
    Generate a detailed product description focusing on features and performance
    """
    try:
        headers = {
            "X-RapidAPI-Key": API_KEY,
            "X-RapidAPI-Host": API_HOST,
            "Content-Type": "application/json"
        }
        
        prompt = {
            "prompt": f"""Generate a detailed product description for {item_name}, focusing on its features and performance:

                      Product: {item_name}
                      Category: {category}
                      Available Quantity: {quantity}
                      
                      Please include:
                      1. Key features and specifications (be very specific)
                      2. Performance metrics and capabilities
                      3. Unique selling points or advantages
                      4. Technical details relevant to the product type
                      5. How these features benefit the user
                      
                      Format the description as a list of bullet points for clarity.
                      Be specific, technical, and focus on factual information about the product's capabilities and performance.""",
            "max_tokens": 300,
            "temperature": 0.5
        }
        
        response = requests.post(
            API_URL,
            headers=headers,
            json=prompt,
            timeout=20
        )
        
        if response.status_code == 200:
            try:
                result = response.json()
                description = result.get('generated_text', '')
                if description:
                    return description.strip()
            except json.JSONDecodeError:
                print("Failed to parse API response")
        
        # Fallback description focusing on features and performance
        return f"""Key features and performance of {item_name} ({category}):
• High-performance device suitable for various applications
• Advanced technology ensuring reliable operation
• User-friendly interface for easy navigation and control
• Optimized for efficiency and productivity
• Durable construction for long-lasting use
• Compatible with industry-standard software and hardware
• Energy-efficient design for reduced operating costs
• Available quantity: {quantity} units
For detailed specifications and performance metrics, please contact our sales team."""
        
    except requests.RequestException as e:
        print(f"API Request Error: {e}")
        return f"""Features and performance highlights of {item_name} ({category}):
• Cutting-edge technology for optimal performance
• Versatile functionality suitable for diverse applications
• Intuitive controls for enhanced user experience
• Robust build quality ensuring durability
• Designed for seamless integration with existing systems
• Energy-efficient operation
• Current stock: {quantity} units
Contact us for comprehensive specifications and performance data."""

@app.route('/')
def index():
    try:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM inventory ORDER BY id DESC")
        inventory = cursor.fetchall()
        cursor.close()
        return render_template('index.html', inventory=inventory)
    except Exception as e:
        db.rollback()
        print(f"Database Error: {e}")
        return "An error occurred while fetching inventory"

@app.route('/add_item', methods=['POST'])
def add_item():
    try:
        item_name = request.form['item-name']
        category = request.form['category']
        quantity = request.form.get('quantity', type=int)
        price = request.form.get('price', type=float)
        description = request.form.get('description', '')
        
        # Input validation
        if not all([item_name, category, quantity is not None, price is not None]):
            return "All fields are required", 400
        
        cursor = db.cursor()
        cursor.execute(
            """INSERT INTO inventory 
               (item_name, category, quantity, price, description) 
               VALUES (%s, %s, %s, %s, %s)""",
            (item_name, category, quantity, price, description)
        )
        db.commit()
        cursor.close()
        return redirect(url_for('index'))
        
    except Exception as e:
        db.rollback()
        print(f"Error adding item: {e}")
        return "An error occurred while adding the item", 500

@app.route('/update_item/<int:id>', methods=['POST'])
def update_item(id):
    try:
        item_name = request.form['item-name']
        category = request.form['category']
        quantity = request.form.get('quantity', type=int)
        price = request.form.get('price', type=float)
        description = request.form.get('description', '')
        
        # Input validation
        if not all([item_name, category, quantity is not None, price is not None]):
            return "All fields are required", 400
        
        cursor = db.cursor()
        cursor.execute(
            """UPDATE inventory 
               SET item_name=%s, category=%s, quantity=%s, price=%s, description=%s 
               WHERE id=%s""",
            (item_name, category, quantity, price, description, id)
        )
        db.commit()
        cursor.close()
        return redirect(url_for('index'))
        
    except Exception as e:
        db.rollback()
        print(f"Error updating item: {e}")
        return "An error occurred while updating the item", 500

@app.route('/delete_item/<int:id>', methods=['POST'])
def delete_item(id):
    try:
        cursor = db.cursor()
        cursor.execute("DELETE FROM inventory WHERE id=%s", (id,))
        db.commit()
        cursor.close()
        return redirect(url_for('index'))
    except Exception as e:
        db.rollback()
        print(f"Error deleting item: {e}")
        return "An error occurred while deleting the item", 500

@app.route('/generate_description', methods=['POST'])
def generate_description():
    data = request.json
    item_name = data['item_name']
    category = data['category']
    quantity = data['quantity']
    
    description = generate_product_description(item_name, category, quantity)
    
    return jsonify({'description': description})

if __name__ == '__main__':
    app.run(debug=True)