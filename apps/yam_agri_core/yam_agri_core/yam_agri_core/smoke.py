from __future__ import annotations

from yam_agri_core.yam_agri_core.health import checks as _checks

# Backward-compatibility shim for legacy bench execute paths.
__all__ = [name for name in dir(_checks) if not name.startswith("_")]

for _name in __all__:
	globals()[_name] = getattr(_checks, _name)

