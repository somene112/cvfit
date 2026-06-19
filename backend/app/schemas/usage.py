"""Phase 6 Usage / Plan / Credits Shell schemas.

Read-only, informational only. No real payment, no checkout, no paid-plan
enforcement. Usage is computed from existing records at request time.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class UsageResponse(BaseModel):
    plan_id: str
    plan_name: str
    period: str
    usage: Dict[str, int]
    limits: Dict[str, int]
    warnings: List[str]
    limitations: List[str]
    reset_at: Optional[datetime] = None
    enforcement_enabled: bool = False


class PlanItem(BaseModel):
    id: str
    name: str
    price: str  # demo placeholder copy only — never a real charge
    features: List[str]
    current: bool
    # Intentionally no checkout_url / payment fields.


class PlansResponse(BaseModel):
    plans: List[PlanItem]
    upgrade_available: bool = False
    upgrade_teaser_disabled: bool = True
    limitations: List[str]
