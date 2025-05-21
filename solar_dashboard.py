import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import dash_daq as daq

# ----------------------
# Simulation Logic
# ----------------------
def simulate_data(irradiance, temp, dust):
    ideal_eff = 0.18
    loss_temp = 0.005 * (temp - 25)
    loss_dust = 0.2 * dust
    eff = ideal_eff * (1 - loss_temp - loss_dust)
    eff = np.clip(eff, 0, ideal_eff)
    power = irradiance * 1.6 * eff / 1000  # kW
    return eff * 100, power

# ----------------------
# Initialize Dash App
# ----------------------
app = dash.Dash(__name__)
app.title = "Solar Panel Digital Twin"

app.layout = html.Div(style={'backgroundColor': '#1e1e2f', 'color': 'white', 'padding': '20px'}, children=[
    html.H1("☀️ Solar Panel Digital Twin Dashboard", style={'textAlign': 'center'}),

    html.Div([
        html.Div([
            daq.Knob(id='irradiance-knob', label='Irradiance (W/m²)', value=800, min=0, max=1200, color="#FFD700"),
            daq.Knob(id='temp-knob', label='Ambient Temp (°C)', value=25, min=-10, max=60, color="#FF6347"),
            daq.Knob(id='dust-knob', label='Dust Level', value=0.1, min=0, max=1, size=80, color="#A9A9A9",
                     scale={'custom': {0: 'Low', 0.5: 'Med', 1: 'High'}})
        ], style={'display': 'flex', 'justifyContent': 'space-around'}),

        html.Br(),
        html.Div([
            html.Button('Start Simulation', id='start-btn', n_clicks=0, style={'marginRight': '10px'}),
            html.Button('Stop Simulation', id='stop-btn', n_clicks=0)
        ], style={'textAlign': 'center'}),

        dcc.Interval(id='interval', interval=1000, n_intervals=0, disabled=True)
    ]),

    html.Div([
        dcc.Graph(id='efficiency-graph'),
        dcc.Graph(id='power-graph')
    ]),

    html.Div(id='alert-div', style={'textAlign': 'center', 'fontSize': '20px', 'color': 'red', 'paddingTop': '10px'})
])

# ----------------------
# App State
# ----------------------
data_store = {
    "time": [],
    "efficiency": [],
    "power": []
}

# ----------------------
# Callbacks
# ----------------------
@app.callback(
    Output('interval', 'disabled'),
    [Input('start-btn', 'n_clicks'), Input('stop-btn', 'n_clicks')],
    [State('interval', 'disabled')]
)
def toggle_interval(start, stop, disabled):
    changed_id = dash.callback_context.triggered_id
    if changed_id == 'start-btn':
        return False
    elif changed_id == 'stop-btn':
        return True
    return disabled


@app.callback(
    [Output('efficiency-graph', 'figure'),
     Output('power-graph', 'figure'),
     Output('alert-div', 'children')],
    [Input('interval', 'n_intervals')],
    [State('irradiance-knob', 'value'),
     State('temp-knob', 'value'),
     State('dust-knob', 'value')]
)
def update_graph(n, irradiance, temp, dust):
    efficiency, power = simulate_data(irradiance, temp, dust)

    data_store['time'].append(n)
    data_store['efficiency'].append(efficiency)
    data_store['power'].append(power)

    eff_fig = go.Figure()
    eff_fig.add_trace(go.Scatter(x=data_store['time'], y=data_store['efficiency'],
                                 mode='lines+markers', name='Efficiency', line=dict(color='lime')))
    eff_fig.update_layout(paper_bgcolor='#1e1e2f', plot_bgcolor='#1e1e2f', font=dict(color='white'),
                          title='Efficiency (%)', xaxis_title='Time', yaxis_title='Efficiency')

    power_fig = go.Figure()
    power_fig.add_trace(go.Scatter(x=data_store['time'], y=data_store['power'],
                                   mode='lines+markers', name='Power', line=dict(color='orange')))
    power_fig.update_layout(paper_bgcolor='#1e1e2f', plot_bgcolor='#1e1e2f', font=dict(color='white'),
                            title='Power Output (kW)', xaxis_title='Time', yaxis_title='Power')

    alert = ''
    if efficiency < 14:
        alert = '⚠️ هشدار: بازده سیستم به زیر 14٪ رسیده!'

    return eff_fig, power_fig, alert

# ----------------------
# Run App
# ----------------------
if __name__ == '__main__':
    app.run(debug=True)
