import sqlite3
from datetime import datetime
from unittest import result

from flask import Flask, request #把 Flask 這個工具箱裡的 Flask, request 這個東西拿進來用
from flask_sqlalchemy import SQLAlchemy
from init_db import conn, cursor

app = Flask(__name__) #建立一個「應用程式」的實體,__name__ 是 Python 內建的變數,Flask 用它來定位你的專案位置(現階段不用深究,先知道這是慣例寫法)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///swap.db"
db = SQLAlchemy(app) # 直接傳 app，立即初始化

@app.route("/hello") #這行是關鍵——它是一個「裝飾器(decorator)」,意思是「當有人打 /hello 這個路徑的時候,執行底下這個函式」
def hello():
    return {"message": "hello Davy"} #這個函式被打到的時候,回傳一個 Python 字典,Flask 會自動幫你轉成 JSON 格式回傳給呼叫的人

@app.route("/add")
def add():
    a = request.args.get("a", type=int)
    b = request.args.get("b", type=int) #request.args是 Flask 幫你解析「網址上 ? 後面那串參數」的地方,例如 /add?a=3&b=5 這個網址,a=3&b=5 這部分就叫做 query string(查詢字串)
    if a is None or b is None:
        return {"error": "缺少參數 a 或 b，或參數不是合法整數"}, 400 #這裡回傳的不只是一個字典，後面多了一個 400。這是 HTTP status code（狀態碼）——之前沒指定的時候，Flask 預設會回 200（代表「成功」）。
    result = a + b
    return {"result": result}

@app.route("/swap", methods=["POST"])
def swap():
    data = request.get_json() #這是解析 POST request body 裡 JSON 資料的方法，跟之前 GET 用的 request.args.get(...) 是不同的取值方式，因為資料來源不一樣（一個在網址、一個在 body）
    token_in = data.get("tokenIn") # 從字典中取出鍵名為 "tokenIn" 的值，存到變數 token_in, .get("鍵名") 是安全的取值方式
    token_out = data.get("tokenOut")
    amount_in = data.get("amountIn")

    if token_in is None or token_out is None or amount_in is None:
        return {"error": "缺少必要欄位 tokenIn、tokenOut 或 amountIn"}, 400

    created_at = datetime.now().isoformat() #拿目前時間，轉成一個標準格式的字串（例如 2026-08-03T15:20:00），存進資料庫的 created_at 欄位

    conn = sqlite3.connect("swap.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO swaps (token_in, token_out, amount_in, created_at) VALUES (?, ?, ?, ?)",
        (token_in, token_out, amount_in, created_at)
    )
    conn.commit()
    new_id = cursor.lastrowid #拿到剛剛插入的這筆資料，資料庫自動幫你產生的 id 是多少
    conn.close()

    return {
        "id": new_id,
        "tokenIn": token_in,
        "tokenOut": token_out,
        "amountIn": amount_in,
        "createdAt": created_at,
        "message": "swap 紀錄已存入資料庫"
    }

@app.route("/swap", methods=["GET"])
def get_swaps():
    conn = sqlite3.connect("swap.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT id, token_in, token_out, amount_in, created_at FROM swaps ORDER BY id DESC")
    rows = cursor.fetchall() #把查詢結果全部抓出來，會得到一個 list，每個元素是一個 tuple
    conn.close()
    result = []
    for row in rows:
        result.append({
            "id": row[0],
            "tokenIn": row[1],
            "tokenOut": row[2],
            "amountIn": row[3],
            "createdAt": row[4]
        })
    return {"swaps": result}
"""
sqlite3.connect("swap.db")：建立（或連接到，如果已存在）一個叫 swap.db 的檔案，這個檔案就是你的整個資料庫——這是 SQLite 的特色，不像 MySQL/PostgreSQL 需要另外跑一個資料庫伺服器，SQLite 就是一個檔案
cursor：你可以把它想成「操作資料庫的手」，之後所有的 SQL 指令都透過 cursor.execute(...) 送出去執行
CREATE TABLE IF NOT EXISTS swaps (...)：這是 SQL 語法，意思是「如果 swaps 這張表還不存在，就建立它」——加 IF NOT EXISTS 是為了避免你重複執行這支程式時，因為表已經存在而報錯
NOT NULL：代表這個欄位不允許是空值，插入資料時一定要給值，這是資料庫層級的一種資料完整性保護
conn.commit()：這行很關鍵，不能漏——在資料庫的世界裡，你做的異動（像建表、新增資料）預設是在一個「暫存狀態」，要呼叫 commit() 才會真正把改動寫入硬碟、正式生效
conn.close()：關閉連線，釋放資源，養成好習慣用完就關
"""
@app.route("/swaps/<int:swap_id>", methods=["GET"])
def get_swap_by_id(swap_id):
    conn = sqlite3.connect("swap.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, token_in, token_out, amount_in, created_at FROM swaps WHERE id = ?",
   (swap_id,)
                   )
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return {"error": f"找不到 id 為 {swap} 的 swap 記錄"}, 404
    result = {
        "id": row[0],
        "tokenIn": row[1],
        "tokenOut": row[2],
        "amountIn": row[3],
        "createdAt": row[4]
    }
    return result
"""
<int:swap_id>：這是 Flask 的動態路由語法。<類型:變數名稱> 的格式——這裡限定這個路徑片段一定要是整數，如果有人打 /swaps/abc（不是數字），Flask 會直接回傳 404，連進到你的函式邏輯都不會，這是 Flask 內建的型別保護
函式參數 swap_id：注意路由裝飾器裡的 <int:swap_id>，跟函式定義 def get_swap_by_id(swap_id) 的參數名稱要一致，Flask 會自動把網址裡解析到的值，當作參數傳進函式裡
WHERE id = ?：SQL 的篩選條件語法，只抓出符合條件的那一筆，一樣用 ? 佔位符做參數化查詢
cursor.fetchone()：跟之前的 fetchall() 不同，這裡只抓一筆（因為 id 是主鍵，本來就不會重複，最多只有一筆符合）
if row is None：這是這支 API 的關鍵設計——如果查無此 id，不能讓程式直接崩潰或回傳空資料當作「成功」，而是要明確回傳 404 Not Found，告訴呼叫方「你要的資源不存在」
"""
if __name__ == "__main__":
    app.run(debug=True) #啟動這個服務,debug=True 代表你改程式碼存檔後,伺服器會自動重啟,不用手動重跑(開發階段很方便,正式上線時要記得關掉)