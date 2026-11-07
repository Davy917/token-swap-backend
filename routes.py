from flask import request
from app import app
from services import quote, InvalidInputError, NoResourceError
from units import from_base_units

@app.route("/quote", methods=["GET"])
def get_quote():
    token_in = request.args.get("tokenIn", type=str)
    token_out = request.args.get("tokenOut", type=str)
    amount_in = request.args.get("amountIn", type=str)
    try:
        result = quote(token_in, token_out, amount_in)
    except InvalidInputError as e:
        return {'error': str(e)}, 400
    except NoResourceError as e:
        return {'error': str(e)}, 404
    return {
        "tokenIn": result.token_in,
        "tokenOut": result.token_out,
        "amountIn": from_base_units(result.amount_in, result.decimals_in),
        "amountOut": from_base_units(result.amount_out, result.decimals_out),
    }