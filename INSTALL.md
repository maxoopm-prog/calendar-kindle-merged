# 极简日历应用 - 安装指南

## 关键问题

**应用无法启动的原因：Flask依赖没有安装！**

## 解决方案

### 方法1：直接安装依赖（推荐）

```bash
cd /root/docker/rili/  # 或你的应用目录
pip install -r requirements.txt
python app.py
```

### 方法2：使用Docker Dockerfile

创建 `Dockerfile`：

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["python", "app.py"]
```

构建并运行：

```bash
docker build -t calendar-app .
docker run -p 5000:5000 calendar-app
```

### 方法3：检查依赖是否安装

```bash
python -c "import flask; import flask_sqlalchemy; print('✓ 依赖OK')"
```

如果出现 `ModuleNotFoundError`，说明需要安装。

## 必需依赖

```
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-Login==0.6.2
werkzeug==2.3.7
SQLAlchemy==2.0.20
python-dateutil==2.8.2
```

## 验证应用正常运行

启动后，访问：

```
http://localhost:5000/
# 应该看到日历界面

http://localhost:5000/api/calendar/2024/5
# 应该返回JSON数据，包含 success: true 和 days 数组
```

## 常见错误

**错误：ModuleNotFoundError: No module named 'flask_sqlalchemy'**
→ 解决：`pip install -r requirements.txt`

**错误：错误的端口已在使用**
→ 解决：修改app.py最后的 `port=5000` 为其他端口，或关闭占用该端口的程序

**错误：日历显示空白**
→ 检查浏览器开发者工具（F12）Console标签，应该看到详细的调试日志
