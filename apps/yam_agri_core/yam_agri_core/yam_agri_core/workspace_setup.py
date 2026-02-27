from __future__ import annotations

from yam_agri_core.yam_agri_core.workspace import setup as _workspace_setup

# Backward-compatibility shim for legacy bench execute paths.
__all__ = [name for name in dir(_workspace_setup) if not name.startswith("_")]

for _name in __all__:
	globals()[_name] = getattr(_workspace_setup, _name)

