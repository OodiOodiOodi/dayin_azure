# models.py
from peewee import Model, CharField, DateTimeField, TextField, BooleanField  # 引入 BooleanField
from config import get_settings
from playhouse.pool import PooledPostgresqlDatabase
from datetime import datetime
from database import postgresPool
import bcrypt  # 引入 bcrypt 库

settings = get_settings()
postgresPool  = PooledPostgresqlDatabase(
    settings.postgresql['database'],
    user=settings.postgresql['user'],
    password=settings.postgresql['password'],
    host=settings.postgresql['host'],
    port=settings.postgresql['port']
)

# 新增的用户表，用于记录用户名和密码
class UserAccount(Model):
    username = CharField(unique=True)  # 用户名，唯一
    password = CharField()  # 密码

    def set_password(self, password):
        """对密码进行加密并存储"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        self.password = hashed.decode('utf-8')

    def check_password(self, password):
        """验证密码是否正确"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

    class Meta:
        database = postgresPool
        table_name = 'user_account'


class User(Model):
    # 用户名字段：你是谁，作为身份标识
    username = CharField()
    # 数据字段：打印的要求：黑白、双面打印、打印份数等
    data = CharField()
    # 文件路径字段：记录文件存储的路径
    file_path = TextField()  # 添加 file_path 字段，允许为空
    # 新增：记录数据添加时间的字段：作为顺序和文件夹的标识
    created_at = DateTimeField(default=datetime.now)
    # 新增：任务状态字段，默认为未打印
    status = CharField(default='未打印')
    print_shop_address = CharField()  # (null=True)表示允许为空

    class Meta:
        database = postgresPool
        table_name = 'user'


def initialize_database():
    try:
        # 连接数据库
        postgresPool.connect()

        # 创建表
        # 检查 UserAccount 表是否存在，如果不存在则创建
        if not UserAccount.table_exists():
            UserAccount.create_table()

        # 检查 User 表是否存在，如果不存在则创建
        if not User.table_exists():
            User.create_table()

        # 检查并创建 control 用户
        def create_control_user():
            control_user = UserAccount.get_or_none(UserAccount.username == 'control')
            if not control_user:
                control_user = UserAccount(username='control')
                control_user.set_password('123456')
                control_user.save()

        # 调用函数创建 control 用户
        create_control_user()

    except Exception as e:
        print(f"数据库初始化出错: {e}")
    finally:
        # 关闭数据库连接
        if not postgresPool.is_closed():
            postgresPool.close()