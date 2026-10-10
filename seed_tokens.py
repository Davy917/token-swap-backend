from app import app, db, Token
from sqlalchemy.exc import IntegrityError

new_token_1 = Token(
    symbol="USDT",
    decimals=6
)
new_token_2 = Token(
    symbol="BTC",
    decimals=8
)
new_token_3 = Token(
    symbol="ETH",
    decimals=18
)

with app.app_context():
    db.session.add_all([new_token_1, new_token_2, new_token_3])
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        print(f"新增 Token 失敗: {e.orig}")  # e.orig 是底層的錯誤訊息
        raise  # 重新拋出例外