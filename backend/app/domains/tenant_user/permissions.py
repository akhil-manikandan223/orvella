from enum import StrEnum


class TenantPermission(StrEnum):
    """Fine-grained permissions a tenant role can carry.

    Deliberately named Resource.Action (see ORVELLA_PROJECT_PLAN.md #12) so
    this reads the same way once Phase 4 entities (People, Departments, ...)
    add their own permissions alongside these.
    """

    TENANT_USERS_VIEW = 'TenantUsers.View'
    TENANT_USERS_MANAGE = 'TenantUsers.Manage'

    DEPARTMENTS_VIEW = 'Departments.View'
    DEPARTMENTS_MANAGE = 'Departments.Manage'

    LOCATIONS_VIEW = 'Locations.View'
    LOCATIONS_MANAGE = 'Locations.Manage'

    PEOPLE_VIEW = 'People.View'
    PEOPLE_MANAGE = 'People.Manage'


# A small fixed role set, not a tenant-customizable role builder - see
# TenantUser.role. Every tenant user can view their tenant's own data;
# only admins can create/update/delete it.
ROLE_PERMISSIONS: dict[str, frozenset[TenantPermission]] = {
    'admin': frozenset(TenantPermission),
    'member': frozenset(
        {
            TenantPermission.TENANT_USERS_VIEW,
            TenantPermission.DEPARTMENTS_VIEW,
            TenantPermission.LOCATIONS_VIEW,
            TenantPermission.PEOPLE_VIEW,
        }
    ),
}


def role_has_permission(role: str, permission: TenantPermission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, frozenset())
