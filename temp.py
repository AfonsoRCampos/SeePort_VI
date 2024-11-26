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
        
    display_data.drop(display_data.tail(1).index,inplace=True)
    return display_data, filtered_data

def calculate_terminal_allocation(data, start, end, date_range, ib_mean_of_transport=None, ob_mean_of_transport=None, iso_type=None, container_action=None, full_container=None):
    start = pd.to_datetime(start)
    end = pd.to_datetime(end)
    
    filtered_data = data[(data['Outbound Date Time'] >= start) & (data['Inbound Date Time'] <= end)]
    if ob_mean_of_transport:
        filtered_data = filtered_data[(filtered_data['Outbound Mean of Transport'] == ob_mean_of_transport)]
    if iso_type:
        filtered_data = filtered_data[(filtered_data['ISO Type'] == iso_type)]
    if container_action:
        filtered_data = filtered_data[(filtered_data['Container Action'] == container_action)]
    if ib_mean_of_transport:
        filtered_data = filtered_data[(filtered_data['Inbound Mean of Transport'] == ib_mean_of_transport)]
    if full_container is not None:
        filtered_data = filtered_data[(filtered_data['Full Container?'] == full_container)]
    display_data = pd.DataFrame(date_range, columns=['Date'])
    for i in range(len(display_data) - 1):
        date = display_data["Date"][i]
        next_date = display_data["Date"][i + 1]
        
        display_data.loc[i, "Period Start"] = date
        display_data.loc[i, "Period End"] = next_date
        count = len(filtered_data[(filtered_data["Inbound Date Time"] < next_date) & (filtered_data["Outbound Date Time"] >= date)])
        display_data.loc[i, "Count"] = int(count)
        
    display_data.drop(display_data.tail(1).index,inplace=True)
    return display_data, filtered_data

def calculate_wait_times(data, start, end, nbins=10, nhide=0, ib_mean_of_transport=None, ob_mean_of_transport=None, iso_type=None, container_action=None, full_container=None):
    start = pd.to_datetime(start)
    end = pd.to_datetime(end)
    filtered_data = data[(data['Outbound Date Time'] >= start) & (data['Inbound Date Time'] <= end)]
    if ob_mean_of_transport:
        filtered_data = filtered_data[(filtered_data['Outbound Mean of Transport'] == ob_mean_of_transport)]
    if iso_type:
        filtered_data = filtered_data[(filtered_data['ISO Type'] == iso_type)]
    if container_action:
        filtered_data = filtered_data[(filtered_data['Container Action'] == container_action)]
    if ib_mean_of_transport:
        filtered_data = filtered_data[(filtered_data['Inbound Mean of Transport'] == ib_mean_of_transport)]
    if full_container is not None:
        filtered_data = filtered_data[(filtered_data['Full Container?'] == full_container)]
    filtered_data["Wait Time Days"] = filtered_data["Outbound Date Time"] - filtered_data["Inbound Date Time"]
    bins = pd.cut(filtered_data["Wait Time Days"], bins=nbins)
    values = []
    for line in bins.value_counts().items():
        min = line[0].left.days
        if min < 0: min  = 0
        max = line[0].right.days
        d = {"Min Wait Time": min, "Max Wait Time": max, "Count": line[1]}
        values.append(d)
    display_data = pd.DataFrame(values)
    display_data.sort_values(by="Min Wait Time", inplace=True)
    if nhide > 0:
        display_data = display_data.iloc[nhide:]
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
stays_data = pd.read_csv("data/container_stays.csv", parse_dates=['Inbound Date Time', 'Outbound Date Time'])

max_date = data['Date'].max().date()
min_date = data['Date'].min().date()

start = pd.to_datetime("2022/01/01").date()
end = pd.to_datetime("2022/12/31").date()

# Dashboard

st.set_page_config(layout="wide")

st.title("Dashboard de Contentores")


granularidade = st.segmented_control("Agrupar os dados por:", ["Hora", "Dia", "Semana", "Mês"], default = "Mês")

gran_freq_dict = {"Hora": "h", "Dia": "D", "Semana": "W", "Mês": "MS"}
gran_format_dict = {"Hora": "%H:%M", "Dia": "%d/%m/%Y", "Semana": "%d/%m/%Y", "Mês": "%m/%Y"}

date_slider = st.toggle("Usar slider para datas", True)

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

date_range = pd.date_range(start=start, end=end, freq=gran_freq_dict[granularidade], inclusive='both')
if date_range.shape[0] > 100:
        st.write(f"Muitos dados para exibir ({date_range.shape[0]} datas). Por favor, selecione um intervalo menor ou uma granularidade mais alta.")
        st.stop()

with st.expander("Movimentação de Contentores: análise da produtividade do terminal", expanded=False):
    brush = alt.selection_interval(encodings=['x'])

    bar_select = alt.selection_point(fields=['Date', 'Period Start', 'Period End'], nearest=True, empty='none', on='click')
        
    # Create two columns for radio buttons (side by side)
    col3, col4 = st.columns([0.15,0.6])
    with col3:
        mean_of_transport = st.segmented_control("Mean of Transport", ["All"] + list(data["Mean of Transport"].unique()), default="All")
    with col4:
        in_out = st.segmented_control("In/Out", ["All"] + list(data["In/Out"].unique()), default="All")

    # Create a searchable dropdown for ISO Type (multiselect with search)
    iso_type = st.selectbox("Select Container ISO Type", ["All"] + list(data["ISO Type"].unique()), help="Searchable")

    # Set None for "All" selections
    if mean_of_transport == "All":
        mean_of_transport = None
    if iso_type == "All":
        iso_type = None
    if in_out == "All":
        in_out = None


    display_data, filtered_data = calculate_movement_counts(data, start, end, date_range, mean_of_transport, iso_type, in_out)

    if display_data.empty:
        st.write("Sem dados para o período selecionado.")
        st.stop()
        
    col3, col4 = st.columns([0.15,0.6], vertical_alignment="bottom")

    # Add option to toggle between Bar chart and Line chart
    with col3: chart_type = st.segmented_control("Select Chart Type", ["Bar Chart", "Line Chart"], default="Bar Chart")

    # Conditional "In/Out" discrimination for "All" filter
    with col4:
        discriminate_in_out = False
        if in_out == None:
            discriminate_in_out = st.toggle("Discriminate In/Out", value=False)
    
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
                color=alt.condition(bar_select, 
                                    alt.value('orange'), 
                                    alt.Color('In/Out:N', scale=alt.Scale(domain=['In', 'Out'], range=['green', 'red']))),
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
                ] + periods,
                color=alt.condition(bar_select, alt.value('orange'), alt.value('steelblue'))
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
    
    new_start, new_end = start, end
    
    new_filters = selection_dict["selection"]["param_1"]
    if type(new_filters) == dict:
        if "Date" in new_filters:
            new_start = pd.to_datetime(new_filters["Date"][0], unit="ms", origin="unix")
            new_end = pd.to_datetime(new_filters["Date"][1], unit="ms", origin="unix")
            #new_start, new_end = round_out_start_end(new_start, new_end, granularidade)
            table_filtered_data = table_filtered_data[(table_filtered_data["Date"] >= new_start) & (table_filtered_data["Date"] <= new_end)]
    elif type(new_filters) == list:
        new_filters = new_filters[0]
        if "Period Start" in new_filters and "Period End" in new_filters:
            new_start = pd.to_datetime(new_filters["Period Start"], unit="ms", origin="unix")
            new_end = pd.to_datetime(new_filters["Period End"], unit="ms", origin="unix")
            #new_start, new_end = round_out_start_end(new_start, new_end, granularidade)
            table_filtered_data = table_filtered_data[(table_filtered_data["Date"] >= new_start) & (table_filtered_data["Date"] <= new_end)]
        if "In/Out" in new_filters:
            table_filtered_data = table_filtered_data[table_filtered_data["In/Out"] == new_filters["In/Out"]]
            
    # Tabela
    st.dataframe(table_filtered_data.reset_index(drop=True).astype('object'), height=400)
    
    st.write(f"Periodo selecionado: {new_start.strftime('%d/%m/%Y %H:%M:%S')} a {new_end.strftime('%d/%m/%Y %H:%M:%S')}")
    st.write(f"Movimentos totais: {len(table_filtered_data)} / Entradas: {len(table_filtered_data[table_filtered_data['In/Out'] == 'In'])} / Saídas: {len(table_filtered_data[table_filtered_data['In/Out'] == 'Out'])}")

        
    
    
with st.expander("Contentores no Terminal: análise da alocação do terminal", expanded=False):
    brush2 = alt.selection_interval(encodings=['x'])
        
    # Create two columns for radio buttons (side by side)
    col3, col4 = st.columns([0.25,0.6])
    with col3:
        ib_mean_of_transport = st.segmented_control("Inbound Mean of Transport", ["All"] + list(stays_data["Inbound Mean of Transport"].unique()), default="All", key="ib_mean_of_transport")
        ob_mean_of_transport = st.segmented_control("Outbound Mean of Transport", ["All"] + list(stays_data["Outbound Mean of Transport"].unique()), default="All", key="ob_mean_of_transport")
    with col4:
        container_action = st.segmented_control("Container Action", ["All"] + list(stays_data["Container Action"].unique()), default="All")
        full_cont = st.segmented_control("Full Container", ["All", "Yes", "No"], default="All", key="full_cont")

    # Create a searchable dropdown for ISO Type (multiselect with search)
    iso_type2 = st.selectbox("Select Container ISO Type", ["All"] + list(stays_data["ISO Type"].unique()), help="Searchable", key="iso_type2")

    if granularidade == "Hora": periods = [alt.Tooltip('Period Start:T', title='Início do Período', format="%d/%m/%Y %H:%M"), 
                                           alt.Tooltip('Period End:T', title='Fim do Período', format="%d/%m/%Y %H:%M")]
    else: periods = [alt.Tooltip('Period Start:T', title='Início do Período'), alt.Tooltip('Period End:T', title='Fim do Período')]
    
    # Set None for "All" selections
    if ib_mean_of_transport == "All":
        ib_mean_of_transport = None
    if ob_mean_of_transport == "All":
        ob_mean_of_transport = None
    if container_action == "All":
        container_action = None
    if iso_type2 == "All":
        iso_type2 = None
    if full_cont == "All":
        full_cont = None
    elif full_cont == "Yes":
        full_cont = True
    elif full_cont == "No":
        full_cont = False
        
    display_data2, filtered_data2 = calculate_terminal_allocation(stays_data, start, end, date_range, ib_mean_of_transport, ob_mean_of_transport, iso_type2, container_action, full_cont)

    if display_data2.empty:
        st.write("Sem dados para o período selecionado.")
    else:
        chart2 = alt.Chart(display_data2).mark_line().encode(
            x=alt.X('Date:T', title='Data', axis=alt.Axis(format=gran_format_dict[granularidade])),
            y=alt.Y('Count:Q', title='Quantidade de Contentores'),
            tooltip=[
                alt.Tooltip('Count:Q', title='Quantidade Total'),
            ] + periods
        ).add_params(brush2).properties(title='Alocação de Contentores no Terminal')
        
    selection_dict2 = st.altair_chart(chart2, use_container_width=True, on_select="rerun", key="chart2")
    
    table_filtered_data2 = filtered_data2.copy()
    
    new_start2, new_end2 = start, end
    
    new_filters2 = selection_dict2["selection"]["param_1"]
    if type(new_filters2) == dict:
        if "Date" in new_filters2:
            new_start2 = pd.to_datetime(new_filters2["Date"][0], unit="ms", origin="unix")
            new_end2 = pd.to_datetime(new_filters2["Date"][1], unit="ms", origin="unix")
            #new_start, new_end = round_out_start_end(new_start, new_end, granularidade)
            table_filtered_data2 = table_filtered_data2[(table_filtered_data2["Outbound Date Time"] >= new_start2) & (table_filtered_data2["Inbound Date Time"] <= new_end2)]
            
    st.dataframe(table_filtered_data2.reset_index(drop=True).astype('object'), height=400)
    
    st.write(f"Periodo selecionado: {new_start2.strftime('%d/%m/%Y %H:%M:%S')} a {new_end2.strftime('%d/%m/%Y %H:%M:%S')}")


with st.expander("Tempos de Estadias de Contentores: análise de casos anómalos", expanded=False):
    brush3 = alt.selection_interval(encodings=['x'])
    
    # Create two columns for radio buttons (side by side)
    col3, col4 = st.columns([0.25,0.6])
    with col3:
        ib_mean_of_transport2 = st.segmented_control("Inbound Mean of Transport", ["All"] + list(stays_data["Inbound Mean of Transport"].unique()), default="All", key="ib_mean_of_transport2")
        ob_mean_of_transport2 = st.segmented_control("Outbound Mean of Transport", ["All"] + list(stays_data["Outbound Mean of Transport"].unique()), default="All", key="ob_mean_of_transport2")
    with col4:
        container_action2 = st.segmented_control("Container Action", ["All"] + list(stays_data["Container Action"].unique()), default="All", key="container_action2")
        full_cont2 = st.segmented_control("Full Container", ["All", "Yes", "No"], default="All", key="full_cont2")

    # Create a searchable dropdown for ISO Type (multiselect with search)
    iso_type3 = st.selectbox("Select Container ISO Type", ["All"] + list(stays_data["ISO Type"].unique()), help="Searchable", key="iso_type3")
    
    # Set None for "All" selections
    if ib_mean_of_transport2 == "All":
        ib_mean_of_transport2 = None
    if ob_mean_of_transport2 == "All":
        ob_mean_of_transport2 = None
    if container_action2 == "All":
        container_action2 = None
    if iso_type3 == "All":
        iso_type3 = None
    if full_cont2 == "All":
        full_cont2 = None
    elif full_cont2 == "Yes":
        full_cont2 = True
    elif full_cont2 == "No":
        full_cont2 = False
    
    col3, col4, col5 = st.columns([0.35, 0.35, 1])
    
    with col3:
        nbins = st.slider("Número de Bins", min_value=5, max_value=100, value=10)
    with col4:
        nhide = st.slider("Esconder Primeiros N Bins", min_value=0, max_value=nbins-3, value=0)
    
    display_data3, filtered_data3 = calculate_wait_times(stays_data, start, end, nbins, nhide, ib_mean_of_transport2, ob_mean_of_transport2, iso_type3, container_action2, full_cont2)

    chart3 = alt.Chart(display_data3).mark_bar().encode(
        x=alt.X('Min Wait Time:Q', title='Wait Time (Days)', bin='binned'),
        x2='Max Wait Time:Q',  # Use x2 to specify the upper boundary of the bin
        y=alt.Y('Count:Q', title='Number of Containers'),
        tooltip=[
            alt.Tooltip('Min Wait Time:Q', title='Lower Wait Time (Days)'),
            alt.Tooltip('Max Wait Time:Q', title='Upper Wait Time (Days)'),
            alt.Tooltip('Count:Q', title='Count'),
        ]
    ).add_params(
        brush3
    ).properties(
        title='Tempos de Estadia dos Contentores',
        width=600,
        height=400
    )
    
    selection_dict3 = st.altair_chart(chart3, use_container_width=True, on_select="rerun")
    
    table_filtered_data3 = filtered_data3.copy()
    table_filtered_data3["Wait Time Days"] = table_filtered_data3["Wait Time Days"].dt.days
    
    min_days, max_days = min(display_data3["Min Wait Time"]), max(display_data3["Max Wait Time"])
    
    new_filters3 = selection_dict3["selection"]["param_1"]
    if "Min Wait Time" in new_filters3:
        new_filters3 = new_filters3["Min Wait Time"]
        min_days = round(new_filters3[0])
        max_days = round(new_filters3[1])
        table_filtered_data3 = table_filtered_data3[(table_filtered_data3["Wait Time Days"] >= min_days) & (table_filtered_data3["Wait Time Days"] <= max_days)]


    table_filtered_data3 = table_filtered_data3[["Stay Id", "Container Plate", "Wait Time Days", "Inbound Date Time", "Outbound Date Time", "Inbound Mean of Transport", "Outbound Mean of Transport", "Container Action", "ISO Type", "Full Container?"]]
    st.dataframe(table_filtered_data3.reset_index(drop=True).astype('object'), height=400)
    
    st.write(f"Minímo e máximo de dias de espera: {min_days} dias a {max_days} dias")
