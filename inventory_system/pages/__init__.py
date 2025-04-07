from .about import about
from .overview import overview
from .index import index
from .profile import profile
from .settings import settings
from .table import table
from .register import register_page
from .login import login_page
from .logout import logout_page
from .supplier_approval import supplier_approval
from .supplier_register import supplier_register
from .admin_management import admin_management

__all__ = ["about", "overview", "profile", "settings", "index", 
           "table","register_page","login_page","logout_page", "supplier_approval", 
           "supplier_register","admin_management"]
