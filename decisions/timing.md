# Timing

Decisions at month-end t use prices dated ≤ t only.
Trades execute at the close of the next trading day; cost is charged at execution, before the holding return.
Holding period runs from execution close to the next execution close; `w_prev` is the previous target drifted over it and renormalised.
The first decision has no `w_prev`: no turnover constraint, no cost term, no cost or turnover recorded.
