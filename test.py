import pandas as pd
import altair as alt
import geopandas as gpd
import numpy as np

# -- Start of pre-processing steps --
file_path = 'data/OECD_betterLifeIndex.xlsx'
sheet_name = 'PyhtonReadable'
df = pd.read_excel(file_path, sheet_name=sheet_name)
df.columns = df.columns.str.strip()
df.replace('..', np.nan, inplace=True)

# Impute using mean values
for sel_1 in df.columns:
    if sel_1 not in ['Country', 'OCED']:
        df[sel_1] = pd.to_numeric(df[sel_1], errors='coerce')
        column_mean = df[sel_1].mean()
        column_mean = round(column_mean, 2)
        df[sel_1].fillna(column_mean, inplace=True)
# load geo json for map display view
world_geo = gpd.read_file('data/custom.geo.json')
# merge data from excel with geo_json data
merged_data = world_geo.merge(df, how='left', left_on='name_en', right_on='Country')
# -- End of pre-processing steps --

# -- Start of interactive component variable definition --
column_helper = pd.DataFrame({'variable': df.columns.values.tolist()})
# Create brush for selection within the world map
brush = alt.selection_point()
# Create dropdown boxes for category selection
sel_1 = alt.binding_select(options=column_helper['variable'].tolist(), name='Value1')
sel_2 = alt.binding_select(options=column_helper['variable'].tolist(), name='Value2')
p = alt.param(value='Homicide rate', bind=sel_1)
x = alt.param(value='Housing expenditure', bind=sel_2)
# Slider variables
range0 = alt.binding_range(min=-180, max=180, step=5, name='Rotate Longitude ')
range1 = alt.binding_range(min=-180, max=180, step=5, name='Rotate Latitude ')
range2 = alt.binding_range(min=100, max=500, step=5, name='Zoom')
rotate0 = alt.param(value=-10, bind=range0)
rotate1 = alt.param(value=-20, bind=range1)
Zoom = alt.param(value=100, bind=range2)
hover = alt.selection_point(on="mouseover", clear="mouseout")
# -- End of interactive component variable definition --

# -- Start of graph creation --
# Create bar chart
bar_chart = alt.Chart(merged_data).mark_bar().encode(
    # Allow the y column type to be changed by the dropdown box
    y=alt.Y(f'y:Q').title('Value'),
    # Sort the values by their Y value
    x=alt.X('Country:N').sort('-y'),
    color='Country:N'
).transform_calculate(
    # Extract the parameter name and use it as the y axis
    y=f'datum[{p.name}]'
).transform_filter(brush).add_params(brush,p).properties(
    height=400,
    width=600
)


# Create scatter plot to compare two drop down values
compare = alt.Chart(merged_data).mark_point().encode(
    y=alt.Y('y:Q').title('Value1'),
    x=alt.X('x:Q').title('Value2'),
    color='Country:N',
    shape='Country:N'
).transform_calculate(
    # Extract parameters and assign them to the values of the x and y columns
    y=f'datum[{p.name}]',
    x=f'datum[{x.name}]'
).add_params(p, x).transform_filter(brush).interactive()

# Create sphere to fill background of world visualization
sphere = alt.Chart(alt.sphere()).mark_geoshape(
    fill="aliceblue", stroke="black", strokeWidth=1.5
)


# Create the globe to represent to world data
world = alt.Chart(merged_data). mark_geoshape(
     stroke="black", strokeWidth=0.35
).encode(
    # I wanted to create an interactive tooltip but you cannot assign to tooltips in runtime as far as I can see
    tooltip=['Country:N'],
    stroke=alt.condition(brush, alt.value('red'), alt.value('gray')),
    color=alt.Color('color:Q')
).properties(
    width=400,
    height=400
).add_params(hover, rotate0, rotate1, Zoom, p, brush).transform_calculate(
    color=f'datum[{p.name}]'
)

# The idea for this visualization style for the world view came from the altair documentation
# https://altair-viz.github.io/user_guide/marks/geoshape.html
# Layer together the background and world data
final_map = alt.layer(sphere, world).project(
    type="orthographic",
    scale=Zoom, # When this is set, it removes  the default scale params which is what is moving the sphere off centre
    rotate=alt.expr(f"[{rotate0.name}, {rotate1.name}, 0]"), # Scale the spheres rotation based on the sliders defined above
    # This moves our sphere down so that it is not off screen
    translate=[200, 200]
)
Visualization = alt.hconcat(final_map, bar_chart, compare)
# -- End of graph creation --
# This is simply the output of the visualization HTML, most formatting css changes cannot be done using altair and
# Have therefore been done post export, see submitted output.html for finished page
Visualization.save('output.html')