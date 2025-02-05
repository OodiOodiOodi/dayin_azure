# app.py
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from models import User, UserAccount, postgresPool, initialize_database
import os
from datetime import datetime
import shutil  # 引入 shutil 模块用于删除文件夹
import json
from pathlib import Path
import subprocess
import platform

app = Flask(__name__)
# 设置一个唯一且保密的 secret_key：这段代码的主要意义是为 Flask 应用设置一个唯一且保密的 secret_key，并确保该密钥已正确配置
app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    raise ValueError("SECRET_KEY environment variable is not set.") 

# 配置上传文件夹
UPLOAD_ROOT_FOLDER = '/home/打印文件'
app.config['UPLOAD_ROOT_FOLDER'] = UPLOAD_ROOT_FOLDER

# 确保上传根文件夹存在
if not os.path.exists(UPLOAD_ROOT_FOLDER):
    os.makedirs(UPLOAD_ROOT_FOLDER)


# 在应用启动时调用数据库初始化函数
initialize_database()


# 新的首页路由
@app.route('/')
def home():
    return render_template('home.html')


# 新添加的路由，用于处理注册请求
@app.route('/register', methods=['GET', 'POST'])
def register():
    error_message = None  # 初始化 error_message 变量
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username and password:
            # 检查用户名是否已存在
            existing_user = UserAccount.get_or_none(UserAccount.username == username)
            if existing_user:
                error_message = "用户名已存在！"
            else:
                # 创建新用户
                new_user = UserAccount(username=username)
                new_user.set_password(password)
                new_user.save()
                return redirect(url_for('login'))
        else:
            error_message = "用户名和密码是必填项！"
    return render_template('register.html', error_message=error_message)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error_message = None
    role = request.args.get('role')
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')  # 获取用户输入的密码

        # 检查用户名是否存在
        user = UserAccount.get_or_none(UserAccount.username == username)

        if role == 'consumer':
            session['username'] = username
            return redirect(url_for('print_shops'))
        elif role == 'admin':
            if not user:  # user是布尔
                # 如果用户名不存在，闪现错误信息并重定向到登录页面
                error_message = "用户名不存在"
                return render_template('login.html', error_message=error_message, role=role)

            if username == 'control':
                # 如果输入的用户名是 control
                if user.check_password(password):
                    # 且密码正确，重定向到显示所有打印任务的页面
                    return redirect(url_for('all_print_tasks'))
                else:
                    # 密码不正确，闪现错误信息并重定向到登录页面
                    error_message = '密码不正确'
                    return render_template('login.html', error_message=error_message, role=role)
            elif username:
                if user.check_password(password):
                    session['username'] = username  # 将用户的用户名存储在会话（session）中。session 是一个字典（类似 Python 中的字典），用于存储与当前用户会话相关的数据。
                    return redirect(url_for('print_shops'))
                else:
                    error_message = "密码错误"
                    return render_template('login.html', error_message=error_message, role=role)

    return render_template('login.html', error_message=error_message, role=role)


# 打印店信息页面
@app.route('/print_shops')
def print_shops():
    shops = [
        {'name': '迅捷打印中心', 'address': '北京市朝阳区幸福路123号'},
        {'name': '优质打印店', 'address': '上海市浦东新区科技大道456号'},
        {'name': '快捷打印服务', 'address': '广州市天河区商业街789号'},
        {'name': '高效打印坊', 'address': '深圳市南山区创新路101号'},
        {'name': '专业打印屋', 'address': '成都市锦江区文化路202号'}
    ]
    return render_template('print_shops.html', shops=shops)


@app.route('/select_print_shop')
def select_print_shop():
    name = request.args.get('name')
    if name:
        session['print_shop_address'] = [name]  # 将选中的地址存储在 session 中
    return redirect(url_for('index', name=name))  # 重定向到 index 页面并传递地址参数


@app.route('/index')
def index():
    username = session.get('username')
    address = session.get('name')
    if username:
        # 查询当前用户数据
        users = User.select().where(User.username == username)
        return render_template('index.html', users=users)
    else:
        return redirect(url_for('login'))


# 新添加的路由，用于显示所有打印任务
@app.route('/all_print_tasks')
def all_print_tasks():
    # 查询所有用户数据
    all_users = User.select()
    return render_template('all_print_tasks.html', users=all_users)


@app.route('/delete/<int:user_id>')
def delete(user_id):
    user = User.get_or_none(id=user_id)
    if user:
        # 如果 file_path 存在，尝试删除对应的文件夹
        if user.file_path and os.path.exists(user.file_path):
            try:
                shutil.rmtree(user.file_path)  # 删除整个文件夹及其内容
            except Exception as e:
                print(f"删除文件夹时出错：{e}")
        
        # 删除用户记录
        user.delete_instance()
    
    # 获取请求的来源页面
    referrer = request.referrer
    if 'all_print_tasks' in referrer:
        return redirect(url_for('all_print_tasks'))
    elif 'index' in referrer:
        return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))  # 默认重定向到index


@app.route('/update/<int:user_id>', methods=['GET', 'POST'])
def update(user_id):
    user = User.get_or_none(id=user_id)
    if user:
        if request.method == 'POST':
            new_data = request.form.get('new_data')
            new_file = request.files.get('file')
            if new_data:
                user.data = new_data
            if new_file:
                # 创建新的上传文件夹
                current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                user_upload_folder = os.path.join(app.config['UPLOAD_ROOT_FOLDER'], f"{current_time}_{user.username}_{user.data}")
                if not os.path.exists(user_upload_folder):
                    os.makedirs(user_upload_folder)

                # 保存新文件到用户特定的上传文件夹
                new_file_path = os.path.join(user_upload_folder, new_file.filename)
                new_file.save(new_file_path)

                # 删除旧文件（如果存在）
                if user.file_path and os.path.exists(user.file_path):
                    os.remove(user.file_path)

                # 更新数据库中的文件路径
                user.file_path = new_file_path

            user.save()
            return redirect(url_for('index'))
        else:
            # 如果是 GET 请求，返回一个包含当前用户数据的表单页面
            return render_template('update.html', user=user)
    return redirect(url_for('index'))


# 新添加的路由，用于处理文件上传请求
@app.route('/upload_file', methods=['POST'])
def upload_file():
    username = session.get('username')
    data = request.form.get('data')
    files = request.files.getlist('file')  # 获取多个文件
    print_address = session.get('print_shop_address')  # 获取打印店地址

    if data and print_address and files:
        # 创建用户特定的上传文件夹
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        user_upload_folder = os.path.join(app.config['UPLOAD_ROOT_FOLDER'], f"{current_time}_{print_address}_{username}_{data}")
        if not os.path.exists(user_upload_folder):
            os.makedirs(user_upload_folder)

        # 遍历文件列表，将文件保存到文件夹中
        for file in files:
            file_path = os.path.join(user_upload_folder, file.filename)
            file.save(file_path)

        user_upload_folder = Path(user_upload_folder)
        # 创建用户记录，同时保存文件路径到数据库
        User.create(username=username, data=data, file_path=user_upload_folder, print_shop_address=print_address)  

        # 重定向到首页，刷新页面信息
        return redirect(url_for('index', address=print_address))
    else:
        return jsonify({"status": "error", "message": "Username, data, and files are required!"})


@app.route('/mark_as_completed/<int:user_id>')
def mark_as_completed(user_id):
    user = User.get_or_none(id=user_id)
    if user:
        user.status = '已完成打印'
        user.save()
    return redirect(url_for('all_print_tasks'))


@app.route('/mark_as_uncompleted/<int:user_id>')
def mark_as_uncompleted(user_id):
    user = User.get_or_none(id=user_id)
    if user:
        user.status = '未打印'
        user.save()
    return redirect(url_for('all_print_tasks'))


@app.route('/open_folder/<int:user_id>')
def open_folder(user_id):
    user = User.get_or_none(id=user_id)
    if user and user.file_path and os.path.exists(user.file_path):
        if platform.system() == "Windows":
            # 在Windows系统中使用explorer打开文件夹
            os.startfile(user.file_path)
        elif platform.system() == "Darwin":
            # 在Mac系统中使用open命令打开文件夹
            subprocess.call(["open", user.file_path])
        else:
            # 在Linux系统中使用xdg-open命令打开文件夹
            subprocess.call(["xdg-open", user.file_path])
        return redirect(url_for('all_print_tasks'))
    else:
        flash('文件夹不存在或用户记录有误', 'error')
        return redirect(url_for('all_print_tasks'))


if __name__ == '__main__':
    app.run(debug=True)