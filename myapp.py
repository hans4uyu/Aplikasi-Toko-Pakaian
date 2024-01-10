from flask import Flask, render_template, session, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
from datetime import datetime
import os


app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


app.secret_key = '!@#$%'

# database config
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "db_tokopakaian"


mysql = MySQL(app)

@app.route('/', methods=['GET', 'POST'])
def login():
    user_type = "user" 
    if request.method == 'POST' and 'inpEmail' in request.form and 'inpPass' in request.form:
        email = request.form['inpEmail']
        passwd = request.form['inpPass']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, passwd))
        result = cur.fetchone()
        cur.close()

        if result:
            user_type = result[4]

            if user_type == 'user':
                session['is_logged_in'] = True
                session['username'] = result[1]
                if 'cart' not in session:
                    session['cart'] = []
                return redirect(url_for('home'))
                
            elif user_type == 'admin':
                session['is_logged_in_admin'] = True
                session['username'] = result[1]
                return redirect(url_for('admin'))
        else:
            return render_template('login.html')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        regusn = request.form['inpUsn']
        regmail = request.form['inpEmail']
        regpasswd = request.form['inpPass']
        regpasswd2 = request.form['inpPass2']
        if regpasswd == regpasswd2:
            mycursor = mysql.connection.cursor()
            query = "INSERT INTO users (username, password, email, user_type) VALUES (%s, %s, %s, 'user')"
            mycursor.execute(query, (regusn, regpasswd, regmail))
            mysql.connection.commit()
            return redirect(url_for('login'))
        else:
            return "email tidak valid"
    else:
        return render_template('register.html')

def get_some_product_data():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM produk ORDER BY RAND() LIMIT 1")
        product = cur.fetchone()
        cur.close()
        return product
    except Exception as e:
        print(f"Error fetching product data: {str(e)}")
        return None

@app.route('/home')
def home():
    if 'is_logged_in' in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users")
        data = cur.fetchall()
        cur.close()


        num_products_to_fetch = 16
        products = [get_some_product_data() for _ in range(num_products_to_fetch)]

        products_grouped = [products[i:i+4] for i in range(0, len(products), 4)]

        return render_template('users/home.html', users=data, product=products_grouped)
    else:
        return redirect(url_for('login'))


@app.route('/product')
def product():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM produk')
    products = cur.fetchall()
    cur.close()
    
    return render_template('users/product.html', products=products)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM produk WHERE id_produk = %s', (product_id,))
    product = cur.fetchone()
    cur.close()

    if product:
        return render_template('users/product_detail.html', product=product)
    else:
        return render_template('error_page.html', message='Product not found', product=None)


@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'cart' not in session:
        session['cart'] = []

    cur = mysql.connection.cursor()
    cur.execute("SELECT * from produk where id_produk = %s", (int(product_id),))
    product = cur.fetchone()
        
    if product not in session['cart']:
        
        session['cart'].append(product)
        flash('Product added to cart successfully!', 'success')

    return redirect(url_for('product')) 

@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    if 'cart' in session:
        index_to_remove = next((index for index, product in enumerate(session['cart']) if product[0] == product_id), None)

        if index_to_remove is not None:
            removed_product = session['cart'].pop(index_to_remove)
            flash('Product removed from cart successfully!', 'success')
        else:
            flash('Product not found in cart!', 'error')

    return redirect(url_for('product'))
@app.route('/checkout')
def checkout():
    if 'is_logged_in' in session:
        if 'cart' in session:
            cur = mysql.connection.cursor()
            product_ids = [str(product[0]) for product in session['cart']]
            product_ids_str = ','.join(product_ids)

            cur.execute(f'SELECT * FROM produk WHERE id_produk IN ({product_ids_str})')
            products_in_cart = cur.fetchall()
            cur.close()

            return render_template('users/checkout.html', products_in_cart=products_in_cart)
        else:
            flash('Your shopping cart is empty. Please add items before proceeding to checkout.', 'info')
            return redirect(url_for('product'))
    else:
        return redirect(url_for('login'))

@app.route('/process_checkout', methods=['POST'])
def process_checkout():
    try:
        username = session.get('username')

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user_info = cur.fetchone()
        cur.close()

        if not user_info:
            flash('User information not found. Please log in again.', 'error')
            return redirect(url_for('login'))

        buyer_name = user_info[1]
        alamat =  request.form['shipping_address']
        payment_method =  request.form['payment_method']
        purchase_date = datetime.now()

        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO pembelian (buyer_name, purchase_date, alamat_pengiriman, payment) VALUES (%s, %s, %s, %s)",
                (buyer_name, purchase_date, alamat, payment_method))
        mysql.connection.commit()

        purchase_id = cur.lastrowid

        total_amount = 0
        for product in session['cart']:
            product_id = product[0]
            quantity = 1 

            cur.execute("SELECT harga FROM produk WHERE id_produk = %s", (product_id,))
            product_price_result = cur.fetchone()

            if product_price_result:
                product_price = product_price_result[0]
                total_price = quantity * product_price

                cur.execute("INSERT INTO detail_pembelian (purchase_id, id_produk, quantity, total_price) VALUES (%s, %s, %s, %s)", (purchase_id, product_id, quantity, total_price))
                mysql.connection.commit()

                total_amount += total_price

        invoice_number = 'INV-' + str(purchase_id) 
        cur.execute("INSERT INTO invoices (purchase_id, invoice_number, total_amount, purchase_date) VALUES (%s, %s, %s, %s)", (purchase_id, invoice_number, total_amount, purchase_date))
        mysql.connection.commit()

        session.pop('cart', None) 
        flash('Checkout successful! Thank you for your purchase.', 'success')
        return redirect(url_for('invoice', purchase_id=purchase_id))

    except Exception as e:
        print(f"Checkout error: {str(e)}")
        flash('An error occurred during checkout. Please try again.', 'error')
        return redirect(url_for('checkout'))

@app.route('/about')
def about():
    return render_template('users/about.html')

@app.route('/contact')
def contact():
    return render_template('users/contact.html')

@app.route('/logout')
def logout():
    session.pop('is_logged_in', None)
    session.pop('is_logged_in_admin', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/admin')
def admin():
    if 'is_logged_in_admin' in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users")
        users = cur.fetchall()
        cur.close()
        return render_template('admin/admin_page.html', users=users)
    else:
        return redirect(url_for('login'))
    

@app.route('/invoice/<int:purchase_id>')
def invoice(purchase_id):
    try:
        cur = mysql.connection.cursor()

        # Fetch invoice information from the database
        cur.execute("SELECT * FROM invoices WHERE purchase_id = %s", (purchase_id,))
        invoice_info = cur.fetchone()

        if not invoice_info:
            flash('Invoice not found.', 'error')
            return redirect(url_for('home'))

        # Fetch shipping address and payment details
        cur.execute("SELECT alamat_pengiriman, payment FROM pembelian WHERE purchase_id = %s", (purchase_id,))
        purchase_info = cur.fetchone()

        # Fetch products associated with the invoice
        cur.execute("""
            SELECT p.*, pd.quantity, pd.total_price, pb.buyer_name
            FROM produk p
            JOIN detail_pembelian pd ON p.id_produk = pd.id_produk
            JOIN pembelian pb ON pd.purchase_id = pb.purchase_id
            WHERE pd.purchase_id = %s
        """, (purchase_id,))
        products_in_invoice = cur.fetchall()

        cur.close()

        print("Invoice Data:", invoice_info)
        print("Purchase Info:", purchase_info)
        print("Products Data:", products_in_invoice)


        return render_template('users/invoice.html', invoice=invoice_info, purchase=purchase_info, products=products_in_invoice)

    except Exception as e:
        print(f"Error generating invoice: {str(e)}")
        flash('An error occurred while generating the invoice.', 'error')
        return redirect(url_for('home'))
# CRUD admin product
@app.route('/admin_produk')
def admin_produk():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM produk')
    data = cur.fetchall()
    cur.close()
    return render_template('admin/admin_produk.html', products=data)

@app.route('/add', methods=['POST'])
def add_produk():
    if request.method == 'POST':
        product = request.form
        file = request.files['file_gambar']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            cur = mysql.connection.cursor()
            cur.execute('''
                INSERT INTO produk (no_artikel, nama_produk, deskripsi, harga, size, file_gambar)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (product['no_artikel'], product['nama_produk'], product['deskripsi'], product['harga'], product['size'], filename))
            mysql.connection.commit()
            cur.close()
            
            return redirect(url_for('admin_produk'))
    return "Failed to add product"
        
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/edit_produk/<int:id>', methods=['GET', 'POST'])
def edit_produk(id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM produk WHERE id_produk = %s', (id,))
    product = cur.fetchone()
    cur.close()

    if request.method == 'POST':
        edited_product = request.form
        file = request.files['file_gambar']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            cur = mysql.connection.cursor()
            cur.execute('''
                UPDATE produk
                SET no_artikel=%s, nama_produk=%s, deskripsi=%s, harga=%s, size=%s, file_gambar=%s
                WHERE id_produk=%s
            ''', (edited_product['no_artikel'], edited_product['nama_produk'], edited_product['deskripsi'],
                  edited_product['harga'], edited_product['size'], filename, id))
            mysql.connection.commit()
            cur.close()

            flash('Product updated successfully!', 'success')
            return redirect(url_for('admin_produk'))

    return render_template('admin/baru.html', product=product)

@app.route('/delete/<int:id>')
def delete_produk(id):
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM produk WHERE id_produk = %s', (id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('admin_produk'))






if __name__ == '__main__':
    app.run(debug=True)
