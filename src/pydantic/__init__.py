"""Lightweight stand-in for pydantic used in offline tests."""

from __future__ import annotations

from typing import Any, Dict


class _UnsetType:
    pass


_UNSET = _UnsetType()


class FieldInfo:
    def __init__(self, default: Any = _UNSET, default_factory: Any | None = None) -> None:
        self.default = default
        self.default_factory = default_factory


def Field(*, default: Any = _UNSET, default_factory: Any | None = None) -> FieldInfo:
    return FieldInfo(default=default, default_factory=default_factory)


class BaseModel:
    def __init__(self, **data: Any) -> None:
        annotations = getattr(self.__class__, "__annotations__", {})
        for name in annotations:
            value = self._resolve_default(name)
            if name in data:
                value = data[name]
            setattr(self, name, value)
        for key, value in data.items():
            if key not in annotations:
                setattr(self, key, value)

    @classmethod
    def _field_info(cls, name: str) -> FieldInfo | _UnsetType | Any:
        value = getattr(cls, name, _UNSET)
        return value

    @classmethod
    def _resolve_default(cls, name: str) -> Any:
        info = cls._field_info(name)
        if isinstance(info, FieldInfo):
            if info.default_factory is not None:
                return info.default_factory()
            if info.default is not _UNSET:
                return info.default
            return None
        if info is _UNSET:
            return None
        return info

    @classmethod
    def model_validate(cls, data: Any) -> "BaseModel":
        if isinstance(data, cls):
            return data
        if not isinstance(data, dict):
            raise TypeError("Expected mapping for model validation")
        return cls(**data)

    def model_dump(self) -> Dict[str, Any]:
        annotations = getattr(self.__class__, "__annotations__", {})
        return {name: getattr(self, name) for name in annotations}


__all__ = ["BaseModel", "Field"]
