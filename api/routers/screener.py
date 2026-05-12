from fastapi import APIRouter, HTTPException
from ..services import screener_service

router = APIRouter(prefix="/screener", tags=["Screeners"])


@router.get("/rsi")
def rsi_screen(universe: str = "sp500", oversold: int = 30, overbought: int = 70):
    """
    Screen stocks by RSI levels.
    - universe: sp500 | nasdaq | nyse | amex | russell3000 | nse | bse
    - oversold: RSI threshold for oversold (default 30)
    - overbought: RSI threshold for overbought (default 70)
    """
    try:
        return screener_service.rsi_screener(universe, oversold, overbought)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/minervini")
def minervini_screen(universe: str = "sp500"):
    """
    Screen stocks using Mark Minervini's SEPA trend template.
    Returns stocks in a strong stage 2 uptrend.
    - universe: sp500 | nasdaq | nyse | amex | russell3000
    """
    try:
        results = screener_service.minervini_screener(universe)
        return {
            "universe": universe,
            "count":    len(results),
            "stocks":   results,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
