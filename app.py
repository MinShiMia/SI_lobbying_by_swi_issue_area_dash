'''
 # @ Create Time: 2025-02-14 11:22:20.564782
'''

import dash
from dash import Dash, dcc, html, dash_table, dcc
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import io
import os
import requests

# Include Bootstrap for better default styling
external_stylesheets = ["https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css"]

app = dash.Dash(__name__, title="lobbying-by-swi-issue-area-dash", external_stylesheets=external_stylesheets)

# Declare server for Heroku deployment. Needed for Procfile.
server = app.server


# Load data from GitHub with error handling
def load_csv_from_github(url):
    try:
        response = requests.get(url, timeout=10)  # Set a timeout to avoid hanging requests
        response.raise_for_status()  # Raise an error for HTTP errors (404, 403, etc.)
        csv_data = response.content.decode('utf-8')
        df = pd.read_csv(io.StringIO(csv_data))
        print(df.head())
        return df
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on failure


# URLs for CSV files
df_frequency_url = "https://raw.githubusercontent.com/MinShiMia/SI_lobbying_by_swi_issue_area_dash/main/data/lda_frequency_by_SWI_issue_area_over_time.csv"
df_expenses_url = "https://raw.githubusercontent.com/MinShiMia/SI_lobbying_by_swi_issue_area_dash/main/data/lda_quarterly_total_lobbying_expenses_by_SWI_issue_area_over_time.csv"

# Load the data
df_frequency = load_csv_from_github(df_frequency_url)
df_expenses = load_csv_from_github(df_expenses_url)

# Check if data loaded successfully
if df_frequency.empty:
    print("Failed to load df_frequency.")
if df_expenses.empty:
    print("Failed to load df_expenses.")

# Convert lobbying_expenses to millions for readability
df_expenses['lobbying_expenses'] = pd.to_numeric(df_expenses['lobbying_expenses'], errors='coerce').fillna(0)
df_expenses['lobbying_expenses'] = df_expenses['lobbying_expenses'] / 1_000_000  # Convert to millions

# Aggregate Data by issue_name
agg_frequency = (
    df_frequency.groupby('issue_name')['LDA_frequency']
    .sum()
    .reset_index(name='Total Frequency')
)

agg_expenses = (
    df_expenses.groupby('issue_name')['lobbying_expenses']
    .sum()
    .reset_index(name='Total Expenses ($ Million)')
)

# App Layout
app.layout = html.Div(
    [
    # # App Title
    # html.H1(
    #     "LDA Filing Frequency and Lobbying Expenses by SWI Issue Area Dashboard",
    #     style={
    #         'text-align': 'center',
    #         'font-size': '22px',
    #         'margin-bottom': '20px',  # Reduce space below the title
    #         'margin-top': '20px'       # Reduce space above the title
    #     }
    # ),
    # Filter Section at the Top
    html.Div([
        # Select Year filter
        html.Div([
            html.Label("Select Year:", style={'font-size': '14px', 'font-weight': 'bold'}),
            dcc.Dropdown(
                id='year-dropdown',
                options=[{'label': str(year), 'value': year} for year in sorted(df_frequency['Year'].unique())],
                multi=True,
                placeholder="Select Year(s)"
            ),
        ], style={'width': '24%', 'display': 'inline-block', 'padding-right': '10px'}),

        # Select Quarter filter
        html.Div([
            html.Label("Select Quarter:", style={'font-size': '14px', 'font-weight': 'bold'}),
            dcc.Dropdown(
                id='quarter-dropdown',
                options=[{'label': f"Q{q}", 'value': q} for q in sorted(df_frequency['Quarter'].unique())],
                multi=True,
                placeholder="Select Quarter(s)"
            ),
        ], style={'width': '24%', 'display': 'inline-block', 'padding-right': '10px'}),

        # Sort By Dropdown filter
            html.Div([
                html.Label("Sort By:", style={'font-size': '14px', 'font-weight': 'bold'}),
                dcc.Dropdown(
                    id='order-dropdown',
                    options=[
                        {'label': 'Total Frequency', 'value': 'Total Frequency'},
                        {'label': 'Total Expenses', 'value': 'Total Expenses'}
                    ],
                    value='Total Frequency',  # Default sorting
                    clearable=False
                ),
            ], style={'width': '24%', 'display': 'inline-block'}),

        # Select Top Issues Dropdown
        html.Div([
            html.Label("Top Issues to Show:", style={'font-size': '14px', 'font-weight': 'bold'}),
            dcc.Dropdown(
                id='top-issues-dropdown',
                options=[{'label': f"Top {i}", 'value': i} for i in range(10, 51, 10)],  # 10 to 100, step 10
                value=50,  # Default value
                clearable=False
            ),
        ], style={'width': '24%', 'display': 'inline-block'})
    ], style={
            'width': '100%',
            'display': 'flex',
            'justify-content': 'space-between',
            'align-items': 'center',
            'margin-bottom': '0px',
            'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif',
            'fontSize': '12px',
            'color': '#333'
        }),

    # Dual-Axis Bar Chart
    dcc.Graph(id='dual-axis-bar-chart', style={
        "height": "600px",
        "margin-top": "0px"  # Negative margin to bring it closer
    }),

    # Dynamic Title Section
    html.Div(id='dynamic-title', style={'font-size': '14px', 'font-weight': 'bold', 'margin-bottom': '0px'}),

    # Time Series Plots (Two Columns with Reduced Space and Y-axis Titles)
    html.Div([
        html.Div([
            dcc.Graph(id='frequency-time-series-plot', style={"height": "250px"}),
            html.Div("LDA Frequency Over Time",
                     style={'text-align': 'center', 'font-size': '14px', 'font-weight': 'bold'})
        ], style={'width': '48%', 'display': 'inline-block', 'padding-right': '10px'}),

        html.Div([
            dcc.Graph(id='expenses-time-series-plot', style={"height": "250px"}),
            html.Div("Lobbying Expenses (in Millions)",
                     style={'text-align': 'center', 'font-size': '14px', 'font-weight': 'bold'})
        ], style={'width': '48%', 'display': 'inline-block'})
    ], style={'width': '100%', 'display': 'flex', 'justify-content': 'space-between', 'margin-top': '0px'}),

])


# Callback for Dynamic Title
@app.callback(
    Output('dynamic-title', 'children'),
    [Input('dual-axis-bar-chart', 'clickData')]
)

def update_dynamic_title(clickData):
    # Default issue's external link
    default_swi_issue_id = f"https://app.legis1.com/issues/detail?id=67#summary"

    if not clickData:
        return html.Span([
            "LDA filing frequency and lobbying expenses for default issue: ",
            html.A("Affordable Care Act (ACA)", href=default_swi_issue_id, target="_blank",
                   style={'color': 'blue', 'text-decoration': 'underline'}),
            ". Click on another issue's bar to see its trend."
        ])

    # Extract selected issue name
    selected_issue = clickData['points'][0]['x']

    # Get the corresponding swi_issue_id
    selected_swi_issue_id = df_frequency.loc[df_frequency['issue_name'] == selected_issue, 'swi_issue_id'].values[0]

    # Construct the external URL
    external_url = f"https://app.legis1.com/issues/detail?id={selected_swi_issue_id}#summary"

    # Return the dynamic title with a clickable link
    return html.Span([
        f"LDA filing frequency and lobbying expenses for selected issue: ",
        html.A(f"{selected_issue}", href=external_url, target="_blank",
               style={'color': 'blue', 'text-decoration': 'underline'}),
        "."
    ])


# Callback for the Dual-Axis Bar Chart
@app.callback(
    Output('dual-axis-bar-chart', 'figure'),
    [Input('year-dropdown', 'value'),
     Input('quarter-dropdown', 'value'),
     Input('order-dropdown', 'value'),
     Input('top-issues-dropdown', 'value')]
)


def update_dual_axis_bar_chart(selected_years, selected_quarters, selected_order, top_n):
    # Filter the data based on the selected years and quarters
    filtered_frequency = df_frequency
    filtered_expenses = df_expenses

    if selected_years:
        filtered_frequency = filtered_frequency[filtered_frequency['Year'].isin(selected_years)]
        filtered_expenses = filtered_expenses[filtered_expenses['Year'].isin(selected_years)]

    if selected_quarters:
        filtered_frequency = filtered_frequency[filtered_frequency['Quarter'].isin(selected_quarters)]
        filtered_expenses = filtered_expenses[filtered_expenses['Quarter'].isin(selected_quarters)]

    # Aggregate data for bar chart
    agg_frequency = (
        filtered_frequency.groupby('issue_name')['LDA_frequency']
        .sum()
        .reset_index(name='Total Frequency')
    )

    agg_expenses = (
        filtered_expenses.groupby('issue_name')['lobbying_expenses']
        .sum()
        .reset_index(name='Total Expenses')
    )

    # Merge the frequency and expenses data for plotting
    merged_data = pd.merge(agg_frequency, agg_expenses, on='issue_name', how='outer').fillna(0)

    # Sort the data dynamically based on user selection
    if selected_order and top_n:
        # Ensure selected_order is valid
        if selected_order in ["Total Frequency", "Total Expenses"]:
            merged_data = merged_data.sort_values(by=selected_order, ascending=False)

        # Limit to top N firms after sorting
        merged_data = merged_data.head(top_n)

    # Create the bar chart with two traces (Frequency and Expenses)
    fig = go.Figure()

    # Add Total Frequency bars on the left y-axis
    fig.add_trace(go.Bar(
        x=merged_data['issue_name'],
        y=merged_data['Total Frequency'],
        name='Total Frequency',
        marker_color='rgb(46, 89, 142)',
        yaxis='y1',
        offsetgroup=0
    ))

    # Add Total Expenses bars on the right y-axis
    fig.add_trace(go.Bar(
        x=merged_data['issue_name'],
        y=merged_data['Total Expenses'],
        name='Total Expenses ($ Million)',
        marker_color='rgb(77, 0, 0)',
        yaxis='y2',
        offsetgroup=1
    ))

    # Layout for dual y-axis
    fig.update_layout(
        xaxis=dict(tickangle=-45, categoryorder='array', categoryarray=merged_data['issue_name']),
        yaxis=dict(title="Total Frequency"),
        yaxis2=dict(title="Total Expenses ($ Million)", overlaying='y', side='right'),
        barmode='group',
        bargap=0.2,
        height=600,
        legend=dict(x=0.01, y=1.15, orientation="h")
    )

    return fig


# Callback for Time Series Plots
@app.callback(
    [Output('frequency-time-series-plot', 'figure'),
     Output('expenses-time-series-plot', 'figure')],
    [Input('dual-axis-bar-chart', 'clickData')]
)


def update_time_series_plot(clickData):
    # Default to "Affordable Care Act (ACA)" if no bar is clicked
    selected_issue = "Affordable Care Act (ACA)"
    if clickData:
        selected_issue = clickData['points'][0]['x']

    # Frequency Time Series Data
    issue_data_freq = (
        df_frequency[df_frequency['issue_name'] == selected_issue]
        .groupby(['Year', 'Quarter'])['LDA_frequency']
        .sum()
        .reset_index()
    )
    issue_data_freq['Year_Quarter'] = issue_data_freq['Year'].astype(str) + " Q" + issue_data_freq['Quarter'].astype(str)

    # Frequency Time Series Plot
    freq_fig = go.Figure()
    freq_fig.add_trace(go.Scatter(
        x=issue_data_freq['Year_Quarter'],
        y=issue_data_freq['LDA_frequency'],
        mode='lines+markers',
        line=dict(color='teal'),
        name='Frequency'
    ))
    freq_fig.update_layout(
        title="",
        yaxis_title="Frequency",
        xaxis_title="Year-Quarter",
        height=250,
        margin=dict(t=00, b=00)
    )

    # Expenses Time Series Data
    issue_data_exp = (
        df_expenses[df_expenses['issue_name'] == selected_issue]
        .groupby(['Year', 'Quarter'])['lobbying_expenses']
        .sum()
        .reset_index()
    )
    issue_data_exp['Year_Quarter'] = issue_data_exp['Year'].astype(str) + " Q" + issue_data_exp['Quarter'].astype(str)

    # Expenses Time Series Plot
    exp_fig = go.Figure()
    exp_fig.add_trace(go.Scatter(
        x=issue_data_exp['Year_Quarter'],
        y=issue_data_exp['lobbying_expenses'],
        mode='lines+markers',
        line=dict(color='orange'),
        name='Lobbying Expenses'
    ))
    exp_fig.update_layout(
        title="",
        yaxis_title="Lobbying Expenses (Millions)",
        # yaxis_tickformat=",.2f",
        xaxis_title="Year-Quarter",
        height=250,
        margin=dict(t=00, b=00)
    )

    return freq_fig, exp_fig

# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run_server(debug=True, host="0.0.0.0", port=port)