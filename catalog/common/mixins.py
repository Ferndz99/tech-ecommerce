from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.decorators import action


class BaseAPIViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet for public/admin APIs with support for multiple serializers.

    This ViewSet provides:

    ---------------------------------------------------------
    - Dynamic serializers based on the action:

    * create/update/partial_update → write_serializer_class

    * list → public or admin list serializer

    * retrieve → public or admin read serializer

    - Automatic permissions:

    * Public: list and retrieve

    * Admin: create, update, partial_update, destroy

    - Extended methods for:

    * Always responding with a read serializer after create/edit.

    * Easily instantiate the correct read serializer using:

    get_read_serializer_instance()

    Child classes must define:

    - public_list_serializer_class

    - admin_list_serializer_class

    - write_serializer_class

    - admin_read_serializer_class

    - public_read_serializer_class

    Optionally:

    - Override get_permissions() or get_serializer_class()
    """

    public_list_serializer_class = None
    admin_list_serializer_class = None
    write_serializer_class = None
    admin_read_serializer_class = None
    public_read_serializer_class = None
    serializer_class = public_list_serializer_class

    def get_permissions(self):
        """
        Control permissions by action:

        - Public: list, retrieve
        - Admin: create, update, partial_update, destroy
        """
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]

        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminUser()]

        return super().get_permissions()

    def get_serializer_class(self):  # type: ignore
        """
        Returns the appropriate serializer based on:

        - Action

        Whether the user is admin or public
        """
        if self.action in ["create", "update", "partial_update"]:
            return self.write_serializer_class

        if self.action in ["list"]:
            if self.request.user.is_staff:
                return self.admin_list_serializer_class
            return self.public_list_serializer_class

        if self.action in ["retrieve"]:
            if self.request.user.is_staff:
                return self.admin_read_serializer_class
            return self.public_read_serializer_class

        return super().get_serializer_class()

    def get_read_serializer_instance(self, instance, *args, **kwargs):
        """
        Returns an instance of the appropriate read serializer.

        Used in:
        - create()
        - update()
        - mixins that want to return the entity in read mode

        Uses user permissions to differentiate between admin and public serializers.
        """
        if (
            self.request.user
            and self.request.user.is_authenticated
            and self.request.user.is_staff
        ):
            SerializerClass = self.admin_read_serializer_class
        else:
            SerializerClass = self.public_read_serializer_class

        if SerializerClass is None:
            raise NotImplementedError(
                "BaseAPIViewSet requiere que 'admin_read_serializer_class' "
                "y 'public_read_serializer_class' estén definidos en la clase hija."
            )

        return SerializerClass(
            instance,
            *args,
            **kwargs,
            context=self.get_serializer_context(),
        )

    # ---------------------------------------------------
    # Create
    # ---------------------------------------------------
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        read_serializer = self.get_read_serializer_instance(instance)
        headers = self.get_success_headers(read_serializer.data)
        return Response(
            read_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    # ---------------------------------------------------
    # Update
    # ---------------------------------------------------
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        read_serializer = self.get_read_serializer_instance(instance)
        return Response(read_serializer.data)

    # ---------------------------------------------------
    # Partial Update (PATCH)
    # ---------------------------------------------------
    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)


class LifeCycleActionMixin:
    """
    A mixin that adds standard lifecycle actions for ViewSets that use a model based on 'LifeCycleMixin'.

    This mixin assumes that the associated model implements the following methods:

    - activate()
    - deactivate()
    - soft_delete()
    - restore()
    - hard_delete()

    --------------------------------

    Features included:

    - activate: Activates an instance (POST).
    - deactivate: Deactivates an instance (POST).
    - restore: Restores a previously deleted instance (POST).
    - destroy: Overrides the standard DELETE to perform a 'soft_delete'.
    - hard_delete: Permanently deletes the instance (DELETE), requires confirmation.

    --------------------------------

    Notes:

    - For 'destroy', the correct read serializer is returned based on the user's permissions.
    - 'hard_delete' should only be accessible to administrators (see 'get_permissions').
    """

    @action(detail=True, methods=["post"])
    def activate(self, request, *args, **kwargs):
        """Activates a specific instance and returns its updated state."""
        instance = self.get_object()
        instance.activate()
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def deactivate(self, request, *args, **kwargs):
        """Disables a specific instance and returns its updated state."""
        instance = self.get_object()
        instance.deactivate()
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def restore(self, request, *args, **kwargs):
        """Restores a previously deleted instance (soft delete)."""
        instance = self.get_object()
        instance.restore()
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Performs a soft delete instead of a traditional delete.
        Returns the corresponding read serializer based on user permissions.
        """
        instance = self.get_object()
        instance.soft_delete()
        instance.refresh_from_db()
        read_serializer = self.get_read_serializer_instance(instance)
        return Response(read_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["delete"])
    def hard_delete(self, request, *args, **kwargs):
        """
        Permanently deletes an instance.

        Requires:
        {"confirm": true}

        Returns:

        - 204 NO CONTENT if successfully deleted.
        - 400 if no confirmation is sent.
        """
        confirm = request.data.get("confirm")

        if confirm is not True:
            return Response(
                {
                    "detail": "Hard delete requires confirm=true",
                    "hint": 'Send {"confirm": true} in the request body.',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance = self.get_object()
        instance.hard_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
