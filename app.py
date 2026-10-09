import os
from db_types import BigIntAsText
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///" + os.path.join(basedir, "swap.db"))
db = SQLAlchemy(app)

@db.event.listens_for(db.Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

class Token(db.Model):
    __tablename__ = "tokens"
    symbol = db.Column(db.String, primary_key = True)
    decimals = db.Column(db.Integer, nullable = False)

class Pool(db.Model):
    __tablename__ = "pools"
    id = db.Column(db.Integer, primary_key=True)
    token_a = db.Column(db.ForeignKey("tokens.symbol"), nullable=False)
    token_b = db.Column(db.ForeignKey("tokens.symbol"), nullable=False)
    last_updated_time = db.Column(db.String, nullable=False)
    __table_args__ = (db.UniqueConstraint("token_a", "token_b", name = "uix_token_pair"),)

class Swap(db.Model):
    __tablename__ = "swaps"
    id = db.Column(db.Integer, primary_key=True)
    token_in = db.Column(db.ForeignKey("tokens.symbol"), nullable=False)
    token_out = db.Column(db.ForeignKey("tokens.symbol"), nullable=False)
    amount_in = db.Column(BigIntAsText, nullable=False)
    amount_out = db.Column(BigIntAsText, nullable=False)
    created_at = db.Column(db.String, nullable=False)

class PoolReserve(db.Model):
    __tablename__ = "pool_reserve"
    id = db.Column(db.Integer, primary_key=True)
    pool_id = db.Column(db.Integer, db.ForeignKey("pools.id"), nullable=False)
    token = db.Column(db.String, db.ForeignKey("tokens.symbol"), nullable=False)
    reserve = db.Column(BigIntAsText, nullable=False)