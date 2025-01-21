import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import subprocess
from flask import Flask, jsonify
from threading import Thread

# Load data
@st.cache_data
def load_data():
    conn = st.connection("postgresql", type="sql")
    return conn.query('SELECT * FROM datanal;', ttl=0)

# Generate plot
def generate_plot(df, region, y_column, title, color):
    df_filtered = df[df['regija'] == region]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_filtered['Godina'], y=df_filtered[y_column], mode='lines+markers', name=y_column, line=dict(color=color), marker=dict(size=8)))
    fig.add_trace(go.Scatter(x=df_filtered['Godina'], y=df_filtered['Postotak Zaposlenosti'], mode='lines+markers', name='Postotak Zaposlenosti', line=dict(color='green'), marker=dict(size=8), yaxis='y2'))
    
    fig.update_layout(
        title=title,
        xaxis=dict(title='Godina'),
        yaxis=dict(title=y_column, titlefont=dict(color=color), tickfont=dict(color=color)),
        yaxis2=dict(title='Postotak Zaposlenosti', titlefont=dict(color='green'), tickfont=dict(color='green'), overlaying='y', side='right'),
        legend=dict(x=0.5, y=1, xanchor='center'),
    )
    return fig

# Plot with prediction
def plot_with_prediction(data, target_column, title, year_range):
    data = data.dropna(subset=[target_column])
    years = data['Godina'].values.reshape(-1, 1)
    values = data[target_column].values

    model = LinearRegression()
    model.fit(years, values)

    future_years = np.arange(year_range[0], year_range[1] + 1).reshape(-1, 1)
    predictions = model.predict(future_years)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data['Godina'], y=data[target_column], mode='lines+markers', name='Stvarni podaci'))
    fig.add_trace(go.Scatter(x=future_years.flatten(), y=predictions, mode='lines+markers', name='Predikcija', line=dict(dash='dot', color='red')))

    fig.update_layout(
        title=title,
        xaxis_title="Godina",
        yaxis_title=target_column,
        template="plotly_dark"
    )
    return fig

# Plot combined data
def plot_combined_data(df, region):
    df_filtered = df[df['regija'] == region]
    
    fig = go.Figure()
    
    for column, color in [('Broj Ucenika', 'blue'), ('Broj Studenata', 'orange'), ('Broj Diplomiranih Studenata', 'red')]:
        fig.add_trace(go.Scatter(x=df_filtered['Godina'], y=df_filtered[column], mode='lines+markers', name=column, line=dict(color=color), marker=dict(size=8)))
    
    fig.add_trace(go.Scatter(x=df_filtered['Godina'], y=df_filtered['Postotak Zaposlenosti'], mode='lines+markers', name='Postotak Zaposlenosti', line=dict(color='green'), marker=dict(size=8), yaxis='y2'))
    
    fig.update_layout(
        title=f'Kombinirani podaci za regiju: {region}',
        xaxis=dict(title='Godina'),
        yaxis=dict(title='Broj Svih Studenata', titlefont=dict(color='blue')),
        yaxis2=dict(title='Postotak Zaposlenosti', titlefont=dict(color='green'), tickfont=dict(color='green'), overlaying='y', side='right'),
        legend=dict(x=0.5, y=1, xanchor='center'),
    )
    
    return fig

# Display tab content
def display_tab_content(data, region, y_column, title, color, key):
    fig = generate_plot(data, region, y_column, title, color)
    st.plotly_chart(fig, use_container_width=True)

    region_data = data[data['regija'] == region]
    max_year = int(region_data['Godina'].max())
    selected_years = st.slider(
        "Odaberite raspon godina za predikciju:",
        min_value=max_year + 1,
        max_value=max_year + 20,
        value=(max_year + 1, max_year + 5),
        key=key
    )

    fig = plot_with_prediction(region_data, y_column, f"Predikcija {y_column.lower()}", selected_years)
    st.plotly_chart(fig, use_container_width=True)

# Create Flask API
def create_api(df):
    app = Flask(__name__)

    @app.route('/data', methods=['GET'])
    def get_data():
        return jsonify(df.to_dict(orient="records"))

    def run_flask():
        app.run(host="127.0.0.1", port=5000)

    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()

    return 'http://127.0.0.1:5000/data'

#####
result = subprocess.run(['python', 'main.py'], capture_output=True, text=True)
st.success(result.stdout, icon="✅")

st.title("Analiza trendova obrazovanja i zapošljavanja u Hrvatskoj")

df = load_data()

filtered_data = {
    'srednje': df[['regija', 'Godina', 'Broj Ucenika', 'Postotak Zaposlenosti']],
    'fakulteti': df[['regija', 'Godina', 'Broj Studenata', 'Postotak Zaposlenosti']],
    'diplomirani': df[['regija', 'Godina', 'Broj Diplomiranih Studenata', 'Postotak Zaposlenosti']]
}

region_selected = st.selectbox("Odaberi regiju", df['regija'].unique())

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Srednje Škole", "Fakulteti", "Diplomirani Studenti", "Sve Osobe", "Podaci"])

with tab1:
    display_tab_content(filtered_data['srednje'], region_selected, 'Broj Ucenika', 'Trendovi za Srednje Škole', 'blue', 1)

with tab2:
    display_tab_content(filtered_data['fakulteti'], region_selected, 'Broj Studenata', 'Trendovi za Fakultete', 'orange', 2)

with tab3:
    display_tab_content(filtered_data['diplomirani'], region_selected, 'Broj Diplomiranih Studenata', 'Trendovi za Diplomirane', 'purple', 3)

with tab4:
    fig = plot_combined_data(df, region_selected)
    st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.dataframe(df)

df = df.fillna("null")
api_url = create_api(df)
st.link_button("REST API", api_url)
