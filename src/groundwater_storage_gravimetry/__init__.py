"""Core spatial statistics and hydrological model evaluation library."""

from .metrics import kling_gupta_efficiency, nash_sutcliffe_efficiency, rmse

__all__ = [
    "kling_gupta_efficiency",
    "nash_sutcliffe_efficiency",
    "rmse",
]
__version__ = "0.1.0"
