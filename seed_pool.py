from app import app, create_pool_if_not_exist

from decimal import Decimal
with app.app_context():
    new_pool, error = create_pool_if_not_exist("USDT", "BTC", Decimal("100000"), Decimal("2"))
    if error:
        print(f"建立失敗：{error}")
    else:
        print(f"流動性池已建立完成，pool_id = {new_pool.id}")

"""
    app.app_context()
SQLAlchemy 的操作需要知道「現在是在哪個 Flask app 的上下文底下執行」，
因為理論上一個程式可能同時管理多個 Flask app 實例。
with app.app_context(): 就是明確告訴 SQLAlchemy「接下來的資料庫操作，都是在這個 app 底下進行」。
這個概念現階段只需要記得「凡是要在 test.py 之外操作 SQLAlchemy，都要包一層 app.app_context()」，之後用多了自然會有感覺。

    db.create_all()
這行的意思是：「檢查目前定義的所有 db.Model 子類別，如果對應的表在資料庫裡不存在，就建立它」。
注意它是 IF NOT EXISTS 的邏輯——如果表已經存在，這行不會做任何事、也不會報錯，
更不會幫你檢查欄位有沒有變動（這點之後你如果修改欄位定義會踩到坑，先知道就好，現階段不深究）。
"""