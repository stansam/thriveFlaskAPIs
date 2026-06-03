from typing import TypedDict, Callable, Sequence


class RouteConfig(TypedDict):
    url_rule: str
    view_func: Callable
    methods: Sequence[str]