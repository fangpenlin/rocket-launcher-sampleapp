from flask_principal import identity_loaded
from flask_principal import Permission
from flask_principal import Principal
from flask_principal import RoleNeed

admin_role_need = RoleNeed("admin")

admin_permission = Permission(admin_role_need)
