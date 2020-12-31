# =============================================================================
# IMPORT NECESSARY LIBRARIES
# =============================================================================

import pandas as pd
import geopandas as gpd
import numpy as np
from datetime import date
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from shapely.geometry import Point
import plotly.express as px
import json
import dash_table
import dash_bootstrap_components as dbc

 
# =============================================================================
# LOAD AND WRANGLE DATASETS
# =============================================================================

crime_main = pd.read_csv('Data/crime_main_geo.csv', low_memory=False)
crime_main['DAY_OF_WEEK'] = pd.Categorical(crime_main['DAY_OF_WEEK'], 
                                          categories=["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
                                          ordered=False)

crime_main['MONTH'] = pd.Categorical(crime_main['MONTH'], 
                                          categories=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                                          ordered=False)

crime_main['GEOID10'] = crime_main['GEOID10'].fillna(0.0).apply(np.int64).astype('category')
geometry = [Point(xy) for xy in zip(crime_main['X'], crime_main['Y'])]
crime_main_geo = gpd.GeoDataFrame(crime_main, crs={'init': 'epsg: 4326'}, geometry=geometry)

print(crime_main_geo.columns)

social = gpd.read_file("Data/3aeae140-8174-4d77-8c0e-de3ef0ce4b672020330-1-1rr22uq.veze.shp")
boston_polygon = social[['FID', 'GEOID10', 'Name', 'geometry']]

with open('Data/Boston_Social_Vulnerability.geojson') as f:
    boston_geojson = json.load(f)

boston_geo = []

for i in boston_geojson['features']:
    neighbourhood_name = i['properties']['Name']
    geo_id = i['properties']['GEOID10']
    geometry = i['geometry']
    boston_geo.append({
        'type': 'Feature',
        "GEOID10": geo_id,
        "properties": {
            "name": neighbourhood_name
        },
        'geometry': geometry,
    })

boston_geo_ok = {'type': 'FeatureCollection', 'features': boston_geo}

# Create a list of options for UCR categories
UCR_OPTIONS = crime_main_geo['UCR'].unique()
UCR_OPTIONS = [i for i in UCR_OPTIONS if i == i]

# Create a list of options for neighbourhoods in Boston
NEIGHBOURHOODS = list(crime_main_geo['Name'].unique())
NEIGHBOURHOODS = [i for i in NEIGHBOURHOODS if i == i]

# =============================================================================
# DEFINE APP LAYOUT
# =============================================================================
app = dash.Dash()

app.layout = html.Div([
    html.H1(
        children=" An Exploratory Analysis of Crimes in Boston"
        ),
    
    # Dropdown 1
    html.Div([
        html.Label("Select UCR Category"),
        dcc.Dropdown(
            id = 'ucr-category',
            options=[{'label': i, 'value': i} for i in UCR_OPTIONS],
            value = [UCR_OPTIONS[0]],
            multi=True
            )
        ], 
        style = {
            'width': '15%', 
            'display': 'inline-block', 
            'vertical-align': 'top', 
            # 'color': 'blue', 
            # 'border':'2px blue solid', 
            # 'borderRadius': 5,
            'padding':10
            }
        ),
    
        html.Div([""],
             style = {
                 'width': '5%',
                 'display': 'inline-block', 
                 'vertical-align': 'top', 
                  'borderRadius':5,
                  'padding':10
                 }
        ),
    
    # Dropdown 2
    html.Div([
        html.Label("Select Neighbourhood"),
        dcc.Dropdown(
            id='neighbourhood',
            options=[{'label': i, 'value': i} for i in NEIGHBOURHOODS],
            value=[NEIGHBOURHOODS[0], NEIGHBOURHOODS[1]],
            multi=True
            )       
        ], 
        style = {
            'width':'25%', 
            'display': 'inline-block', 
            'vertical-align': 'top', 
            'borderRadius':5,
            'padding':10
            }
        ),
    
        html.Div([""],
             style = {
                 'width': '5%',
                 'display': 'inline-block', 
                 'vertical-align': 'top', 
                  'padding':10
                 }
        ),
    
    # Dropdown 2
    html.Div([
        html.Label("Select Date Range"),
        dcc.DatePickerRange(
            id='date-range',
            start_date=date(2018, 1, 1),
            end_date=date(2018, 12, 31),
            display_format='DD-MM-YYYY'
            ),
        html.Div(
            id="output")           
        ], 
        style = {
            'width': '20%', 
            'display': 'inline-block', 
            'vertical-align': 'top', 
            'borderRadius': 5,
            'padding':10, 
            }
        ),
    
    html.Br(),
    html.Br(),
    dbc.Tabs(
        [
        dbc.Tab(
            label="Overview",
            children=[
                html.Div([
                    
                    html.Center(["AGGREGATION OF CRIME REPORTS"],
                                style={'font-weight': 'bold'}),
                    
                    html.Br(),
                    
                    "Select mode of aggregation",
                    
                    dcc.Dropdown(
                        id="agg-mode",
                        options=[
                            {'label': 'Year', 'value': 'YEAR'},
                            {'label': 'Month', 'value': 'MONTH'},
                            {'label': 'Day', 'value': 'DAY_OF_WEEK'},
                            {'label': 'Hour', 'value': 'TIME_HOUR'}
                            ],
                        value='YEAR'
                        ),
                    
                    dcc.Graph(id="bar-chart-agg-mode"),
                    
                    html.Hr(),
                    
                    html.Center(["TOP CRIME CATEGORIES"],
                                style={'font-weight': 'bold'}),
                    
                    html.Br(),
                    
                    "Select number of top crime categories to view",
                    
                    html.Br(),

                    dcc.Slider(
                        id="top-n",
                        min=3,
                        max=15,
                        marks={i: '{}'.format(i) for i in range(3, 16)},
                        value=5,
                        ),
                    
                    html.Br(),
                    
                    dcc.Graph(id="bar-chart-top-crimes")
                    ], 
                    style = {'width': '31%', 
                             'display': 'inline-block', 
                             'vertical-align': 'top', 
                             'padding':10
                             }
                    ),
                
                html.Div([""], 
                         style = {'width': '0.5%', 
                                  'display': 'inline-block', 
                                  'vertical-align': 'top', 
                                  'padding':10}
                         ),
                
                html.Div([
                    
                    html.Center(["PROPORTION OF CRIME CLASSES"],
                                style={'font-weight': 'bold'}),
                    
                    html.Br(),
                    
                    dcc.Graph(id="donut-crime-classes"),
                    
                    html.Hr(),
                    
                    html.Center(["PROPORTION OF SHOOTING INCIDENTS"],
                                style={'font-weight': 'bold'}),
                    
                    html.Br(),
                    
                    dcc.Graph(id="donut-shooting")
                    
                    ], 
                    style = {'width': '31%', 
                             'display': 'inline-block', 
                             'vertical-align': 'top', 
                             'padding':10}
                    ),
                
                html.Div([""], 
                         style = {'width': '0.5%', 
                                  'display': 'inline-block', 
                                  'vertical-align': 'top',  
                                  'padding':10}
                         ),
            
                html.Div([
                    
                    html.Center(["CHOROPLETH MAP OF CRIME COUNTS"],
                                style={'font-weight': 'bold'}),
                    
                    html.Center(["BY GEOGRAPHICAL REGIONS"],
                                style={'font-weight': 'bold'}),
                    html.Br(),
                    
                    dcc.Graph(id="choropleth")], 
                          style = {'width': '31%', 
                                   'display': 'inline-block', 
                                   'vertical-align': 'top', 
                                   'padding':10}
                          ),
                    ]),
        dbc.Tab(
            label="Analysis by Offence Type",
            children=[
                
                html.Div([
                    
                    html.Center(["GEOSPATIAL ANALYSIS"],
                                style={'font-weight': 'bold'}),
                    
                    html.Br(),
                    
                    "Select offense type",
                    
                    dcc.Dropdown(id='offense_types'),
                    
                    html.Br(),
                    
                    dcc.Graph(id="scatter_map"),
                    
                    ],
                    style = {'width': '30%', 
                             'display': 'inline-block', 
                             'vertical-align': 'top', 
                             'padding':10
                             }
                    ),

                html.Div([
                    
                    html.Center(["TIME-SERIES ANALYSIS"],
                                style={'font-weight': 'bold'}),
                    
                    html.Br(),
                    
                    dcc.Graph(id="time-series"),
                    
                    html.Hr(),
                    
                    html.Center(["HEATMAP ANALYSIS"],
                                style={'font-weight': 'bold'}),
                    
                    html.Br(),
                    
                    html.Div([dcc.Graph(id="heatmap-1")], 
                             style = {'width': '33%', 
                             'display': 'inline-block', 
                             'vertical-align': 'top', 
                             'padding':10
                             }
                             ), 
                    
                    html.Div([dcc.Graph(id="heatmap-2")], 
                             style = {'width': '65%', 
                             'display': 'inline-block', 
                             'vertical-align': 'top', 
                             'padding':10
                             }
                             ), 
                    ],
                    style = {'width': '67%', 
                             'display': 'inline-block', 
                             'vertical-align': 'top', 
                             'padding':10
                             }
                    ),
                ]
            ),
        
        dbc.Tab(
            dbc.Card(
                dbc.CardBody([
                    dash_table.DataTable(
                          id='datatable',
                            editable=False,
                            filter_action="native",
                              sort_action="native",
                              sort_mode="multi",
                              page_action="native",
                              page_current= 0,
                              page_size= 15,
                              style_cell={
                              'whiteSpace': 'normal'
                              },
                          )
                    ])
                
                ),
            label="Data"
            )
        ]
        )
    ]
    )

# =============================================================================
# DEFINE APP CALLBACKS
# =============================================================================

@app.callback(
    [
     Output('datatable', 'data'),
     Output('datatable', 'columns')
     ],
    [
     Input("ucr-category", "value"),
     Input("neighbourhood", "value"),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date')
     ]
    )

def update_datatable(selected_ucr, selected_neighbourhood, start_date, end_date):
    
    df = crime_main_geo[(crime_main_geo['UCR'].isin(selected_ucr)) & 
                        (crime_main_geo['Name'].isin(selected_neighbourhood))]
    df = df.rename(columns={'d1': 'DATE'})
    df = df[(df['DATE'] >= start_date) & (df['DATE'] <= end_date)]  
    df1 = df[['DATE', 'TIME', 'DAY_OF_WEEK', 'UCR', 'OFFENSE_CODE_GROUP', 'OFFENSE_DESCRIPTION', 'SHOOTING', 'Name', 'GEOID10', 'STREET']]
    df1.columns = ['Date', 'Time', 'Day', 'UCR Class', 'Offense Code Group', 'Offense Description', 'Shooting?', 'Neighbourhood', 'GEOID10', 'Incident Location']
    
    return df1.to_dict('records'), [{"name": i, "id": i, "deletable": False, "selectable": True} for i in df1.columns]

@app.callback(
    [
     Output("scatter_map", "figure"),
     Output("time-series", "figure"),
      Output("heatmap-1", "figure"),
      Output("heatmap-2", "figure")
      ],
    [
     Input("ucr-category", "value"),
     Input("neighbourhood", "value"), 
     Input("offense_types", "value"),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date')
     ]
    )

def update_graphs(selected_ucr, selected_neighbourhood, selected_offense_type, start_date, end_date):

    # Filter the selected UCR category & Neighbourhood & offense type
    df = crime_main_geo[(crime_main_geo['UCR'].isin(selected_ucr)) & 
                        (crime_main_geo['Name'].isin(selected_neighbourhood)) & 
                        (crime_main_geo['OFFENSE_CODE_GROUP'] == selected_offense_type)]
    df = df.rename(columns={'d1': 'DATE'})
    df = df[(df['DATE'] >= start_date) & (df['DATE'] <= end_date)]
    df['OFFENSE_DESCRIPTION'] = df['OFFENSE_DESCRIPTION'].astype('category')

    # GEOSPATIAL ANALYSIS
    fig_scatter_map = px.scatter_mapbox(df, lat="Y", lon="X", 
                                        # color=df["OFFENSE_DESCRIPTION"], 
                                        hover_name="Name", 
                                        hover_data=["DATE", "STREET", "OFFENSE_DESCRIPTION"],
                                        zoom=10, 
                                        height=850)
    fig_scatter_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, 
                                  mapbox_style="carto-positron", 
                                  height=800, 
                                  width=520)
    fig_scatter_map.update_layout(legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
    

    # TIME-SERIES ANALYSIS
    crime_ts_1 = df.groupby(by='DATE').count()[['OFFENSE_CODE_GROUP']].reset_index()
    crime_ts_1['MOV_AVG'] = crime_ts_1['OFFENSE_CODE_GROUP'].rolling(14).mean()

    fig_time_series = px.line(crime_ts_1, x='DATE', y='MOV_AVG', 
                          labels={"DATE": "", "MOV_AVG": "Number of Crime Reports"})
    fig_time_series.update_traces(line=dict(color="orange", width=3))
    fig_time_series.add_scatter(x=crime_ts_1['DATE'], y=crime_ts_1['OFFENSE_CODE_GROUP'], mode='lines', line=dict(color='blue', width=0.4))
    fig_time_series.update_layout(height=400, width=1170, showlegend=False, margin={"r":0,"t":0,"l":0,"b":0})

    # HEATMAP ANALYSIS
    crime_hm_1 = df.groupby(by=['DAY_OF_WEEK', 'MONTH'])['OFFENSE_CODE_GROUP'].count().to_frame('COUNT').reset_index()
    crime_hm_2 = crime_hm_1.pivot(index='MONTH', columns='DAY_OF_WEEK', values='COUNT')    
    fig_hm_1 = px.imshow(crime_hm_2.values.tolist(),
                    labels=dict(x="", y="Month", color="Number of\nCrime Reports"),
                    x=list(crime_hm_2.columns),
                    y=list(crime_hm_2.index),
                    color_continuous_scale='YlOrRd', 
                    origin='lower'
                    )
    fig_hm_1.update_layout(width=380, height=400, margin={"r":0,"t":0,"l":15,"b":0})
    fig_hm_1.update_coloraxes(showscale=False)

    crime_hm_4 = df.groupby(by=['DAY_OF_WEEK', 'TIME_HOUR'])['OFFENSE_CODE_GROUP'].count().to_frame('COUNT').reset_index()
    crime_hm_5 = crime_hm_4.pivot(index='TIME_HOUR', columns='DAY_OF_WEEK', values='COUNT')

    fig_hm_2 = go.Figure(data=go.Heatmap(
        z=crime_hm_5.values.tolist(),
        x=list(crime_hm_5.columns),
        y=list(crime_hm_5.index),
        hoverongaps = False, 
        colorscale = "YlGnBu", 
        connectgaps = True, 
        showscale = False))

    fig_hm_2.update_layout(yaxis_title="Hour of the Day")
    fig_hm_2.update_layout(
        height=340, 
        margin={"r":0,"t":0,"l":70,"b":0})

    return fig_scatter_map, fig_time_series, fig_hm_1, fig_hm_2
  
@app.callback(
    [
     Output("offense_types", "options"),
     Output("offense_types", "value")
     ],
    [
     Input("ucr-category", "value"),
     Input("neighbourhood", "value"),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date')
     ]
    )

def update_offense_types(selected_ucr, selected_neighbourhood, start_date, end_date):
        
    df = crime_main_geo[(crime_main_geo['UCR'].isin(selected_ucr)) & 
                        (crime_main_geo['Name'].isin(selected_neighbourhood))]
    df = df.rename(columns={'d1': 'DATE'})
    df = df[(df['DATE'] >= start_date) & (df['DATE'] <= end_date)]
    OFFENSE_TYPES = list(df['OFFENSE_CODE_GROUP'].unique())
    OFFENSE_TYPES = [i for i in OFFENSE_TYPES if i == i]
    
    return [{'label': i, 'value': i} for i in OFFENSE_TYPES], OFFENSE_TYPES[0]
    

@app.callback(
    [
     Output("bar-chart-agg-mode", "figure"),
     Output("bar-chart-top-crimes", "figure"),
     Output("donut-crime-classes", "figure"),
     Output("donut-shooting", "figure"),
     Output("choropleth", "figure")
     ],
    [
     Input("ucr-category", "value"),
     Input("neighbourhood", "value"),
     Input("agg-mode", "value"), 
     Input("top-n", "value"),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date')
     ]
    )

def update_agg_mode_bar_chart(selected_ucr, selected_neighbourhood, selected_agg_mode, selected_n, start_date, end_date):

    df = crime_main_geo[(crime_main_geo['UCR'].isin(selected_ucr)) & 
                        (crime_main_geo['Name'].isin(selected_neighbourhood))]
    df = df.rename(columns={'d1': 'DATE'})
    df = df[(df['DATE'] >= start_date) & (df['DATE'] <= end_date)]
    
    # AGGREGATION OF CRIME REPORTS
    df_grouped = df.groupby(by = selected_agg_mode).count()[["CODE"]].reset_index()
    df_grouped.columns = [selected_agg_mode, 'COUNT']
    
    fig_agg_mode = go.Figure(go.Bar(x = df_grouped[selected_agg_mode], 
                                    y = df_grouped['COUNT'], 
                                    marker_color='lightsalmon'))
    fig_agg_mode.update_xaxes(type='category')
    fig_agg_mode.update_layout(height=390, yaxis_title="Number of Crime Reports")

    
    # TOP CRIME CATEGORIES
    df_top = df.value_counts('OFFENSE_CODE_GROUP').to_frame().reset_index()
    df_top.columns = ['OFFENSE_CODE_GROUP', 'COUNT']
    df_top = df_top.head(selected_n)
    
    fig_top_crimes = go.Figure(go.Bar(x = df_top['COUNT'], 
                                      y = df_top['OFFENSE_CODE_GROUP'], 
                                      orientation = 'h',
                                      marker_color='indianred'))
    
    fig_top_crimes.update_layout(height=400, yaxis=dict(autorange="reversed"))
    
    # PROPORTION OF CRIME CLASSES
    colors_1 = ['#E0BBE4', '#957DAD', '#D291BC', '#FEC8D8']
    
    df_donut_crime_classes = df["CRIME_CLASS"].value_counts().to_frame().reset_index()
    df_donut_crime_classes.columns = ["CRIME_CLASS", 'COUNT']
    
    fig_donut_crime_class = go.Figure(data=[go.Pie(labels=df_donut_crime_classes["CRIME_CLASS"], 
                                                   values=df_donut_crime_classes['COUNT'],
                                                   hole=0.4)])
    fig_donut_crime_class.update_traces(marker=dict(colors=colors_1))
    fig_donut_crime_class.update_layout(legend=dict(orientation="v",
                                                 yanchor="bottom",
                                                 y=-0.3,
                                                 xanchor="right",
                                                 x=1))
    fig_donut_crime_class.update_layout(margin=dict(t=20, b=20, l=20, r=20))
    
    # PROPORTION OF SHOOTING INCIDENTS
    colors_2 = ["#85DE77", "#FF756D"]
    
    df_donut_shooting = df["SHOOTING"].value_counts().to_frame().reset_index()
    df_donut_shooting.columns = ["SHOOTING", 'COUNT']
    
    fig_donut_shooting = go.Figure(data=[go.Pie(labels=df_donut_shooting["SHOOTING"], 
                                                values=df_donut_shooting['COUNT'],
                                                hole=0.4)])
    fig_donut_shooting.update_traces(marker=dict(colors=colors_2))
    fig_donut_shooting.update_layout(legend=dict(orientation="v",
                                                 yanchor="bottom",
                                                 y=-0.07,
                                                 xanchor="right",
                                                 x=1))
    fig_donut_shooting.update_layout(margin=dict(t=0, b=0, l=0, r=0))
    
    # CHOROPLETH MAP OF CRIME COUNTS BY GEOGRAPHICAL REGIONS
    df_choro = df.groupby(by="GEOID10").count()[['OFFENSE_CODE_GROUP']].reset_index()
    df_choro['GEOID10'] = df_choro['GEOID10'].astype('str')
    df_choro = df_choro[df_choro['GEOID10'] != '0']
    df_choro_merged = pd.merge(boston_polygon, df_choro, how='left', on='GEOID10')
    
    fig_choro = go.Figure(go.Choroplethmapbox(geojson=boston_geo_ok, 
                                        locations=df_choro_merged['GEOID10'], 
                                        z=df_choro_merged['OFFENSE_CODE_GROUP'],
                                        colorscale="Blues", 
                                        featureidkey="GEOID10",
                                        marker_opacity=0.5, 
                                        marker_line_width=0.7))
    fig_choro.update_layout(mapbox_style="carto-positron",
                      mapbox_zoom=10, 
                      mapbox_center = {"lat": 42.33, "lon": -71.09})
    fig_choro.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=930)
    fig_choro.update_geos(fitbounds="locations", 
                    visible=True)
        
    return fig_agg_mode, fig_top_crimes, fig_donut_crime_class, fig_donut_shooting, fig_choro


if __name__ == '__main__':
    app.run_server(debug=True)
