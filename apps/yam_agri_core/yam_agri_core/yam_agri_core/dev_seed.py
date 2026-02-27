from __future__ import annotations

from yam_agri_core.yam_agri_core.seed import dev_data as _dev_data

# Backward-compatibility shim for legacy bench execute paths.
__all__ = [name for name in dir(_dev_data) if not name.startswith("_")]

for _name in __all__:
	globals()[_name] = getattr(_dev_data, _name)

