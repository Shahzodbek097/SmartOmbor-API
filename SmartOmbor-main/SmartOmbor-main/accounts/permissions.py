"""DRF permissions — API equivalent of accounts/decorators.py (kept untouched)."""
from rest_framework.permissions import BasePermission


class IsSuperuserOrInGroups(BasePermission):
    """Allow superuser (always) or users in any of `groups` (and Django perms if set)."""

    groups: tuple = ()
    perms: tuple = ()  # e.g. ("products.view_product",)

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if self.groups and user.groups.filter(name__in=self.groups).exists():
            return True
        if self.perms:
            return any(user.has_perm(p) for p in self.perms)
        return False


class IsRahbar(IsSuperuserOrInGroups):
    groups = ("Rahbar",)


class IsOmborchi(IsSuperuserOrInGroups):
    groups = ("Omborchi",)


class IsSotuvchi(IsSuperuserOrInGroups):
    groups = ("Sotuvchi",)


class IsAnyRole(IsSuperuserOrInGroups):
    groups = ("Rahbar", "Omborchi", "Sotuvchi")


class ProductsAccess(IsSuperuserOrInGroups):
    # Old code used @permission_required("products.view_product") etc.
    # API: products usable by any real role (Rahbar/Omborchi/Sotuvchi) to keep frontend simple.
    groups = ("Rahbar", "Omborchi", "Sotuvchi")
    perms = ("products.view_product", "products.add_product", "products.change_product")
