from nicegui import ui, app
from datetime import datetime
import os, subprocess, json, smtplib, re
from collections import defaultdict
from email.message import EmailMessage

# --- CLOUD COMPATIBILITY CHECK ---
IS_MAC = False
try:
    from AppKit import NSWorkspace
    IS_MAC = True
except ImportError:
    NSWorkspace = None

DATA_FILE = "adults_usage.json"

# Global variable to track lock status for the API
lock_signal = {"should_lock": False}

# --- 📧 EMAIL CONFIG ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = "ScreenTimeAlert@gmail.com"
SENDER_PASSWORD = "PASSWORD2014"  # ⚠️ Use Gmail App Password in real use

# --- DATA LOGIC ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except:
            return []
    return []

def get_summary_data():
    data = load_data()
    summary = defaultdict(int)
    for entry in data:
        try:
            time_str = entry.get('time', '0m 0s')
            numbers = [int(n) for n in re.findall(r'\d+', time_str)]
            total_sec = 0

            if len(numbers) == 2:
                total_sec = (numbers[0] * 60) + numbers[1]
            elif len(numbers) == 1:
                total_sec = numbers[0] * 60 if 'm' in time_str else numbers[0]

            app_name = entry.get('app', 'Unknown')
            summary[app_name] += total_sec
        except:
            continue

    return [{"app": k, "total": f"{v // 60}m {v % 60}s"} for k, v in summary.items()]

# --- 🛰️ API ENDPOINT ---
@app.get('/check_lock')
def check_lock():
    return lock_signal

def send_alert_email(recipient, app_name, total_min):
    msg = EmailMessage()
    msg.set_content(f"Alert: {app_name} has been used for {total_min} minutes (15m over limit).")
    msg['Subject'] = f"Focus Alert: {app_name}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"Email error: {e}")

def lock_mac():
    global lock_signal
    if IS_MAC:
        subprocess.run([
            "/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession",
            "-suspend"
        ])
    else:
        lock_signal["should_lock"] = True
        print("Cloud: Lock Signal Activated")

# --- 🎨 UI PAGE ---
@ui.page('/')
def main():
    state = {
        'sec': 0,
        'min': 0,
        'limit': 1,
        'tracking': False,
        'username': "",
        'user_email': "",
        'current_app': "Idle",
        'notified_10': False,
        'notified_15': False,
    }

    # ✅ SAFE UI INIT (prevents crash)
    current_app_label = ui.label('Idle')
    timer_label = ui.label('00:00')

    def save_session_to_disk():
        if state['min'] == 0 and state['sec'] == 0:
            return

        data = load_data()
        data.append({
            'user': state['username'],
            'app': state['current_app'],
            'time': f"{state['min']}m {state['sec']}s",
            'date': datetime.now().strftime("%Y-%m-%d %H:%M")
        })

        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    def tick():
        global lock_signal

        if not state['tracking']:
            return

        if NSWorkspace:
            active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
            new_app = active_app.localizedName() if active_app else "Desktop"
        else:
            new_app = "Web-Tracker"

        if new_app != state['current_app'] and state['current_app'] != "Idle":
            save_session_to_disk()
            state['sec'] = 0
            state['min'] = 0
            state['notified_10'] = False
            state['notified_15'] = False
            lock_signal["should_lock"] = False

        state['current_app'] = new_app

        state['sec'] += 1
        if state['sec'] >= 60:
            state['min'] += 1
            state['sec'] = 0

        timer_label.set_text(f"{state['min']:02d}:{state['sec']:02d}")
        current_app_label.set_text(state['current_app'])

        over_limit = state['min'] - state['limit']

        if over_limit >= 10 and not state['notified_10']:
            ui.notify("⚠️ 10m Over Limit", type='warning')
            state['notified_10'] = True

        if over_limit >= 15 and not state['notified_15']:
            if state['user_email']:
                send_alert_email(state['user_email'], state['current_app'], state['min'])
            state['notified_15'] = True

        if over_limit >= 30:
            lock_mac()

    ui.timer(1.0, tick)
    ui.dark_mode().enable()

    ui.add_css("""
    .glass-card {
        border-radius: 24px;
        padding: 32px;
        margin: 0 auto;
        max-width: 500px;
        backdrop-filter: blur(12px);
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
    }
    """)

    with ui.column().classes('w-full items-center p-8'):
        with ui.tabs().classes('w-full text-blue-400') as tabs:
            ui.tab('Tracker', icon='timer')
            ui.tab('History', icon='analytics')
            ui.tab('Calculator', icon='calculate')  # ✅ FIXED NAME

        with ui.tab_panels(tabs, value='Tracker').classes('w-full bg-transparent'):

            # --- TRACKER ---
            with ui.tab_panel('Tracker'):
                with ui.card().classes('glass-card'):
                    ui.label('Screen Time Tracker').classes('text-3xl font-black text-center w-full text-blue-400')

                    with ui.column().classes('w-full gap-4').bind_visibility_from(state, 'tracking', backward=lambda x: not x):
                        ui.input('Name').bind_value(state, 'username').classes('w-full')
                        ui.input('Alert Email').bind_value(state, 'user_email').classes('w-full')
                        ui.number('Limit (min)', value=1).bind_value(state, 'limit').classes('w-full')

                    with ui.column().classes('items-center w-full py-4').bind_visibility_from(state, 'tracking'):
                        current_app_label
                        timer_label

                    def toggle():
                        global lock_signal

                        if not state['tracking']:
                            if not state['username'].strip() or "@" not in state['user_email']:
                                ui.notify('Setup Name and Email first!', type='negative')
                                return
                        else:
                            save_session_to_disk()
                            lock_signal["should_lock"] = False

                        state['tracking'] = not state['tracking']
                        state['sec'] = 0
                        state['min'] = 0

                    ui.button(on_click=toggle).bind_text_from(
                        state, 'tracking',
                        backward=lambda x: 'STOP' if x else 'START'
                    ).classes('w-full mt-4 py-4 rounded-xl font-bold bg-blue-600')

            # --- HISTORY ---
            with ui.tab_panel('History'):
                with ui.card().classes('glass-card w-full max-w-2xl'):
                    ui.label('Usage Summary').classes('text-xl font-bold text-blue-200 mb-2')

                    summary_grid = ui.aggrid({
                        'columnDefs': [
                            {'field': 'app', 'headerName': 'App'},
                            {'field': 'total', 'headerName': 'Total'}
                        ],
                        'rowData': get_summary_data(),
                        'theme': 'ag-theme-alpine-dark'
                    }).classes('h-40 mb-6')

                    ui.button(
                        'Refresh',
                        icon='sync',
                        on_click=lambda: summary_grid.update_row_data(get_summary_data())
                    ).classes('w-full mt-4').props('flat color=blue')

            # --- CALCULATOR ---
            with ui.tab_panel('Calculator'):
                with ui.card().classes('glass-card w-full max-w-2xl'):
                    ui.label('Calculator').classes('text-xl font-bold text-blue-200 mb-2')

                    with ui.row().classes('w-full gap-4'):
                        AGE = ui.number(label='Age:').classes('w-full')
                        AVG = ui.number(label='Avg Hours per day:').classes('w-full')

                    result_label = ui.label('Result: ').classes('text-lg font-bold mt-4')

                    def calculate():
                        try:
                            if AGE.value is None or AVG.value is None:
                                result_label.set_text("Please enter values")
                                return

                            result = (80 - AGE.value) * AVG.value * 365
                            result_label.set_text(f"Result: {result} hours and {result/24:.1f} days and {result/8760:.2f} years left until 80")
                        except Exception as e:
                            result_label.set_text(f"Error: {e}")

                    ui.button('Calculate', on_click=calculate).classes(
                        'w-full mt-4 py-3 rounded-xl font-bold bg-green-600'
                    )

# --- RUN ---
port = int(os.environ.get('PORT', 8082))
ui.run(host='0.0.0.0', port=port, title="Screen Time Tracker", reload=False)
