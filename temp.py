import altair as alt
import pandas as pd
import streamlit as st

# Funções
def calculate_movement_counts(data, start, end, date_range, mean_of_transport=None, iso_type=None, in_out=None):
    start = pd.to_datetime(start)
    end = pd.to_datetime(end)
    filtered_data = data[(data['Date'] >= start) & (data['Date'] <= end)]
    if mean_of_transport:
        filtered_data = filtered_data[(filtered_data['Mean of Transport'] == mean_of_transport)]
    if iso_type:
        filtered_data = filtered_data[(filtered_data['ISO Type'] == iso_type)]
    if in_out:
        filtered_data = filtered_data[(filtered_data['In/Out'] == in_out)]
    display_data = pd.DataFrame(date_range, columns=['Date'])
    for i in range(len(display_data) - 1):
        date = display_data["Date"][i]

        next_date = display_data["Date"][i + 1]
        
        count = len(filtered_data[(filtered_data["Date"] >= date) & (filtered_data["Date"] < next_date)])
        count_in = len(filtered_data[(filtered_data["Date"] >= date) & (filtered_data["Date"] < next_date) & (filtered_data["In/Out"] == "In")])
        count_out = len(filtered_data[(filtered_data["Date"] >= date) & (filtered_data["Date"] < next_date) & (filtered_data["In/Out"] == "Out")])
        display_data.loc[i, "Count"] = int(count)
        display_data.loc[i, "In"] = int(count_in)
        display_data.loc[i, "Out"] = int(count_out)
        display_data.loc[i, "Period Start"] = date
        display_data.loc[i, "Period End"] = next_date
        
    return display_data, filtered_data

def round_out_start_end(start, end, granularidade):
    if granularidade == "Dia" or granularidade == "Hora":
        start = pd.to_datetime(start).replace(hour=0, minute=0, second=0)
        end = (pd.to_datetime(end) + pd.Timedelta(days=1)).replace(hour=0, minute=0, second=0)
    elif granularidade == "Semana":
        start = pd.to_datetime(start).to_period('W').start_time
        end = pd.to_datetime(end).to_period('W').end_time.replace(hour=0, minute=0, second=0)
    elif granularidade == "Mês":
        start = pd.to_datetime(start).replace(day=1, hour=0, minute=0, second=0)
        end = (pd.to_datetime(end) + pd.offsets.MonthBegin(1)).replace(hour=0, minute=0, second=0)
    return start, end

# Carregar os dados iniciais
data = pd.read_csv("data/container_throughput.csv", parse_dates=['Date'])

max_date = data['Date'].max().date()
min_date = data['Date'].min().date()

start = pd.to_datetime("2022/01/01").date()
end = pd.to_datetime("2023/01/01").date()

# Dashboard

st.title("Dashboard de Contentores")

col1, col2 = st.columns([2, 1])

with col1:
    granularidade = st.radio("Agrupar os dados por:", ["Hora", "Dia", "Semana", "Mês"], index=3)

gran_freq_dict = {"Hora": "h", "Dia": "D", "Semana": "W", "Mês": "MS"}
gran_format_dict = {"Hora": "%H:%M", "Dia": "%d/%m/%Y", "Semana": "%d/%m/%Y", "Mês": "%m/%Y"}

with col2:
    date_slider = st.checkbox("Usar slider para datas", True)

if date_slider:
    dates = st.slider(
        "Periodo a visualizar:", 
        min_value=min_date, 
        max_value=max_date, 
        value=(start, end), 
        format="DD/MM/YYYY"
    )
else:
    dates = st.date_input(
        "Periodo a visualizar:", 
        min_value=min_date, 
        max_value=max_date, 
        value=(start, end)
    )

# Validar se ambos os valores de data estão definidos
if isinstance(dates, tuple) and len(dates) == 2:
    start, end = dates
else:
    st.warning("Por favor, selecione um intervalo completo de datas.")
    st.stop()

start, end = round_out_start_end(start, end, granularidade)
    
brush = alt.selection_interval(encodings=['x'])

bar_select = alt.selection_point(fields=['Date', 'Period Start', 'Period End'], nearest=True, empty='none', on='click')

with st.expander("Filtros Adicionais", expanded=False):
    # Create two columns for radio buttons (side by side)
    col3, col4 = st.columns(2)
    with col3:
        mean_of_transport = st.radio("Mean of Transport", ["All"] + list(data["Mean of Transport"].unique()))
    with col4:
        in_out = st.radio("In/Out", ["All"] + list(data["In/Out"].unique()))

    # Create a searchable dropdown for ISO Type (multiselect with search)
    iso_type = st.selectbox("Select Container ISO Type", ["All"] + list(data["ISO Type"].unique()), help="Searchable")

    # Set None for "All" selections
    if mean_of_transport == "All":
        mean_of_transport = None
    if iso_type == "All":
        iso_type = None
    if in_out == "All":
        in_out = None

with st.expander("Movimentação de Contentores", expanded=False):
    date_range = pd.date_range(start=start, end=end, freq=gran_freq_dict[granularidade], inclusive='both')
    

    if date_range.shape[0] > 100:
        st.write(f"Muitos dados para exibir ({date_range.shape[0]} pontos). Por favor, selecione um intervalo menor ou uma granularidade mais alta.")
        st.stop()


    display_data, filtered_data = calculate_movement_counts(data, start, end, date_range, mean_of_transport, iso_type, in_out)

    if display_data.empty:
        st.write("Sem dados para o período selecionado.")
        st.stop()

    # Add option to toggle between Bar chart and Line chart
    chart_type = st.radio("Select Chart Type", ["Bar Chart", "Line Chart"])

    # Conditional "In/Out" discrimination for "All" filter
    discriminate_in_out = False
    if in_out == None:
        discriminate_in_out = st.checkbox("Discriminate In/Out", value=False)
    
    if granularidade == "Hora": periods = [alt.Tooltip('Period Start:T', title='Início do Período', format="%d/%m/%Y %H:%M"), 
                                           alt.Tooltip('Period End:T', title='Fim do Período', format="%d/%m/%Y %H:%M")]
    else: periods = [alt.Tooltip('Period Start:T', title='Início do Período'), alt.Tooltip('Period End:T', title='Fim do Período')]

    # Build the chart based on selection
    if chart_type == "Bar Chart":
        if discriminate_in_out:
            aux_display_data = []
            for i in range(len(display_data)):
                aux_display_data.append({"Date": display_data["Date"][i], "Count": display_data["In"][i], "In/Out": "In", "Period Start": display_data["Period Start"][i], "Period End": display_data["Period End"][i]})
                aux_display_data.append({"Date": display_data["Date"][i], "Count": display_data["Out"][i], "In/Out": "Out", "Period Start": display_data["Period Start"][i], "Period End": display_data["Period End"][i]})
            chart = alt.Chart(pd.DataFrame(aux_display_data)).mark_bar().encode(
                x=alt.X('Date:T', title='Data', axis=alt.Axis(format=gran_format_dict[granularidade])),
                y=alt.Y('Count:Q', title='Quantidade de Contentores'),
                xOffset="In/Out:N",
                color=alt.Color('In/Out:N', scale=alt.Scale(domain=['In', 'Out'], range=['green', 'red'])),
                tooltip=[
                    alt.Tooltip('Count:Q', title='Quantidade Total'),
                    alt.Tooltip('Date:T', title='Data')
                ] + periods
            ).add_params(bar_select).properties(title='Movimentação de Contentores')
        else:
            # Standard bar chart
            chart = alt.Chart(display_data).mark_bar().encode(
                x=alt.X('Date:T', title='Data', axis=alt.Axis(format=gran_format_dict[granularidade])),
                y=alt.Y('Count:Q', title='Quantidade de Contentores'),
                tooltip=[
                    alt.Tooltip('Count:Q', title='Quantidade Total'),
                    alt.Tooltip('In:Q', title='Entradas'),
                    alt.Tooltip('Out:Q', title='Saídas')
                ] + periods
            ).add_params(bar_select).properties(title='Movimentação de Contentores')
    else:
        # Line chart
        if discriminate_in_out:
            # Create two lines for In and Out using the "In" and "Out" columns
            chart = alt.Chart(display_data).mark_line(strokeDash=[5, 5]).encode(
                x=alt.X('Date:T', title='Data', axis=alt.Axis(format=gran_format_dict[granularidade])),
                y=alt.Y('value:Q', title='Quantidade de Contentores'),
                color=alt.Color('variable:N', scale=alt.Scale(domain=['In', 'Out'], range=['green', 'red'])),
                tooltip=[
                    alt.Tooltip('value:Q', title='Quantidade'),
                ] + periods
            ).transform_fold(
                ['In', 'Out'],
                as_=['variable', 'value']
            ).add_params(brush).properties(title='Movimentação de Contentores')
        else:
            # Standard line chart
            chart = alt.Chart(display_data).mark_line(strokeDash=[5, 5]).encode(
                x=alt.X('Date:T', title='Data', axis=alt.Axis(format=gran_format_dict[granularidade])),
                y=alt.Y('Count:Q', title='Quantidade de Contentores'),
                tooltip=[
                    alt.Tooltip('Count:Q', title='Quantidade Total'),
                    alt.Tooltip('In:Q', title='Entradas'),
                    alt.Tooltip('Out:Q', title='Saídas')
                ] + periods
            ).add_params(brush).properties(title='Movimentação de Contentores')

    # Display the chart
    selection_dict = st.altair_chart(chart, use_container_width=True, on_select="rerun")
    
    table_filtered_data = filtered_data.copy()
    
    new_filters = selection_dict["selection"]["param_1"]
    if type(new_filters) == dict:
        if "Date" in new_filters:
            new_start = pd.to_datetime(new_filters["Date"][0], unit="ms", origin="unix")
            new_end = pd.to_datetime(new_filters["Date"][1], unit="ms", origin="unix")
            new_start, new_end = round_out_start_end(new_start, new_end, granularidade)
            table_filtered_data = table_filtered_data[(table_filtered_data["Date"] >= new_start) & (table_filtered_data["Date"] <= new_end)]
    elif type(new_filters) == list:
        new_filters = new_filters[0]
        if "Period Start" in new_filters and "Period End" in new_filters:
            new_start = pd.to_datetime(new_filters["Period Start"], unit="ms", origin="unix")
            new_end = pd.to_datetime(new_filters["Period End"], unit="ms", origin="unix")
            new_start, new_end = round_out_start_end(new_start, new_end, granularidade)
            table_filtered_data = table_filtered_data[(table_filtered_data["Date"] >= new_start) & (table_filtered_data["Date"] <= new_end)]
    
    # Tabela
    st.write("**Detalhes da Movimentação:**")
    st.dataframe(table_filtered_data.reset_index(drop=True), height=400)