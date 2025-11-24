from djoser.views import UserViewSet



class CustomAccountViewSet(UserViewSet):
    """UserViewSet with extended documentation for OpenAPI/Swagger."""

    def set_username(self, request, *args, **kwargs):
        raise NotImplementedError("This endpoint is disabled.")

    def reset_username(self, request, *args, **kwargs):
        raise NotImplementedError("This endpoint is disabled.")

    def reset_username_confirm(self, request, *args, **kwargs):
        raise NotImplementedError("This endpoint is disabled.")