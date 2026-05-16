def get(
    obj: dict[str, object] | list[object] | None,
    path: list[str | int],
    defval: object = None
) -> object:
    """
    Аналог lodash.get.
    Вернуть значение сложного объекта по указанному пути.
    """
    for k in path:
        if obj is None:
            return defval
        elif hasattr(obj, 'get'):
            if k not in obj:
                return defval
            obj = obj.get(k) # type: ignore
        elif hasattr(obj, '__iter__'):
            if type(k) != int:
                return defval
            elif len(obj) - 1 < k:
                return defval
            else:
                obj = obj[k] # type: ignore
        else:
            return defval
    return obj