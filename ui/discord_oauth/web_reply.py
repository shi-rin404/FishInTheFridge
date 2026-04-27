import base64
from pathlib import Path

_ASSETS = Path(__file__).parent.parent.parent / "assets"


def _b64_img(name: str) -> str:
    try:
        return base64.b64encode((_ASSETS / name).read_bytes()).decode()
    except Exception:
        return ""


SUCCESS = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Authorization Successful</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    html, body {{
      height: 100%;
      background: #EAE4D5;
      font-family: "Segoe UI", Arial, sans-serif;
      color: #5a5549;
    }}
    .center {{
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      gap: 16px;
    }}
    img {{ width: 96px; height: 96px; }}
    h1 {{
      font-family: Georgia, "Times New Roman", serif;
      font-size: 28px;
      font-weight: normal;
    }}
    p {{ font-size: 14px; color: #9a9585; }}
  </style>
</head>
<body>
  <div class="center">
    <img src="data:image/png;base64,{_b64_img('tick.png')}" alt="">
    <h1>Authorization successful!</h1>
    <p>You can close this tab.</p>
  </div>
</body>
</html>"""

ERROR = lambda msg: f"<html><body><h2>Authorization failed: {msg}</h2></body></html>"
BAD_REQUEST = "<html><body><h2>Bad request</h2></body></html>"
