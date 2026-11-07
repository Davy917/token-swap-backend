import os
# 記憶體資料庫，完全獨立
os.environ["DATABASE_URL"] = "sqlite://"      # 必須在 import app 之前
from app import app, db, Token, Pool, PoolReserve
import routes
from units import to_base_units
import unittest


class ModelTestCase(unittest.TestCase):
    """只放 token 的乾淨資料庫，給 test_models.py 用"""
    def setUp(self):
        # 保險：絕對不能對真正的 swap.db 做 drop_all
        app.testing = False
        self.assertEqual(app.config["SQLALCHEMY_DATABASE_URI"], "sqlite://") # （沒有檔案路徑）代表純記憶體資料庫，程式一結束就消失，跟 swap.db 完全無關。
        self.ctx = app.app_context()
        self.ctx.push()
        db.create_all()
        db.session.add_all([Token(symbol="USDT", decimals=6),
                            Token(symbol="ETH", decimals=18),
                            Token(symbol="BTC", decimals=8)
                           ])
        db.session.commit()

    def tearDown(self): # 每次清空
        app.testing = False
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def make_pool(self):
        pool = Pool(token_a="ETH", token_b="USDT", last_updated_time="t")
        db.session.add(pool)
        db.session.commit()
        return pool


class QuoteTestCase(ModelTestCase):
    """在 token 之外再放好 ETH/USDT pool + reserve，給 test_quote.py 用"""
    def setUp(self):
        super().setUp()
        self.client = app.test_client()
        pool = self.make_pool()
        db.session.add_all([
            PoolReserve(pool_id=pool.id, token="USDT", reserve=to_base_units("25000", 6)),
            PoolReserve(pool_id=pool.id, token="ETH", reserve=to_base_units("10", 18)),
        ])
        db.session.commit()


if __name__ == "__main__":
    unittest.main()
