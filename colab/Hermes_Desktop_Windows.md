# 設定
```bash
hermes --version

hermes pm install chromium

hermes config set terminal.backend local

hermes config set browser.cloud_provider local

hermes config set browser.engine auto

hermes config set browser.headed true

hermes config set agent.tool_use_enforcement true

hermes config set browser.inactivity_timeout 600

set HERMES_GATEWAY_INSTALL_START_ON_LOGIN=0

hermes gateway restart

hermes gateway status
```