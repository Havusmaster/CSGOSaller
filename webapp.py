from flask import Flask, render_template_string, request
from config import FLASK_HOST, FLASK_PORT, t
from database import get_user_pref

app = Flask(__name__)

TEMPLATE = """
<!DOCTYPE html>
<html lang="{{ lang }}">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{{ t(lang, 'web.welcome') }}</title>
    <style>
        body {{
            background-color: {{ 'black' if theme == 'dark' else 'white' }};
            color: {{ 'white' if theme == 'dark' else 'black' }};
            font-family: Arial, sans-serif;
            text-align: center;
            padding-top: 50px;
        }}
        button {{
            padding: 10px 20px;
            margin: 10px;
            border-radius: 8px;
            border: none;
            cursor: pointer;
        }}
    </style>
</head>
<body>
    <h1>{{ t(lang, 'web.welcome') }}</h1>
    <button>{{ t(lang, 'web.cart') }}</button>
    <button>{{ t(lang, 'web.buy') }}</button>
    <p>{{ t(lang, 'web.dark_mode') if theme == 'dark' else t(lang, 'web.light_mode') }}</p>
</body>
</html>
"""

@app.route("/shop")
def shop():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        lang, theme = "uz", "dark"
    else:
        user = get_user_pref(user_id)
        lang, theme = user["lang"], user["theme"]
    return render_template_string(TEMPLATE, t=t, lang=lang, theme=theme)

if __name__ == "__main__":
    app.run(host=FLASK_HOST, port=FLASK_PORT)
