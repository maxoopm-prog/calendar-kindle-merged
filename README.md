# 极简日历 × Kindle 墨水屏显示

一个极简风格的个人日历 Web 应用，支持农历、事项管理，并可将页面截图推送到 Kindle 墨水屏显示。

![界面风格](https://img.shields.io/badge/风格-极简黑白-000000) ![Python](https://img.shields.io/badge/Python-3.10+-blue) ![Flask](https://img.shields.io/badge/Flask-2.3-green) ![Kindle](https://img.shields.io/badge/Kindle-6th%20gen-orange)

---

## 功能特性

**日历**
- 月历视图，显示农历日期、农历节假日、公历节假日、二十四节气
- 点击月份标题可跳转到任意年月
- 下方「下月及以后事项」栏，一眼看到近期安排

**事项管理**
- 点击日期格子添加事项
- 支持循环规则：单次 / 每日 / 每周 / 每月 / 每年
- 支持公开/私有，公开事项所有访客可见
- 登录后可删除自己的事项

**Kindle 墨水屏推送**
- `/kindle.png` 接口：对目标页面截图，转换为 758×1024 灰度 PNG
- 截图目标 URL 可在登录后台配置，无需修改代码
- Kindle 通过定时脚本拉取图片，实现每 30 分钟自动刷新日历

---

## 项目结构

```
.
├── app.py                  # Flask 主程序
├── calendar_lib.py         # 万年历核心库（阳历/农历/节气转换）
├── requirements.txt        # Python 依赖
├── kindle/
│   └── setup_kindle.sh     # Kindle 端一键配置脚本
└── templates/
    └── index.html          # 单页前端
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. 启动应用

```bash
python app.py
```

访问 `http://localhost:5008`，默认演示账号：

| 用户名 | 密码 |
|--------|------|
| demo | demo123 |

### 3. 配置 Kindle 截图地址

登录后，点击右上角**「设置」**按钮，填入截图目标 URL（默认为本机日历地址）。

Kindle 端访问 `http://<服务器IP>:5008/kindle.png` 即可获取当前日历截图。

---

## Kindle 端配置

> 需要已越狱的 Kindle（第六代已验证可用）

将 `kindle/setup_kindle.sh` 传到 Kindle 后，执行一次即可完成全部配置：

```bash
# 在 Kindle 终端执行
mkdir -p /mnt/us/STARTUP   # 首次需手动创建
bash setup_kindle.sh
```

脚本会自动完成：
- 安装更新脚本到 `/mnt/us/dashboard/update_kindle.sh`
- 写入 cron job，每 30 分钟自动拉取并显示图片
- 注册开机自启，重启后无需重新配置

**修改服务器地址：**

```bash
# 编辑 update_kindle.sh 中的 SERVER 变量
vi /mnt/us/dashboard/update_kindle.sh
# 修改这一行：
# SERVER="http://<你的服务器IP>:5008"
```

**手动测试：**

```bash
bash /mnt/us/dashboard/update_kindle.sh
```

**查看运行日志：**

```bash
tail -f /mnt/us/logs/kindle_update.log
```

日志示例（正常运行）：
```
[2026-04-07 11:06:21] === Starting Kindle update ===
[2026-04-07 11:06:21] Downloading image...
[2026-04-07 11:06:23] Downloaded successfully
[2026-04-07 11:06:23] Displaying image...
[2026-04-07 11:06:24] Image displayed
[2026-04-07 11:06:24] Disabling WiFi...
[2026-04-07 11:06:24] === Update completed ===
```

### Kindle 脚本说明

| 文件 | 路径 | 说明 |
|------|------|------|
| 安装脚本 | `kindle/setup_kindle.sh` | 一次性配置，运行后可删除 |
| 更新脚本 | `/mnt/us/dashboard/update_kindle.sh` | 每 30 分钟自动执行 |
| 开机脚本 | `/mnt/us/STARTUP/update_kindle_boot.sh` | 重启后自动恢复 cron |
| 运行日志 | `/mnt/us/logs/kindle_update.log` | 排查问题用 |

> **注意**：脚本针对 BusyBox v1.28.3 环境优化，使用 `wget -T` 替代 `timeout` 命令，避免 Kindle 原生 shell 兼容性问题。

---

## API 说明

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 日历主页面 |
| GET | `/kindle.png` | 截图并返回 Kindle 格式图片 |
| GET | `/api/calendar/:year/:month` | 获取月历数据（含农历） |
| GET | `/api/events/:year/:month` | 获取当前用户事项（需登录） |
| GET | `/api/events/public/:year/:month` | 获取公开事项 |
| POST | `/api/events` | 添加事项（需登录） |
| DELETE | `/api/events/:id` | 删除事项（需登录） |
| GET | `/api/config/screenshot-url` | 获取截图目标 URL（需登录） |
| POST | `/api/config/screenshot-url` | 修改截图目标 URL（需登录） |
| POST | `/login` | 登录 |
| POST | `/logout` | 登出 |
| GET | `/auth/status` | 获取登录状态 |

---

## 技术栈

- **后端**：Python / Flask / SQLAlchemy / Flask-Login
- **数据库**：SQLite
- **截图**：Playwright（Chromium）+ Pillow
- **前端**：原生 HTML/CSS/JS，无框架依赖
- **日历算法**：自实现万年历库，覆盖 1899–2100 年
- **Kindle 端**：BusyBox sh / crond / eips

---

## 注意事项

- 注册接口已关闭，新用户需直接操作数据库添加
- `SECRET_KEY` 默认值仅用于开发，生产环境请在 `app.py` 中替换为随机字符串
- SQLite 数据库文件 `calendar.db` 会在首次启动时自动创建
- Kindle 脚本中的服务器地址需根据实际部署修改
