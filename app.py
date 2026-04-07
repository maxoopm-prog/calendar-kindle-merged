"""
极简日历应用 - Flask后端
运行: python app.py
访问: http://localhost:5000
"""

import os
import io
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dateutil import rrule
from calendar_lib import Calendar
from PIL import Image, ImageOps
from playwright.sync_api import sync_playwright

app = Flask(__name__)
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ 配置 ============
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///calendar.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# ============ 初始化 ============
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ============ 数据库模型 ============
class User(UserMixin, db.Model):
    """用户表"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Event(db.Model):
    """事件表"""
    __tablename__ = 'event'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_str = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD
    content = db.Column(db.String(200), nullable=False)
    recurrence = db.Column(db.String(20), default='once')  # once/daily/weekly/monthly/yearly
    recurrence_rule = db.Column(db.String(500), nullable=True)
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'date_str': self.date_str,
            'content': self.content,
            'recurrence': self.recurrence,
            'is_public': self.is_public
        }


class SiteConfig(db.Model):
    """站点配置表"""
    __tablename__ = 'site_config'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(500), nullable=False)

    @staticmethod
    def get(key, default=None):
        row = SiteConfig.query.filter_by(key=key).first()
        return row.value if row else default

    @staticmethod
    def set(key, value):
        row = SiteConfig.query.filter_by(key=key).first()
        if row:
            row.value = value
        else:
            row = SiteConfig(key=key, value=value)
            db.session.add(row)
        db.session.commit()


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ============ 万年历服务 ============
class CalendarService:
    """日历数据生成 - 使用Calendar库"""
    
    @staticmethod
    def get_month(year, month):
        """生成月份日历数据，去掉最后空白行"""
        view = Calendar.get_month_calendar(year, month)
        
        # 转换为需要的格式
        days = []
        for item in view:
            if item['other_month']:
                days.append(None)
            else:
                days.append({
                    'date': item['date'],
                    'day': item['day'],
                    'lunar': item['lunar'],
                    'festival': item.get('festival', ''),
                })
        
        # 找到最后一个非None的索引
        last_day_idx = -1
        for i in range(len(days) - 1, -1, -1):
            if days[i] is not None:
                last_day_idx = i
                break
        
        # 计算需要的行数（向上取整到完整的一周）
        if last_day_idx >= 0:
            needed_rows = (last_day_idx // 7) + 1
            needed_cells = needed_rows * 7
            # 填充到完整的行
            while len(days) < needed_cells:
                days.append(None)
            return days[:needed_cells]
        
        # 如果没有日期，返回空
        return []


# ============ 认证 API ============
@app.route('/register', methods=['POST'])
def register():
    return jsonify({'success': False, 'message': '注册已关闭'}), 403


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not user.check_password(password):
        return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
    
    login_user(user, remember=True)
    session.permanent = True
    
    return jsonify({'success': True, 'user_id': user.id, 'username': user.username}), 200


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'success': True}), 200


@app.route('/auth/status', methods=['GET'])
def auth_status():
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user_id': current_user.id,
            'username': current_user.username
        }), 200
    return jsonify({'authenticated': False}), 200




# ============ 日历 API ============
@app.route('/api/calendar/<int:year>/<int:month>', methods=['GET'])
def get_calendar(year, month):
    """获取月份日历"""
    if month < 1 or month > 12:
        return jsonify({'success': False}), 400
    
    days = CalendarService.get_month(year, month)
    return jsonify({'success': True, 'days': days}), 200


# ============ 事件 API ============
@app.route('/api/events/<int:year>/<int:month>', methods=['GET'])
@login_required
def get_user_events(year, month):
    """获取用户事件"""
    events = Event.query.filter_by(user_id=current_user.id).all()
    
    result = {}
    month_start = datetime(year, month, 1)
    if month == 12:
        month_end = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = datetime(year, month + 1, 1) - timedelta(days=1)
    
    for event in events:
        dates = expand_dates(event, month_start, month_end)
        for date_str in dates:
            if date_str not in result:
                result[date_str] = []
            result[date_str].append(event.to_dict())
    
    return jsonify({'success': True, 'events': result}), 200


@app.route('/api/events/public/<int:year>/<int:month>', methods=['GET'])
def get_public_events(year, month):
    """获取公开事件"""
    events = Event.query.filter_by(is_public=True).all()
    
    result = {}
    month_start = datetime(year, month, 1)
    if month == 12:
        month_end = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = datetime(year, month + 1, 1) - timedelta(days=1)
    
    for event in events:
        dates = expand_dates(event, month_start, month_end)
        for date_str in dates:
            if date_str not in result:
                result[date_str] = []
            result[date_str].append(event.to_dict())
    
    return jsonify({'success': True, 'events': result}), 200


@app.route('/api/events', methods=['POST'])
@login_required
def create_event():
    """创建事件"""
    data = request.get_json()
    date_str = data.get('date_str', '').strip()
    content = data.get('content', '').strip()
    recurrence = data.get('recurrence', 'once')
    is_public = data.get('is_public', False)
    
    if not date_str or not content:
        return jsonify({'success': False, 'message': '日期和内容不能为空'}), 400
    
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
    except:
        return jsonify({'success': False, 'message': '日期格式错误'}), 400
    
    rule = None
    if recurrence != 'once':
        rule = build_rrule(date_str, recurrence)
    
    event = Event(
        user_id=current_user.id,
        date_str=date_str,
        content=content,
        recurrence=recurrence,
        recurrence_rule=rule,
        is_public=is_public
    )
    db.session.add(event)
    db.session.commit()
    
    return jsonify({'success': True, 'event': event.to_dict()}), 201


@app.route('/api/events/<int:event_id>', methods=['DELETE'])
@login_required
def delete_event(event_id):
    """删除事件"""
    event = Event.query.get(event_id)
    
    if not event or event.user_id != current_user.id:
        return jsonify({'success': False}), 403
    
    db.session.delete(event)
    db.session.commit()
    
    return jsonify({'success': True}), 200


# ============ 辅助函数 ============
def build_rrule(date_str, recurrence):
    """构建RRULE"""
    year, month, day = map(int, date_str.split('-'))
    
    if recurrence == 'daily':
        return 'FREQ=DAILY'
    elif recurrence == 'weekly':
        return 'FREQ=WEEKLY'
    elif recurrence == 'monthly':
        return f'FREQ=MONTHLY;BYMONTHDAY={day}'
    elif recurrence == 'yearly':
        return f'FREQ=YEARLY;BYMONTH={month};BYMONTHDAY={day}'
    return None


def expand_dates(event, start_date, end_date):
    """展开循环事项的日期"""
    dates = []
    
    if event.recurrence == 'once':
        date_obj = datetime.strptime(event.date_str, '%Y-%m-%d').date()
        if start_date.date() <= date_obj <= end_date.date():
            dates.append(event.date_str)
    else:
        try:
            if event.recurrence_rule:
                base = datetime.strptime(event.date_str, '%Y-%m-%d')
                rule = rrule.rrulestr(event.recurrence_rule, dtstart=base)
                
                for dt in rule.between(start_date, end_date, inc=True):
                    dates.append(dt.strftime('%Y-%m-%d'))
        except:
            date_obj = datetime.strptime(event.date_str, '%Y-%m-%d').date()
            if start_date.date() <= date_obj <= end_date.date():
                dates.append(event.date_str)
    
    return dates


# ============ 前端路由 ============
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


# ============ 配置 API ============
KINDLE_WIDTH = 758
KINDLE_HEIGHT = 1024
DEFAULT_SCREENSHOT_URL = 'http://localhost:5008'

@app.route('/api/config/screenshot-url', methods=['GET'])
@login_required
def get_screenshot_url():
    url = SiteConfig.get('screenshot_url', DEFAULT_SCREENSHOT_URL)
    return jsonify({'success': True, 'url': url}), 200


@app.route('/api/config/screenshot-url', methods=['POST'])
@login_required
def set_screenshot_url():
    data = request.get_json()
    url = data.get('url', '').strip()
    if not url:
        return jsonify({'success': False, 'message': 'URL 不能为空'}), 400
    SiteConfig.set('screenshot_url', url)
    return jsonify({'success': True}), 200


# ============ Kindle 截图路由 ============
@app.route('/kindle.png')
def kindle_image():
    """截图目标页面，转换为 Kindle 兼容的灰度 PNG"""
    url = SiteConfig.get('screenshot_url', DEFAULT_SCREENSHOT_URL)
    logger.info(f"Kindle screenshot: {url}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={'width': KINDLE_WIDTH, 'height': KINDLE_HEIGHT})
            page.goto(url, wait_until='networkidle')
            screenshot_bytes = page.screenshot()
            browser.close()
    except Exception as e:
        logger.error(f"Screenshot failed: {e}")
        return "Screenshot failed", 500

    try:
        img = Image.open(io.BytesIO(screenshot_bytes))
        img = img.resize((KINDLE_WIDTH, KINDLE_HEIGHT), Image.Resampling.LANCZOS)
        img = ImageOps.grayscale(img)
        output = io.BytesIO()
        img.save(output, format='PNG')
        output.seek(0)
    except Exception as e:
        logger.error(f"Image conversion failed: {e}")
        return "Image conversion failed", 500

    return send_file(output, mimetype='image/png')


# ============ 初始化 ============
def init_db():
    with app.app_context():
        db.create_all()
        
        if not User.query.filter_by(username='demo').first():
            demo = User(username='demo')
            demo.set_password('demo123')
            db.session.add(demo)
            db.session.commit()
            print('✓ 演示用户: demo / demo123')


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5008, debug=True)

