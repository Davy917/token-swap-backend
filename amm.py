def get_amount_out(reserve_in, reserve_out, amount_in) -> int:
    if type(amount_in) is not int:
        raise TypeError(f"amount_in 只接受 int，不接受 {type(amount_in)}")
    if type(reserve_in) is not int:
        raise TypeError(f"reserve_in 只接受 int，不接受 {type(reserve_in)}")
    if type(reserve_out) is not int:
        raise TypeError(f"reserve_out 只接受 int，不接受 {type(reserve_out)}")
    if amount_in <= 0:
        raise ValueError("amount_in 必須 > 0")
    if reserve_in <= 0:
        raise ValueError("reserve_in 必須 > 0")
    if reserve_out <= 0:
        raise ValueError("reserve_out 必須 > 0")
    amount_out = reserve_out * amount_in // (reserve_in + amount_in)
    if amount_out == 0:
        raise ValueError(f"amount_out 必須 > 0，但計算結果是 {amount_out}。輸入的 amount_in 可能太小。")
    return amount_out

"""
假設用戶選擇 ETH/USDT, 打算花 500 USDT 買 ETH
amount_in: 500 USDT
reserve_in: LP裡有多少 USDT
reserve_out: LP裡有多少 ETH
"""