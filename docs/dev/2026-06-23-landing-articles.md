# 2026-06-23 工作记录 — 落地页 & 文章系统整合

## 一、落地页 Footer 迭代（英文站 zhibi.xyz）

最终状态：
- 链接栏：Articles · Online Detector · GitHub · Changelog
- 版权行：zhibi.xyz · Articles · 中文版 · qjjY2004@gmail.com
- Articles 加下划线强调，邮箱 mailto: 点击唤起邮件客户端
- 中文版链接指向 /cn/

## 二、Gmail 配置

- 邮箱：qjjY2004@gmail.com
- IMAP 收信：正常（端口 993，服务器直连无 VPN）
- SMTP 发信：服务器被墙（465/587 均不可达），本地发信不受影响
- 设置 Gmail → QQ 自动转发，手机 QQ 直接收提醒
- 不需要 Hermes 监控

## 三、中文版 /cn/

- 独立暗色落地页 /opt/deploy/cn/index.html
- 部署至 /var/www/html/cn/index.html（chown www-data）
- 内容：GEO Auditor 中文介绍 + 14维6信号说明
- 底部：动态拉取 /posts 文章列表（JS fetch）
- 含 GitHub 开源、在线检测入口、返回 English 链接

## 四、/posts 文章页面改造

- 模板 /opt/pm/templates/articles_public_list.html
- 从中文浅色主题 → 英文 GitHub 暗色主题
- lang="zh-CN" → "en"，全部文案英文化
- 配色与英文站统一（#0d1117 底色，#161b22 卡片）
- 保留 Flask 路由不变，PM 重启后生效

## 五、架构分工

| 页面 | 语言 | 文章 | 说明 |
|------|------|------|------|
| / | 英文 | 不展示 | 纯英文落地页，Footer 有 Articles 链接 |
| /cn/ | 中文 | 底部动态加载 | 独立中文落地页 |
| /posts | 英文 | 列表页 | 暗色主题，作为 /cn/ 数据源 |

## 六、Bug 修复

- /posts/ 尾部斜杠 404 → 改为 /posts（nginx location 不带斜杠）

## 七、Git 状态

- 仓库：/home/ubuntu/geo-auditor
- 分支：main（origin/qjjy2004/geo-auditor）
- 本地无未提交变更
- 本次改动涉及文件：
  - /opt/deploy/homepage/index.html（英文落地页）
  - /opt/deploy/cn/index.html（中文版，新增）
  - /opt/pm/templates/articles_public_list.html（文章页模板）
