from rest_framework.permissions import BasePermission


class IsAdminToDelete(BasePermission):
    message = "Видаляти можуть лише адміністратори."

    def has_permission(self, request, view):
        if request.method == "DELETE":
            return request.user.is_staff
        return True
