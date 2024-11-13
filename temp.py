import altair as alt
import pandas as pd
import streamlit as st

# Carregar os dados
data = pd.read_csv("data/container_throughput.csv", parse_dates=['Date'])

max_date = data['Date'].max().date()
min_date = data['Date'].min().date()

start = pd.to_datetime("2022/01/01").date()
end = pd.to_datetime("2023/01/01").date()

# Seletores
date_slider = st.toggle("Date Slider", True)
if date_slider:
    start, end = st.slider("Periodo a visualizar:", min_value=min_date, max_value=max_date, value=(pd.to_datetime("2022/01/01").date(), pd.to_datetime("2023/01/01").date()), format="DD/MM/YYYY")
else:
    start, end = st.date_input("Periodo a visualizar:", min_value=min_date, max_value=max_date, value=(pd.to_datetime("2022/01/01").date(), pd.to_datetime("2023/01/01").date()), format="DD/MM/YYYY")
granularidade = st.segmented_control("Granularidade:", ["Hora", "Dia", "Semana", "Mês"], default="Mês")
gran_freq_dict = {"Hora": "h", "Dia": "D", "Semana": "W", "Mês": "ME"}
gran_format_dict = {"Hora": "%H:%M", "Dia": "%d/%m/%Y", "Semana": "%d/%m/%Y", "Mês": "%m/%Y"}

def calculate_movement_counts(data, start, end, date_range):
    start = pd.to_datetime(start)
    end = pd.to_datetime(end)
    filtered_data = data[(data['Date'] >= start) & (data['Date'] <= end)]
    display_data = pd.DataFrame(date_range, columns=['Date'])
    for i in range(len(display_data)):
        date = display_data["Date"][i]
        if i == len(display_data) - 1:
            next_date = end
        else:
            next_date = display_data["Date"][i + 1]
        count = len(filtered_data[(filtered_data["Date"] >= date) & (filtered_data["Date"] < next_date)])
        count_in = len(filtered_data[(filtered_data["Date"] >= date) & (filtered_data["Date"] < next_date) & (filtered_data["In/Out"] == "In")])
        count_out = len(filtered_data[(filtered_data["Date"] >= date) & (filtered_data["Date"] < next_date) & (filtered_data["In/Out"] == "Out")])
        display_data.loc[i, "Count"] = int(count)
        display_data.loc[i, "In"] = int(count_in)
        display_data.loc[i, "Out"] = int(count_out)
    return display_data

date_range = pd.date_range(start=start, end=end, freq=gran_freq_dict[granularidade])

if date_range.shape[0] > 50:
    st.write(f"Muitos dados para exibir ({date_range.shape[0]} pontos). Por favor, selecione um intervalo menor ou uma granularidade mais alta.")
    
    st.stop()

display_data = calculate_movement_counts(data, start, end, date_range)

if display_data.empty:
    st.write("Sem dados para o período selecionado.")
    st.stop()
else: 
    chart = alt.Chart(display_data).mark_bar().encode(
        x=alt.X('Date:T', title='Data', axis=alt.Axis(format=gran_format_dict[granularidade])),
        y=alt.Y('Count:Q', title='Quantidade de Containers'),
    ).properties(title='Movimentação de Containers')
    st.altair_chart(chart, use_container_width=True)

