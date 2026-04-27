import os

# ── Secrets — load from environment variables in production ───────────────────
# Never hardcode these; set them as env vars on your server:
#   set MASTER_SECRET=<64 hex chars>
#   set DISCORD_CLIENT_ID=<your app id>
#   set DISCORD_CLIENT_SECRET=<your app secret>
#   set ADMIN_KEY=<a strong random string>

MASTER_SECRET         = bytes.fromhex(os.environ["MASTER_SECRET"])
DISCORD_CLIENT_ID     = os.environ["DISCORD_CLIENT_ID"]
DISCORD_CLIENT_SECRET = os.environ["DISCORD_CLIENT_SECRET"]
ADMIN_KEY             = os.environ["ADMIN_KEY"]
