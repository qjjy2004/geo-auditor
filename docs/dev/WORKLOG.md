# GEO Auditor — Work Log

Daily development notes. Process, decisions, debugging. Not user-facing (see CHANGELOG.md for that).

---

## 2026-06-23

### Landing page & articles restructure

- **Problem**: `/posts` page was Chinese-only, light theme. Clashed with English landing page.
- **Changes**:
  - Converted `/posts` template to English GitHub dark theme (matches landing page)
  - Created `/cn/` standalone Chinese landing page with article list (JS fetch from /posts)
  - Moved article display to Chinese page only; English landing page footer links to Articles
- **Footer**: `zhibi.xyz · Articles · 中文版 · qjjY2004@gmail.com` (mailto:)
- **Email**: qjjY2004@gmail.com, IMAP reachable from server, SMTP blocked. User forwards to QQ.
- **Bug fix**: `/posts/` trailing slash → 404. Changed to `/posts`.
- **Files**:
  - `/opt/deploy/homepage/index.html`
  - `/opt/deploy/cn/index.html` (new)
  - `/opt/pm/templates/articles_public_list.html`
- **Branch**: `docs/landing-cn-articles`
