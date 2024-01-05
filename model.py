from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    HOST = str(os.environ.get("DB_HOST", "localhost"))
    DATABASE = str(os.environ.get("DB_DATABASE", "dbflask"))
    USERNAME = str(os.environ.get("DB_USERNAME", "root"))
    PASSWORD = str(os.environ.get("DB_PASSWORD", ""))

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://' + Config.USERNAME + ':' + Config.PASSWORD + '@' + Config.HOST + "/" + Config.DATABASE
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
db = SQLAlchemy(app)



class Pembelian(db.Model):
    id_pembelian = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_produk = db.Column(db.Integer, db.ForeignKey('produk.id_produk'), nullable=False)
    jumlah_pembelian = db.Column(db.Integer, nullable=False)
    total_harga = db.Column(db.Float, nullable=False)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Create tables inside the application context
with app.app_context():
    db.create_all()

# Add your routes and the rest of the code here...



if __name__ == '__main__':
    app.run(debug=True)
