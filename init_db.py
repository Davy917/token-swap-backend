import sqlite3
conn = sqlite3.connect("swap.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS swaps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token_in TEXT NOT NULL,
        token_out TEXT NOT NULL,
        amount_in REAL NOT NULL,
        created_at TEXT NOT NULL
    )
""")

conn.commit()
conn.close()

print("資料庫初始化成功")

"""
sqlite3.connect("swap.db")：建立（或連接到，如果已存在）一個叫 swap.db 的檔案，這個檔案就是你的整個資料庫——這是 SQLite 的特色，不像 MySQL/PostgreSQL 需要另外跑一個資料庫伺服器，SQLite 就是一個檔案
cursor：你可以把它想成「操作資料庫的手」，之後所有的 SQL 指令都透過 cursor.execute(...) 送出去執行
CREATE TABLE IF NOT EXISTS swaps (...)：這是 SQL 語法，意思是「如果 swaps 這張表還不存在，就建立它」——加 IF NOT EXISTS 是為了避免你重複執行這支程式時，因為表已經存在而報錯
NOT NULL：代表這個欄位不允許是空值，插入資料時一定要給值，這是資料庫層級的一種資料完整性保護
conn.commit()：這行很關鍵，不能漏——在資料庫的世界裡，你做的異動（像建表、新增資料）預設是在一個「暫存狀態」，要呼叫 commit() 才會真正把改動寫入硬碟、正式生效
conn.close()：關閉連線，釋放資源，養成好習慣用完就關
"""