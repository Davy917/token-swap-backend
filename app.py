import os

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_cors import CORS
from decimal import Decimal

from sqlalchemy.exc import IntegrityError

#os.path.abspath(...) 確保得到的是完整的絕對路徑，不管你從哪裡執行這支程式，都會精準指向 app.py 所在的那個資料夾
basedir = os.path.abspath(os.path.dirname(__file__)) # __file__ 是 Python 內建變數，代表「目前這支程式檔案的路徑」；os.path.dirname(...) 取出它所在的資料夾；
app = Flask(__name__)
CORS(app) #這行要放在 app = Flask(__name__) 之後，因為你需要先有 app 這個實例，才能對它套用 CORS 設定。
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "swap.db")
db = SQLAlchemy(app) #把 SQLAlchemy 這個工具跟你的 Flask app 綁在一起，之後 db 這個變數就是你操作資料庫的入口。

class Swap(db.Model): # db.Model 是 SQLAlchemy 提供的基礎類別，繼承它就代表「這個類別對應到資料庫裡的一張表」
    __tablename__ = "swaps"
    id = db.Column(db.Integer, primary_key=True)
    token_in = db.Column(db.String, nullable=False)
    token_out = db.Column(db.String, nullable=False)
    amount_in = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.String, nullable=False)

class Pool(db.Model):
    __tablename__ = "pools"
    id = db.Column(db.Integer, primary_key=True)
    token_a = db.Column(db.String, nullable=False)
    token_b = db.Column(db.String, nullable=False)
    last_updated_time = db.Column(db.String, nullable=False)
    __table_args__ = (db.UniqueConstraint("token_a", "token_b", name = "uix_token_pair"),)
"""
db.UniqueConstraint("token_a", "token_b", ...)——這是「複合唯一約束(composite unique constraint)」，意思是：token_a 跟 token_b 這兩個欄位的『組合』，在整張表裡不能重複出現。

"""
class PoolReserve(db.Model):
    __tablename__ = "pool_reserve"
    id = db.Column(db.Integer, primary_key=True)
    pool_id = db.Column(db.Integer, db.ForeignKey("pools.id"), nullable=False)
    token = db.Column(db.String, nullable=False)
    reserve = db.Column(db.Numeric(precision=30, scale=10), nullable=False)

def find_pool_id(token_a, token_b):
    pool_ids_a = {r.pool_id for r in PoolReserve.query.filter_by(token=token_a).all()}
    pool_ids_b = {r.pool_id for r in PoolReserve.query.filter_by(token=token_b).all()}
    common_pool_ids = pool_ids_a & pool_ids_b
    if len(common_pool_ids) == 0:
        return None
    return common_pool_ids.pop()

def normalize_token_pair(token_a, token_b, reserve_a, reserve_b):
    pairs = sorted([(token_a.upper(), reserve_a), (token_b.upper(), reserve_b)])
    return pairs[0][0], pairs[1][0], pairs[0][1], pairs[1][1]

def create_pool_if_not_exist(token_a, token_b, reserve_a, reserve_b):
    token_a, token_b, reserve_a, reserve_b = normalize_token_pair(token_a, token_b, reserve_a, reserve_b)
    existing_pool = Pool.query.filter_by(token_a=token_a, token_b=token_b).first()
    if existing_pool:
        return None, "這個交易對已經存在"
    new_pool = Pool(
        token_a=token_a,
        token_b=token_b,
        last_updated_time=datetime.now().isoformat()
    )
    db.session.add(new_pool)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return None, "這個交易對已經存在（資料庫層級攔截）"

    reserve_a_row = PoolReserve(pool_id=new_pool.id, token=token_a, reserve=reserve_a)
    reserve_b_row = PoolReserve(pool_id=new_pool.id, token=token_b, reserve=reserve_b)
    db.session.add(reserve_a_row)
    db.session.add(reserve_b_row)
    db.session.commit()

    return new_pool, None
"""
db.Numeric(precision=30, scale=10)
這是 SQLAlchemy 對應到 Decimal 的資料庫欄位型別，取代原本的 db.Float
precision=30：這個數字總共可以有 30 位數字（整數位 + 小數位加起來）
scale=10：其中，小數點後最多 10 位

Pool 表（池子本身的資訊）：
| id | last_updated_time |
|----|--------------------|

PoolReserve 表（池子裡每種代幣的儲備量）：
| id | pool_id | token | reserve |
"""

@app.route("/hello")
def hello():
    return {"message": "hello Davy"}

@app.route("/add")
def add():
    a = request.args.get("a", type=int)
    b = request.args.get("b", type=int)
    if a is None or b is None:
        return {"error": "缺少參數 a 或 b，或參數不是合法整數"}, 400
    result = a + b
    return {"result": result}

@app.route("/swap", methods=["POST"])
def swap():
    data = request.get_json()
    token_in = data.get("tokenIn")
    token_out = data.get("tokenOut")
    amount_in = data.get("amountIn")
    if token_in is None or token_out is None or amount_in is None:
        return {"error": "缺少必要欄位 tokenIn、tokenOut 或 amountIn"}, 400
    new_swap = Swap( # 建立一個 Swap 物件
        token_in=token_in,
        token_out=token_out,
        amount_in=amount_in,
        created_at=datetime.now().isoformat()
    )
    db.session.add(new_swap) # 加進「暫存區」
    db.session.commit() # 真正寫入
    return {
        "id": new_swap.id,
        "tokenIn": new_swap.token_in,
        "tokenOut": new_swap.token_out,
        "createdAt": new_swap.created_at,
        "message": "swap 記錄已存入資料庫"
    }

@app.route("/swaps", methods=["GET"])
def get_swaps():
    swaps = Swap.query.order_by(Swap.id.desc()).all() # 用 Python 方法鏈(method chaining)表達查詢邏輯
    result = []
    for s in swaps:
        result.append({
            "id": s.id,
            "tokenIn": s.token_in,
            "tokenOut": s.token_out,
            "amountIn": s.amount_in,
            "createdAt": s.created_at
        })
    return {"swaps": result}

@app.route("/swaps/<int:swap_id>", methods=["GET"])
def get_swap_by_id(swap_id):
    s = Swap.query.get(swap_id)
    if s is None:
        return {"error": f"找不到 id 為 {swap_id} 的 swap 記錄"}, 404
    return {
        "id": s.id,
        "tokenIn": s.token_in,
        "tokenOut": s.token_out,
        "amountIn": s.amount_in,
        "createdAt": s.created_at
    }
"""
這是 集合生成式(set comprehension)——跟你可能比較熟悉的「列表生成式(list comprehension)」[x for x in ...] 很像，
差別只在用 {} 包起來，結果會是一個「集合(set)」，不是「列表(list)」。
"""
@app.route("/quote", methods=["GET"])
def get_quote():
    token_in = request.args.get("tokenIn", type=str).upper()
    token_out = request.args.get("tokenOut", type=str).upper()
    amount_in = request.args.get("amount", type=Decimal)
    if token_in is None or token_out is None or amount_in is None:
        return {"error": "缺少必要參數 tokenIn、tokenOut 或 amount"}, 400
    pool_id = find_pool_id(token_in, token_out)
    if pool_id is None:
        return {"error": f"找不到 {token_in}/{token_out} 這個交易對的池子"}, 404
    reserve_in_row = PoolReserve.query.filter_by(pool_id=pool_id, token=token_in).first()
    reserve_out_row = PoolReserve.query.filter_by(pool_id=pool_id, token=token_out).first()
    reserve_in = reserve_in_row.reserve
    reserve_out = reserve_out_row.reserve
    """
    從 PoolReserve 表中查詢符合 pool_id 和 token=token_in 的第一筆記錄
    從 PoolReserve 表中查詢符合 pool_id 和 token=token_out 的第一筆記錄
    從第 1 行查出的記錄中，取出 reserve 欄位的值（入金代幣的儲備量）
    從第 2 行查出的記錄中，取出 reserve 欄位的值（出金代幣的儲備量）
    """
    k = reserve_in * reserve_out
    new_reserve_in = reserve_in + amount_in
    new_reserve_out = k / new_reserve_in
    amount_out = reserve_out - new_reserve_out
    return {
        "tokenIn": token_in,
        "tokenOut": token_out,
        "amountIn": str(amount_in),
        "amountOut": str(amount_out)
    }
if __name__ == "__main__":
    app.run(debug=True)
"""
CORS(app) 做了什麼

最簡單的用法 CORS(app)，會讓這個 Flask 應用允許「所有來源」的跨域請求——這在開發階段很方便，但要先說清楚一個重要觀念：
這種寫法在正式上線的產品環境是不安全的，因為它等於告訴瀏覽器「任何網站都可以呼叫我的 API」。正式環境通常會限制成只允許特定來源，例如：
CORS(app, origins=["http://localhost:5173"])

db.ForeignKey("pools.id")
明確告訴資料庫：「這個欄位的值，必須對應到 pools 表裡真實存在的某個 id」。

文檔:
https://sqlalchemy.flask.org.cn/en/3.1.x/
進去後，有幾個地方最建議優先閱讀：
Quickstart (快速入門)：教你如何正確地在 Flask 中初始化 db，並建立第一個資料模型（Model）。
Models (模型定義)：說明如何定義資料表、欄位型態以及設定「一對多」、「多對多」的關聯。
Queries (查詢資料)：在 Flask-SQLAlchemy 3.x 版本之後，查詢方式已經全面推薦使用 SQLAlchemy 2.0 的 db.select() 風格，文檔裡有詳細的範例。
"""