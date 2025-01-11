from common.constants import SystemConstants
from common.database_v2 import DEFAULT_TABLE_ARGS, DBBase
from sqlalchemy import Column, BigInteger, Boolean, ForeignKey, Integer, String, Text, Float
from sqlalchemy.sql import func


class Role(DBBase):
    __tablename__ = 'roles'
    __primary_key__ = "role_id"
    __table_args__ = DEFAULT_TABLE_ARGS

    role_id = Column(String(32), primary_key=True)
    name = Column(String(50), nullable=False)
    role = Column(String(50), nullable=False)  # Admin, Customer
    permissions = Column(String(1000), nullable=False, server_default='[]')

    is_active = Column(Boolean, nullable=False, default=True)
    date_added = Column(BigInteger, nullable=False)
    date_updated = Column(BigInteger, nullable=False)


class User(DBBase):
    __tablename__ = 'users'
    __primary_key__ = "user_id"
    __table_args__ = DEFAULT_TABLE_ARGS

    user_id = Column(String(32), primary_key=True)
    stripe_customer_id = Column(String(32), nullable=True)

    # will be null for customer
    role_id = Column(ForeignKey(Role.role_id, onupdate='RESTRICT', ondelete='RESTRICT'), nullable=True)

    email = Column(String(100), nullable=False, unique=True)
    password = Column(String(32), nullable=False)

    name = Column(String(128), nullable=True)
    address = Column(String(1024), nullable=True)
    avatar = Column(String(1024), nullable=True)
    status = Column(String(20), nullable=True)
    about = Column(String(1024), nullable=True)
    phone = Column(String(20), nullable=True)

    google_user = Column(Boolean, nullable=False, default=False)
    email_verified = Column(Boolean, nullable=False, default=False)
    two_factor_enabled = Column(Boolean, nullable=False, default=False)
    otp_secret = Column(String(32), nullable=True)
    ask_password_change = Column(Boolean, nullable=False, default=False)
    last_login = Column(BigInteger, nullable=True)
    last_used_ip = Column(String(32), nullable=True)

    trial_availed = Column(Boolean, nullable=False, default=False)
    intro_offer_availed = Column(Boolean, nullable=False, default=False)  # One Dollar First Month
    api_call_access = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    date_added = Column(BigInteger, nullable=False)
    date_updated = Column(BigInteger, nullable=False)


class VerificationCode(DBBase):
    __tablename__ = 'verification_codes'
    __primary_key__ = "code_id"
    __table_args__ = DEFAULT_TABLE_ARGS

    code_id = Column(String(32), primary_key=True)

    user_id = Column(ForeignKey(User.user_id, onupdate='RESTRICT', ondelete='RESTRICT'), nullable=False)

    code = Column(String(10), nullable=False)
    expiry_time = Column(BigInteger, nullable=False)

    date_added = Column(BigInteger, nullable=False)


class UserSession(DBBase):
    __tablename__ = 'user_sessions'
    __primary_key__ = "session_id"
    __table_args__ = DEFAULT_TABLE_ARGS

    session_id = Column(String(32), primary_key=True)

    user_id = Column(ForeignKey(User.user_id, onupdate='RESTRICT', ondelete='RESTRICT'), nullable=False)

    session_data = Column(String(1024), nullable=False)

    is_active = Column(Boolean, nullable=False, default=True)
    date_added = Column(BigInteger, nullable=False)
    date_updated = Column(BigInteger, nullable=False)


class Settings(DBBase):
    __tablename__ = 'settings'
    __primary_key__ = "setting_id"
    __table_args__ = DEFAULT_TABLE_ARGS

    setting_id = Column(String(32), primary_key=True)

    setting_key = Column(String(50), nullable=False, unique=True)
    setting_json = Column(Text, nullable=False)
    
    is_active = Column(Boolean, nullable=False, default=True)
    date_added = Column(BigInteger, nullable=False)
    date_updated = Column(BigInteger, nullable=False)


class Profile(DBBase):
    __tablename__ = 'profiles'
    __primary_key__ = "profile_id"
    __table_args__ = DEFAULT_TABLE_ARGS

    profile_id = Column(String(32), primary_key=True)

    user_id = Column(ForeignKey(User.user_id, onupdate='RESTRICT', ondelete='RESTRICT'), nullable=False)

    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=True)
    password = Column(String(50), nullable=True)

    avatar = Column(String(300), nullable=True)
    bio = Column(String(600), nullable=True)

    created = Column(Boolean, nullable=False, default=False)

    proxy_type = Column(String(50), nullable=True)  # HTTP, SOCKS5
    proxy_address = Column(String(500), nullable=True)  # username:password@host:port
    
    start_page = Column(Text, nullable=True)
    current_page = Column(Text, nullable=True)  # to use for re-open where left
        
    notes = Column(Text, nullable=True)

    process_id = Column(String(200), nullable=True) 
    last_used = Column(BigInteger, nullable=True)
    status = Column(String(100), nullable=False, default='Inactive')  # Inactive, Active, Failed
    comments = Column(Text, nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)
    date_added = Column(BigInteger, nullable=False)
    date_updated = Column(BigInteger, nullable=False)
    

class Account(DBBase):
    __tablename__ = 'accounts'
    __primary_key__ = "account_id"
    __table_args__ = DEFAULT_TABLE_ARGS

    account_id = Column(String(32), primary_key=True)

    profile_id = Column(ForeignKey(Profile.profile_id, onupdate='RESTRICT', ondelete='RESTRICT'), nullable=False)

    website = Column(Text, nullable=False)

    fullname = Column(String(100), nullable=False)
    username = Column(String(100), nullable=False)
    password = Column(String(50), nullable=False)
    
    created = Column(Boolean, nullable=False, default=False)
    verified = Column(Boolean, nullable=False, default=False)
    
    meta_data = Column(Text, nullable=False, default='{}')  # {watchlist: [BURU, HMBL, ]}

    blocked = Column(Boolean, nullable=False, default=False)

    date_added = Column(BigInteger, nullable=False)
    date_updated = Column(BigInteger, nullable=False)
