# In inventory_system/utils/auth.py
from reflex_local_auth import LocalUser
from inventory_system.models import UserInfo

def register_supplier(username: str, email: str, default_password: str, session) -> int:
    try:
        new_user = LocalUser(
            username=username,
            password_hash=LocalUser.hash_password(default_password),
            enabled=True
        )
        session.add(new_user)
        session.commit()
        
        user_info = UserInfo(
            email=email,
            user_id=new_user.id,
            is_supplier=True
        )
        user_info.set_role()
        session.add(user_info)
        session.commit()
        return new_user.id
    except Exception as e:
        session.rollback()
        raise e

