# Universe

18 US-listed ETFs, all trading before 2007-04-30: SPY, IWM, EFA, EEM, XLE, XLF, XLK, XLU, XLV, SHY, IEF, TLT, TIP, LQD, HYG, GLD, DBC, VNQ, in this order everywhere.
Daily adjusted closes from yfinance (`auto_adjust=True`), 2007-04-11 to 2026-09-15; risk-free is FRED DGS3MO over the same range.
Panel starts on the first day all 18 have a price (expected 2007-04-11, HYG's first day), so no missing-asset handling is needed.
196 monthly decision dates, 2010-04-30 to 2026-07-31, each with a 36-month estimation window.
