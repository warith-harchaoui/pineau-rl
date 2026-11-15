"""Numbers as the two texts write them (docs/check_numbers.py): rounding half up, French and English styles."""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Any

__all__ = ["half_up", "pct", "num", "ci", "pts"]


def half_up(x: Any, nd: int = 0) -> Decimal:
    """Round half away from zero, as a reader does: 1.15 -> 1.2, -66.5 -> -67 (Python's round is to even).
    The float goes through its shortest repr, so 1.15 is 1.15, not 1.1499999999999999."""
    q = Decimal(1).scaleb(-nd)
    return Decimal(str(x)).quantize(q, rounding=ROUND_HALF_UP)


def pct(x: Any, nd: int = 0, lang: str = "fr") -> str:
    """A share as a percentage: 0.0515 -> "5,2 %" (fr, nd=1) or "5.2%" (en)."""
    s = str(half_up(Decimal(str(x)) * 100, nd))
    return (s.replace(".", ",") + " %") if lang == "fr" else s + "%"


def num(x: Any, lang: str = "fr") -> str:
    """An integer with thousands separators: 1252 -> "1 252" (fr) or "1,252" (en)."""
    s = f"{int(half_up(x)):,}"
    return s.replace(",", " ") if lang == "fr" else s


def ci(lo: Any, hi: Any, lang: str = "fr") -> str:
    """An interval of shares in whole percentage points: "[12, 46]" (same in both languages)."""
    return f"[{int(half_up(Decimal(str(lo)) * 100))}, {int(half_up(Decimal(str(hi)) * 100))}]"


def pts(t: dict[str, Any], lang: str = "fr") -> tuple[str, str]:
    """The bounds {lo, hi} of a difference in percentage points, signed with the minus sign "−": ("−5", "+12")."""
    lo, hi = int(half_up(Decimal(str(t["lo"])) * 100)), int(half_up(Decimal(str(t["hi"])) * 100))

    def f(v: int) -> str:
        return f"−{abs(v)}" if v < 0 else f"+{v}"

    return f(lo), f(hi)
