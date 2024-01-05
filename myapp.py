from flask import Flask, render_template, session, request, redirect, url_for
from flask_mysqldb import MySQL

# init main app
app = Flask(__name__)
products = [
    {"id": 1, "name": "Product 1", "description": "Description of Product 1."},
    {"id": 2, "name": "Product 2", "description": "Description of Product 2."},
    {"id": 3, "name": "Product 3", "description": "Description of Product 3."},
    {"id": 4, "name": "Product 4", "description": "Description of Product 4."},
    {"id": 5, "name": "Product 5", "description": "Description of Product 5."},
]

# kunci rahasia agar session bisa berjalan
app.secret_key = '!@#$%'

# database config
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "dbflask"

# init mysql
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

@app.route('/home')
def home():
    if 'is_logged_in' in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users")
        data = cur.fetchall()
        cur.close()
        return render_template('users/home.html', users=data)
    else:
        return redirect(url_for('login'))

@app.route('/product')
def product():
    return render_template('users/product.html', products=products)

@app.route('/about')
def about():
    return render_template('users/about.html')

@app.route('/contact')
def contact():
    return render_template('users/contact.html')

@app.route('/admin_produk')
def admin_produk():
    return render_template('admin/admin_produk.html')


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
    
    
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = next((p for p in products if p['id'] == product_id), None)
    if product:
        return render_template('components/product_detail.html', product=product)
    else:
        return render_template('users/product.html')
    



if __name__ == '__main__':
    app.run(debug=True)
