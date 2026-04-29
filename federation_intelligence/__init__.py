"""Federation Intelligence Layer — identifies entity relationships and recommends federated views."""

from .agent import run as run_federation_intelligence
from .schemas import FederationIntelligenceOutput

__all__ = ["run_federation_intelligence", "FederationIntelligenceOutput"]
