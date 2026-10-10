## db.event.listens_for(db.engine, "connect")
這段的用途是：**每當 SQLite 連接建立時，自動執行「啟用外鍵檢查」的 SQL 指令。**

---

## 逐行解釋

```python
@db.event.listens_for(db.Engine, "connect")
```

**監聽事件**：告訴 SQLAlchemy「我要在資料庫連接建立時做一些事」。

- `db.Engine` = SQLAlchemy 的資料庫引擎
- `"connect"` = 監聽「新連接建立」這個事件

---

```python
def set_sqlite_pragma(dbapi_connection, connection_record):
```

**回調函數**：當事件觸發時呼叫的函數。

- `dbapi_connection` = 原始 SQLite 連接物件
- `connection_record` = SQLAlchemy 的連接紀錄（通常不用）

---

```python
cursor = dbapi_connection.cursor()
cursor.execute("PRAGMA foreign_keys=ON")
cursor.close()
```

**執行指令**：
1. 取得遊標
2. 執行 `PRAGMA foreign_keys=ON` 啟用外鍵檢查
3. 關閉遊標

---

## 為什麼需要

SQLite **預設不檢查外鍵**。

如果你有這樣的資料結構：

```python
class PoolReserve(db.Model):
    token = db.Column(db.String, db.ForeignKey("tokens.symbol"), nullable=False)
```

**沒有這段程式碼：**
```python
# ✅ SQLite 不檢查，這會成功插入（即使 tokens 表沒有 DOGE）
db.session.add(PoolReserve(token="DOGE", ...))
db.session.commit()  # 沒錯誤
```

**有這段程式碼：**
```python
# ❌ SQLite 檢查外鍵，拋出 IntegrityError
db.session.add(PoolReserve(token="DOGE", ...))
db.session.commit()  # IntegrityError: FOREIGN KEY constraint failed
```

---

## 簡單來說

這段程式碼的作用就像是告訴 SQLite：

> 「每次我連接到你時，請幫我打開『外鍵檢查』的開關。」

---

## 你應該把它加在哪裡

在你的 `app_decimal.py` 裡，加在建立 `db` 之後：

```python
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "swap.db")
db = SQLAlchemy(app)

# 加這段
@db.event.listens_for(db.engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
```

這樣以後你的外鍵約束才會真的被強制執行。

## 使用FK跟不用的差異在哪?

**FK 的作用：讓資料庫層級強制執行參照完整性。**

無FK vs 有FK的差異：

| | 無 FK | 有 FK |
|--|--|--|
| **插入不存在的 token** | ✅ 成功（沒人檢查） | ❌ 拋 IntegrityError |
| **刪除被引用的 token** | ✅ 成功（可能孤立資料） | ❌ 拋 IntegrityError（或級聯刪除） |
| **資料一致性** | 只靠應用層程式自律 | 資料庫層級保證 |

**你們的例子：**

```python
# 有 FK
class Swap(db.Model):
    token_in = db.Column(db.ForeignKey("tokens.symbol"), nullable=False)
    # 插入 token_in="DOGE" 時 → IntegrityError（PRAGMA foreign_keys=ON 時）

# 無 FK
class Swap(db.Model):
    token_in = db.Column(db.String, nullable=False)
    # 插入 token_in="DOGE" 時 → ✅ 成功（即使 tokens 表沒有 DOGE）
```

**為什麼需要 FK？**
1. **防止孤立資料** — token 被刪了，swap 表裡還有引用
2. **自動化驗證** — 不用每次插入都手動檢查
3. **測試可靠性** — 測試能驗證約束真的有生效

你們的測試 `test_swap_with_unknown_token_rejected` 正是為了驗證 FK 有效。如果改成無 FK，這個測試會失敗（因為插入會成功），這就是**突變測試**的威力——它會揭露程式碼中「看似有保護，但實際失效」的地方。