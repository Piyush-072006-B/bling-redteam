# ============================================================
# Account Pool — Synthetic Account Management
# ============================================================
import json
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class AccountPool:
    """
    Manages a pool of synthetic bank accounts.
    Supports: normal, mule, dormant, high-risk profiles.
    """

    def __init__(self, size: int = 1000):
        self.size = size
        self.accounts: Dict[str, Dict] = {}
        self._generate_pool()

    def _generate_pool(self) -> None:
        """Generate a diverse account pool with realistic profiles."""
        normal_count = int(self.size * 0.70)
        mule_count = int(self.size * 0.10)
        dormant_count = int(self.size * 0.15)
        high_risk_count = self.size - normal_count - mule_count - dormant_count

        for _ in range(normal_count):
            acc = self._create_account("normal", "low")
            self.accounts[acc["account_id"]] = acc

        for _ in range(mule_count):
            acc = self._create_account("mule", "high", is_mule=True)
            self.accounts[acc["account_id"]] = acc

        for _ in range(dormant_count):
            acc = self._create_account("normal", "medium", is_dormant=True)
            self.accounts[acc["account_id"]] = acc

        for _ in range(high_risk_count):
            acc = self._create_account("business", "high")
            self.accounts[acc["account_id"]] = acc

        logger.info(
            f"Account pool generated: {len(self.accounts)} accounts "
            f"(normal={normal_count}, mule={mule_count}, "
            f"dormant={dormant_count}, high_risk={high_risk_count})"
        )

    def _create_account(
        self,
        account_type: str,
        risk_profile: str,
        is_mule: bool = False,
        is_dormant: bool = False,
    ) -> Dict:
        account_id = f"acc_{uuid4().hex[:10]}"
        created = datetime.utcnow() - timedelta(days=random.randint(30, 1825))
        last_active = (
            datetime.utcnow() - timedelta(days=random.randint(90, 730))
            if is_dormant
            else datetime.utcnow() - timedelta(hours=random.randint(1, 720))
        )
        return {
            "account_id": account_id,
            "account_type": account_type,
            "risk_profile": risk_profile,
            "is_mule": is_mule,
            "is_dormant": is_dormant,
            "created_at": created.isoformat(),
            "last_active": last_active.isoformat(),
            "balance": round(random.uniform(100, 500000), 2),
        }

    def get_random(
        self,
        exclude: Optional[List[str]] = None,
        account_type: Optional[str] = None,
    ) -> Dict:
        candidates = list(self.accounts.values())
        if exclude:
            candidates = [a for a in candidates if a["account_id"] not in exclude]
        if account_type:
            typed = [a for a in candidates if a["account_type"] == account_type]
            candidates = typed if typed else candidates
        return random.choice(candidates)

    def get_mule_accounts(self, count: int = 5) -> List[Dict]:
        mules = [a for a in self.accounts.values() if a["is_mule"]]
        return random.sample(mules, min(count, len(mules)))

    def get_dormant_accounts(self, count: int = 3) -> List[Dict]:
        dormant = [a for a in self.accounts.values() if a["is_dormant"]]
        return random.sample(dormant, min(count, len(dormant)))

    def get_by_id(self, account_id: str) -> Optional[Dict]:
        return self.accounts.get(account_id)

    def list_ids(self) -> List[str]:
        return list(self.accounts.keys())

    def sample_ids(self, n: int) -> List[str]:
        return random.sample(self.list_ids(), min(n, len(self.accounts)))
