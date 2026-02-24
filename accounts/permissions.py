from rest_framework import permissions


class IsSuperadmin(permissions.BasePermission):
    """Permission check for superadmin role"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'superadmin'


class IsAdmin(permissions.BasePermission):
    """Permission check for admin role"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsAdminOrSuperadmin(permissions.BasePermission):
    """Permission check for admin or superadmin role"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['admin', 'superadmin']


class IsEmployee(permissions.BasePermission):
    """Permission check for employee role"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'employee'


class IsClient(permissions.BasePermission):
    """Permission check for client role"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'client'


class IsStaff(permissions.BasePermission):
    """Permission check for staff (admin, employee, or superadmin)"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['admin', 'employee', 'superadmin']
