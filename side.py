import altair as alt
import pandas as pd
import streamlit as st

# Carregar os dados
data = pd.read_csv("data/container_throughput.csv")
data['Date'] = pd.to_datetime(data['Date'])  # Certificar que a coluna de data é datetime

# Criar seletores na barra lateral
st.sidebar.title("Configurações do Dashboard")
option = st.sidebar.selectbox("Escolha o tipo de visualização:", ["Diário", "Semanal", "Mensal", "Intervalo"])

st.title("Dashboard de Movimentação de Containers")

if option == "Diário":
    selected_date = st.sidebar.date_input("Escolha uma data:", value=pd.to_datetime('2021-11-01'))
    filtered_data = data[data['Date'].dt.date == selected_date]
    
    # Agrupar por hora e contar 'In' e 'Out'
    if not filtered_data.empty:
        hourly_data = (filtered_data.groupby([filtered_data['Date'].dt.floor('H'), 'In/Out'])
                       .size().reset_index(name='count'))
        # Criar gráfico empilhado
        chart = alt.Chart(hourly_data).mark_bar().encode(
            x=alt.X('Date:T', title='Hora', axis=alt.Axis(format='%H:%M')),
            y=alt.Y('count:Q', title='Quantidade de Containers'),
            color=alt.Color('In/Out:N', scale=alt.Scale(domain=['In', 'Out'], range=['green', 'red'])),
        ).properties(title='Movimentação de Containers por Hora')
        st.altair_chart(chart, use_container_width=True)
    else:
        st.write("Nenhum container encontrado para a data selecionada.")

elif option == "Semanal":
    selected_week = st.sidebar.date_input("Escolha uma data:", value=pd.to_datetime('2021-11-01'))
    week_start = selected_week
    week_end = week_start + pd.Timedelta(days=7)

    week_start = pd.to_datetime(week_start)
    week_end = pd.to_datetime(week_end)


    filtered_data = data[(data['Date'] >= week_start) & (data['Date'] <= week_end)]

    if not filtered_data.empty:
        weekly_data = (filtered_data.groupby([filtered_data['Date'].dt.date, 'In/Out'])
                       .size().reset_index(name='count'))
        chart = alt.Chart(weekly_data).mark_bar().encode(
            x=alt.X('Date:T', title='Data'),
            y=alt.Y('count:Q', title='Quantidade de Containers'),
            color=alt.Color('In/Out:N', scale=alt.Scale(domain=['In', 'Out'], range=['green', 'red']))
        ).properties(title='Movimentação de Containers por Dia')
        st.altair_chart(chart, use_container_width=True)
    else:
        st.write("Nenhum container encontrado para a semana selecionada.")

elif option == "Mensal":
    month_options = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                     'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    selected_month = st.sidebar.selectbox("Escolha o mês:", month_options, index=10)
    selected_year = st.sidebar.number_input("Escolha o ano:", value=2021, min_value=2021, max_value=2025)
    
    month_index = month_options.index(selected_month) + 1
    filtered_data = data[(data['Date'].dt.month == month_index) & (data['Date'].dt.year == selected_year)]

    if not filtered_data.empty:
        monthly_data = (filtered_data.groupby([filtered_data['Date'].dt.date, 'In/Out'])
                        .size().reset_index(name='count'))
        chart = alt.Chart(monthly_data).mark_bar().encode(
            x=alt.X('Date:T', title='Dia', axis=alt.Axis(format='%d')),
            y=alt.Y('count:Q', title='Quantidade de Containers'),
            color=alt.Color('In/Out:N', scale=alt.Scale(domain=['In', 'Out'], range=['green', 'red']))
        ).properties(title='Movimentação de Containers por Dia do Mês')
        st.altair_chart(chart, use_container_width=True)
    else:
        st.write("Nenhum container encontrado para o mês selecionado.")

elif option == "Intervalo":
    start_date = st.sidebar.date_input("Escolha a data de início:", value=pd.to_datetime('2021-11-01'))
    end_date = st.sidebar.date_input("Escolha a data de fim:", value=pd.to_datetime('2021-11-15'))

    # Converter start_date e end_date para datetime
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)


    filtered_data = data[(data['Date'] >= start_date) & (data['Date'] <= end_date)]

    if not filtered_data.empty:
        daily_data = (filtered_data.groupby([filtered_data['Date'].dt.date, 'In/Out'])
                      .size().reset_index(name='count'))

        max_points = 30
        total_days = (end_date - start_date).days
        if total_days >= max_points:
            date_range = pd.date_range(start=start_date, end=end_date, periods=max_points)
            sampled_data = pd.DataFrame(columns=daily_data.columns)
            for date in date_range.date:
                day_data = daily_data[daily_data['Date'] == date]
                if not day_data.empty:
                    sampled_data = pd.concat([sampled_data, day_data], ignore_index=True)
            daily_data = sampled_data

        line_chart = alt.Chart(daily_data).encode(
            x=alt.X('Date:T', title='Data'),
            y=alt.Y('count:Q', title='Quantidade de Containers'),
            color=alt.Color('In/Out:N', scale=alt.Scale(domain=['In', 'Out'], range=['green', 'red']))
        ).properties(title='Movimentação de Containers por Dia')

        line = line_chart.mark_line(strokeDash=[5, 5]).encode(opacity=alt.value(1))
        points = line_chart.mark_point(size=100).encode(opacity=alt.value(1))
        final_chart = line + points
        st.altair_chart(final_chart, use_container_width=True)
    else:
        st.write("Nenhum dado encontrado para o intervalo selecionado.")
