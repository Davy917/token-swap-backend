from datetime import datetime
from units import to_base_units
from sqlalchemy.exc import IntegrityError

from app import app, db, Pool, PoolReserve
with app.app_context():

    new_pool = Pool(
        token_a="ETH",
        token_b="USDT",
        last_updated_time=datetime.now().isoformat()
    )
    db.session.add(new_pool)
    
    try:
        db.session.flush()
        pool_id = new_pool.id
        usdt_reserve = PoolReserve(
            pool_id=pool_id,
            token="USDT",
            reserve=to_base_units("25000", 6)
        )
        eth_reserve = PoolReserve(
            pool_id=pool_id,
            token="ETH",
            reserve=to_base_units("10", 18)
        )
        db.session.add_all([usdt_reserve, eth_reserve])
        db.session.commit()
        print(f"流動性池ETH/USDT新增成功")
    except IntegrityError as e:
        db.session.rollback()
        print(f"新增流動性池ETH/USDT失敗: {e.orig}")  # e.orig 是底層的錯誤訊息
        raise  # 重新拋出例外
