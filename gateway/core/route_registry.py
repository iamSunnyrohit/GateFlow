from dataclasses import dataclass, replace
from threading import RLock

@dataclass(frozen=True)
class Route:
    name: str
    path_prefix: str
    service_url: str
    strip_prefix: str
    methods: frozenset[str]

    def matches(self, path: str) -> bool:
        return (
            path == self.path_prefix
            or path.startswith(self.path_prefix + "/")
        )


class RouteRegistry:

    def __init__(self):
        self._routes: list[Route] = []
        self._lock = RLock()
    
    def clear(self):
        """Remove all routes from the in-memory registry."""
        with self._lock:
            self._routes.clear()
            
    def _validate(self, route: Route):
        if not route.name.strip():
            raise ValueError("Route name cannot be empty")

        if not route.path_prefix.startswith("/"):
            raise ValueError("Path prefix must start with '/'")

        if route.path_prefix != "/" and route.path_prefix.endswith("/"):
            raise ValueError("Path prefix cannot end with '/'")

        if not route.service_url.startswith(("http://", "https://")):
            raise ValueError("Service URL must start with http:// or https://")

        if not route.methods:
            raise ValueError("At least one HTTP method is required")

        if not route.methods.issubset(
            {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}
        ):
            raise ValueError("Unsupported HTTP method")

    def register(self, route: Route):
        """Register a new route."""
        self._validate(route)

        with self._lock:
            if any(
                existing.name == route.name
                or existing.path_prefix == route.path_prefix
                for existing in self._routes
            ):
                raise ValueError(
                    f"Duplicate route name or path: {route.path_prefix}"
                )

            self._routes.append(route)
            self._routes.sort(
                key=lambda item: len(item.path_prefix),
                reverse=True,
            )

        return route

    def update(self, name: str, updated_route: Route):
        """Update an existing route by its name."""
        self._validate(updated_route)

        with self._lock:
            index = next(
                (
                    i for i, route in enumerate(self._routes)
                    if route.name == name
                ),
                None,
            )

            if index is None:
                raise KeyError(f"Route '{name}' not found")

            if updated_route.name != name:
                raise ValueError("Route name cannot be changed")

            for i, existing in enumerate(self._routes):
                if i != index and (
                    existing.path_prefix == updated_route.path_prefix
                ):
                    raise ValueError(
                        f"Path prefix already exists: {updated_route.path_prefix}"
                    )

            self._routes[index] = updated_route
            self._routes.sort(
                key=lambda item: len(item.path_prefix),
                reverse=True,
            )

        return updated_route

    def remove(self, name: str):
        """Remove a route by its name."""
        with self._lock:
            for index, route in enumerate(self._routes):
                if route.name == name:
                    return self._routes.pop(index)

        raise KeyError(f"Route '{name}' not found")

    def get_by_name(self, name: str) -> Route | None:
        """Find a route by its name."""
        with self._lock:
            return next(
                (route for route in self._routes if route.name == name),
                None,
            )

    def resolve(self, path: str) -> Route | None:
        """Find the most specific route matching a request path."""
        with self._lock:
            for route in self._routes:
                if route.matches(path):
                    return route

        return None

    def list_routes(self) -> list[dict]:
        """Return all registered routes."""
        with self._lock:
            return [
                {
                    "name": route.name,
                    "path_prefix": route.path_prefix,
                    "service_url": route.service_url,
                    "strip_prefix": route.strip_prefix,
                    "methods": sorted(route.methods),
                }
                for route in self._routes
            ]


# Global route registry

route_registry = RouteRegistry()


# Existing User Service route

route_registry.register(
    Route(
        name="user-service",
        path_prefix="/api/users",
        service_url="http://user-service:8002",
        strip_prefix="/api",
        methods=frozenset({"GET"}),
    )
)


# Existing Product Service route

route_registry.register(
    Route(
        name="product-service",
        path_prefix="/api/products",
        service_url="http://product-service:8003",
        strip_prefix="/api",
        methods=frozenset({"GET"}),
    )
)
