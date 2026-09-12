from app_sqlalchemy import app, db
with app.app_context():
    db.create_all()
    print("資料表建立完成（或已存在）")