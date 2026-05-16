import typing

T = typing.TypeVar("T", int, float)
def clamp(
    value: T,
    min_value: T,
    max_value: T,
):
    return max(min_value, min(value, max_value))