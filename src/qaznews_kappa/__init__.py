"""Inter-annotator agreement for categorical labels."""

from .agreement import cohen_kappa, fleiss_kappa, load, report

__version__ = "0.2.0"
__all__ = ["cohen_kappa", "fleiss_kappa", "load", "report"]
