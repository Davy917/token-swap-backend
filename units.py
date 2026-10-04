import re

def to_base_units(amount_str: str, decimals: int) -> int:
    if not isinstance(amount_str, str):
        raise ValueError("必須傳入字串")
    if not re.fullmatch(r"[0-9]+(\.[0-9]+)?", amount_str):
        raise ValueError("請輸入有效的數字格式（只允許正整數和小數點）")
    if '.' in amount_str:
        decimal_part = amount_str.split('.')[1]
        if len(decimal_part) > decimals:
            raise ValueError(f"最多只支持小數點{decimals}位")

    whole, _, frac = amount_str.partition(".")
    return int(whole + frac.ljust(decimals, "0"))
    amount = Decimal(amount_str)
    return int(amount * (10 ** decimals)) # 保留Decimal版本寫法

def from_base_units(amount: int, decimals: int) -> str:
    whole, frac = divmod(amount, 10 ** decimals)
    frac_str = str(frac).zfill(decimals)
    frac_str = frac_str.rstrip('0')
    if frac_str:
        return f"{whole}.{frac_str}"
    return str(whole)

if __name__ == "__main__":
    to_base_units("1", 6)
    from_base_units(1500000, 6)
    # print(f"{1.1 * 100:.20f}")
    # print(format(1.1 * 100, ".20f"))



"""
partition() 的作用： 將字串分成三部分
第一部分（whole）— 小數點前的內容
第二部分（_）— 小數點本身 .
第三部分（frac）— 小數點後的內容

frac.ljust(decimals, "0") — 把 frac 左對齐，用 "0" 補齊到 decimals 位
whole + ... — 字串拼接
int(...) — 轉成整數
"""