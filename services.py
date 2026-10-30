from dataclasses import dataclass
from sqlalchemy.orm.exc import NoResultFound
from amm import get_amount_out
from app import normalize_token, Token, Pool, PoolReserve
from units import to_base_units
@dataclass(frozen=True)
class QuoteResult:
    token_in: str
    token_out: str
    amount_in: int
    amount_out: int
    decimals_in: int
    decimals_out: int

class InvalidInputError(Exception):
    pass
class NoResourceError(Exception):
    pass

def quote(token_in: str, token_out: str, amount_in: str) -> QuoteResult:
    token_in, token_out = normalize_token(token_in), normalize_token(token_out)
    if token_in is None or token_out is None:
        raise InvalidInputError("token_in 或 token_out 輸入格式錯誤")
    if token_in == token_out:
        raise InvalidInputError("token_in 和 token_out 不能相同")
    try:
        token_in_decimals = Token.query.filter_by(symbol=token_in).one().decimals
    except NoResultFound:
        raise NoResourceError(f"{token_in} 幣種不存在")
    try:
        token_out_decimals = Token.query.filter_by(symbol=token_out).one().decimals
    except NoResultFound:
        raise NoResourceError(f"{token_out} 幣種不存在")

    pair = sorted([token_in, token_out])
    try:
        pool_id = Pool.query.filter_by(token_a=pair[0], token_b=pair[1]).one().id
    except NoResultFound:
        raise NoResourceError(f"{token_in}/{token_out}流動性池不存在")

    reserve_in = PoolReserve.query.filter_by(pool_id=pool_id, token=token_in).one().reserve
    reserve_out = PoolReserve.query.filter_by(pool_id=pool_id, token=token_out).one().reserve

    try:
        amount_in = to_base_units(amount_in, token_in_decimals)
    except ValueError as e:
        raise InvalidInputError(str(e)) from e
    try:
        amount_out = get_amount_out(reserve_in, reserve_out, amount_in)
    except ValueError as e:
        raise InvalidInputError(str(e)) from e

    return QuoteResult(
        token_in=token_in,
        token_out=token_out,
        amount_in=amount_in,
        amount_out=amount_out,
        decimals_in=token_in_decimals,
        decimals_out=token_out_decimals
    )