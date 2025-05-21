import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import numpy as np

app = dash.Dash(__name__)
app.title = "Solar Panel Monitoring Dashboard"

# Helper function: شبیه‌سازی داده‌ها با پارامترهای ورودی
def simulate_data(irradiance, temp, dust, last_eff=0.18):
    # فرضیات:
    ideal_eff = 0.18
    loss_temp = 0.005 * (temp - 25)
    loss_dust = 0.2 * dust
    actual_eff = ideal_eff * (1 - loss_temp - loss_dust)
    actual_eff = np.clip(actual_eff, 0, ideal_eff)

    panel_area = 1.6
    power_output = irradiance * panel_area * actual_eff / 1000  # kW
    return actual_eff * 100, power_output  # درصد و توان

app.layout = html.Div([
    html.H1("☀️ Solar Panel Monitoring Dashboard", style={'textAlign': 'center'}),

    # نمودارها
    dcc.Graph(id='efficiency-graph'),
    dcc.Graph(id='power-graph'),

    # کنترل‌ها: اسلایدرهای دایره‌ای برای پارامترها
    html.Div([
        html.Div([
            html.Label("☀️ Irradiance (W/m²)"),
            dcc.Slider(id='irradiance-slider', min=0, max=1000, step=10, value=800,
                       marks={i: str(i) for i in range(0, 1100, 200)})
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '20px'}),

        html.Div([
            html.Label("🌡️ Ambient Temperature (°C)"),
            dcc.Slider(id='temp-slider', min=0, max=50, step=1, value=25,
                       marks={i: str(i) for i in range(0, 60, 10)})
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '20px'}),

        html.Div([
            html.Label("🌫️ Dust Factor (0-1)"),
            dcc.Slider(id='dust-slider', min=0, max=1, step=0.01, value=0.1,
                       marks={0: '0', 0.5: '0.5', 1: '1'})
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '20px'}),
    ], style={'textAlign': 'center'}),

    # دکمه استارت / استاپ
    html.Div([
        html.Button("Start Simulation", id='start-stop-button', n_clicks=0)
    ], style={'textAlign': 'center', 'padding': '20px'}),

    # هشدار
    html.Div(id='warning-message', style={'textAlign': 'center', 'color': 'red', 'fontWeight': 'bold'}),

    # Interval برای به‌روزرسانی زنده
    dcc.Interval(id='interval-component', interval=1000, n_intervals=0, disabled=True),

    # ذخیره داده‌ها در حافظه برای رسم نمودار زنده
    dcc.Store(id='data-store', data={'efficiency': [], 'power': [], 'time': []}),
])

@app.callback(
    Output('interval-component', 'disabled'),
    Output('start-stop-button', 'children'),
    Input('start-stop-button', 'n_clicks'),
    State('interval-component', 'disabled'),
)
def toggle_simulation(n_clicks, disabled):
    if n_clicks == 0:
        return True, "Start Simulation"
    else:
        # Toggle
        if disabled:
            return False, "Stop Simulation"
        else:
            return True, "Start Simulation"

@app.callback(
    Output('data-store', 'data'),
    Input('interval-component', 'n_intervals'),
    State('irradiance-slider', 'value'),
    State('temp-slider', 'value'),
    State('dust-slider', 'value'),
    State('data-store', 'data'),
    State('interval-component', 'disabled')
)
def update_data(n_intervals, irradiance, temp, dust, data, disabled):
    if disabled:
        # اگر غیرفعال است، داده‌ها تغییر نکنند
        return data

    # شبیه‌سازی مقدار جدید
    eff, power = simulate_data(irradiance, temp, dust)

    time_list = data['time']
    eff_list = data['efficiency']
    power_list = data['power']

    time_list.append(n_intervals)
    eff_list.append(eff)
    power_list.append(power)

    # محدود کردن تعداد داده‌ها برای نمایش (مثلاً 60)
    max_len = 60
    if len(time_list) > max_len:
        time_list = time_list[-max_len:]
        eff_list = eff_list[-max_len:]
        power_list = power_list[-max_len:]

    return {'time': time_list, 'efficiency': eff_list, 'power': power_list}

@app.callback(
    Output('efficiency-graph', 'figure'),
    Output('power-graph', 'figure'),
    Output('warning-message', 'children'),
    Input('data-store', 'data')
)
def update_graphs(data):
    time_list = data['time']
    eff_list = data['efficiency']
    power_list = data['power']

    # نمودار بهره‌وری
    eff_fig = go.Figure()
    eff_fig.add_trace(go.Scatter(x=time_list, y=eff_list, mode='lines+markers', name='Efficiency', line=dict(color='green')))
    eff_fig.update_layout(title='Efficiency (%) over Time', xaxis_title='Time (s)', yaxis_title='Efficiency (%)', yaxis=dict(range=[0, 20]))

    # نمودار توان
    power_fig = go.Figure()
    power_fig.add_trace(go.Scatter(x=time_list, y=power_list, mode='lines+markers', name='Power Output', line=dict(color='orange')))
    power_fig.update_layout(title='Power Output (kW) over Time', xaxis_title='Time (s)', yaxis_title='Power Output (kW)', yaxis=dict(range=[0, 1.5]))

    # هشدار
    warning_text = ""
    if eff_list and eff_list[-1] < 14:
        warning_text = "⚠️ Warning: Efficiency dropped below 14%!"

    return eff_fig, power_fig, warning_text

if __name__ == '__main__':
    app.run(debug=True)
