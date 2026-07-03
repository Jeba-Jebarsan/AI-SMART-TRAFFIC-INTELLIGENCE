"""E-challan helpers: deterministic challan IDs + fine lookup."""
import datetime

import config


def make_challan_id(seq: int) -> str:
    """CH-YYYYMMDD-#### — human-friendly, unique per run."""
    day = datetime.datetime.now().strftime("%Y%m%d")
    return f"CH-{day}-{seq:04d}"


def fine_for(vtype: str) -> int:
    return config.FINES.get(vtype, 1000)
