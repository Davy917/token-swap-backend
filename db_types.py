from sqlalchemy.types import TypeDecorator, String
class BigIntAsText(TypeDecorator):
    impl = String
    cache_ok = True
    def process_bind_param(self, value, dialect): # value預設是 int
        if value is None:
            return None
        if type(value) is not int:
            raise TypeError(f"只接受 int，不接受 {type(value)}")
        if value < 0:
            raise ValueError("儲備量與金額不應為負")
        return str(value)
    def process_result_value(self, value, dialect): # value預設是 str
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError(f"預期輸出 str，卻輸出 {type(value)}")
        return int(value)
