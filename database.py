# database.py
from config import get_settings
from playhouse.pool import PooledPostgresqlDatabase

__POSTGRES_PARAMS__ = get_settings().postgresql

# 连接池
postgresPool = PooledPostgresqlDatabase(
    **__POSTGRES_PARAMS__,
    max_connections=20,
    timeout=10
)