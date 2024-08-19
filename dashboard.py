import pandas as pd
import lightningchart as lc
import time
import calendar
from datetime import datetime

lc.set_license("LICENSE_KEY")


file_path_japan_2001_2018 = 'datasets/Japan_2001-2018.csv'
file_path_japan_2000_2023 = 'datasets/Japan_2000_2023.csv'

data_japan_2001_2018 = pd.read_csv(file_path_japan_2001_2018)
data_japan_2000_2023 = pd.read_csv(file_path_japan_2000_2023)

# Convert the 'time' column to datetime format
data_japan_2001_2018['time'] = pd.to_datetime(data_japan_2001_2018['time'], utc=True)
data_japan_2000_2023['time'] = pd.to_datetime(data_japan_2000_2023['time'], utc=True)

# Filter and combine the datasets
data_japan_old_filtered = data_japan_2001_2018[data_japan_2001_2018['time'] < '2019-01-01']
data_japan_new_filtered = data_japan_2000_2023[data_japan_2000_2023['time'] >= '2000-01-01']
combined_data = pd.concat([data_japan_old_filtered, data_japan_new_filtered])

# Remove duplicates based on the 'time' column and create a copy to avoid SettingWithCopyWarning
cleaned_combined_data = combined_data.drop_duplicates(subset=['time']).copy()

regions = {
    'Hokkaidō': {'lat_min': 41, 'lat_max': 45.5, 'lon_min': 139, 'lon_max': 146},
    'Tōhoku': {'lat_min': 36.5, 'lat_max': 41.5, 'lon_min': 139, 'lon_max': 142},   
    'Kantō': {'lat_min': 34, 'lat_max': 37, 'lon_min': 138, 'lon_max': 141}, 
    'Chūbu': {'lat_min': 34, 'lat_max': 38.5, 'lon_min': 136, 'lon_max': 139},  
    'Kansai': {'lat_min': 33.5, 'lat_max': 36, 'lon_min': 134, 'lon_max': 137},    
    'Chūgoku': {'lat_min': 33.5, 'lat_max': 36.5, 'lon_min': 130.5, 'lon_max': 134},  
    'Shikoku': {'lat_min': 32.5, 'lat_max': 34.5, 'lon_min': 132, 'lon_max': 135},  
    'Kyūshū & Okinawa': {'lat_min': 23.5, 'lat_max': 34, 'lon_min': 123.5, 'lon_max': 132}, 
    'North East Shore': {'lat_min': 42, 'lat_max': 50, 'lon_min': 145.5, 'lon_max': 155.5},   
    'North West Shore': {'lat_min': 37.5, 'lat_max': 43, 'lon_min': 130, 'lon_max': 139},   
    'East Shore': {'lat_min': 35, 'lat_max': 42, 'lon_min': 141, 'lon_max': 150},   
    'South East Shore': {'lat_min': 20, 'lat_max': 35, 'lon_min': 135, 'lon_max': 150},   
}

def assign_region(row):
    for region, bounds in regions.items():
        if bounds['lat_min'] <= row['latitude'] <= bounds['lat_max'] and bounds['lon_min'] <= row['longitude'] <= bounds['lon_max']:
            return region
    return 'Other'

# Apply the function to assign regions
cleaned_combined_data['region'] = cleaned_combined_data.apply(assign_region, axis=1)

cleaned_combined_data['time'] = pd.to_datetime(cleaned_combined_data['time'])

# Extract the 'year' from the 'time' column
cleaned_combined_data['year'] = cleaned_combined_data['time'].dt.year


# Initialize a Dashboard with 2 columns and 4 rows
dashboard = lc.Dashboard(columns=2, rows=4, theme=lc.Themes.Dark)


# 1. 3D Chart
chart1 = dashboard.Chart3D(column_index=0, row_index=0, column_span=1, row_span=2)

x_values = cleaned_combined_data['longitude'].tolist()
y_values = cleaned_combined_data['latitude'].tolist()
z_values = cleaned_combined_data['depth'].tolist()
magnitude_values = cleaned_combined_data['mag'].tolist()
min_mag = min(magnitude_values)
max_mag = max(magnitude_values)
lookup_values = [(m - min_mag) / (max_mag - min_mag) for m in magnitude_values]
series1 = chart1.add_point_series(
    render_2d=False, individual_lookup_values_enabled=True, individual_point_size_enabled=True
)
series1.set_point_shape('sphere')
series1.set_palette_point_colors(
    steps=[
        {'value': 0.0, 'color': lc.Color(0, 0, 255)},
        {'value': 0.25, 'color': lc.Color(0, 255, 0)},
        {'value': 0.5, 'color': lc.Color(255, 255, 0)},
        {'value': 0.75, 'color': lc.Color(255, 165, 0)},
        {'value': 1.0, 'color': lc.Color(255, 0, 0)}
    ],
    look_up_property='value', interpolate=True, percentage_values=True
)
data = [
    {'x': x_values[i], 'y': y_values[i], 'z': z_values[i], 'size': 7 if magnitude_values[i] > 6.0 else 4, 'value': lookup_values[i]}
    for i in range(len(x_values))
]
series1.add(data)
chart1.set_title("3D Seismic Events (Longitude, Latitude, Depth)")
chart1.get_default_x_axis().set_title("Longitude")
chart1.get_default_y_axis().set_title("Latitude")
chart1.get_default_z_axis().set_title("Depth")


# 2. Monthly Frequency
chart2 = dashboard.BarChart(column_index=1, row_index=0, column_span=1, row_span=1)

cleaned_combined_data['month'] = cleaned_combined_data['time'].dt.month
monthly_event_counts = cleaned_combined_data.groupby('month').size()
data2 = [{'category': calendar.month_name[month], 'value': count} for month, count in monthly_event_counts.items()]
chart2.set_sorting("disabled")
chart2.set_data(data2)
chart2.set_title("Monthly Frequency of Seismic Events")


# 3. Monthly Average Magnitude
chart3 = dashboard.BarChart(column_index=1, row_index=1, column_span=1, row_span=1)

monthly_avg_magnitude = cleaned_combined_data.groupby('month')['mag'].mean()
data3 = [{'category': calendar.month_name[month], 'value': count} for month, count in monthly_avg_magnitude.items()]
chart3.set_sorting("disabled")
chart3.set_data(data3)
chart3.set_title("Average Magnitude of Each Month")


# 4. Depth vs. Magnitude
chart4 = dashboard.ChartXY(column_index=0, row_index=2, column_span=1, row_span=1)

x_values = cleaned_combined_data['depth'].tolist()
y_values = cleaned_combined_data['mag'].tolist()
lookup_values = cleaned_combined_data['mag'].tolist()
series4 = chart4.add_point_series(
    sizes=True, rotations=False, lookup_values=True
).append_samples(
    x_values=x_values,
    y_values=y_values,
    lookup_values=lookup_values
)
series4.set_individual_point_color_enabled()
series4.set_point_shape("triangle")
series4.set_palette_colors(
    steps=[
        {'value': min(lookup_values), 'color': lc.Color(255, 255, 0)},    # Yellow for lower magnitudes
        {'value': (min(lookup_values) + max(lookup_values)) / 2, 'color': lc.Color(0, 255, 255)},  # Cyan for mid-range magnitudes
        {'value': max(lookup_values), 'color': lc.Color(255, 0, 0)},      # Red for higher magnitudes
    ],
    look_up_property='value',
    percentage_values=False
)
chart4.set_title("Depth vs. Magnitude")
chart4.get_default_x_axis().set_title("Depth (km)")
chart4.get_default_y_axis().set_title("Magnitude")


# 5. Distribution by Region
chart5 = dashboard.BarChart(column_index=1, row_index=2, column_span=1, row_span=1)

region_event_counts = cleaned_combined_data.groupby('region').size()
data5 = [{'category': region, 'value': count} for region, count in region_event_counts.items()]
chart5.set_data(data5)
chart5.set_title("Distribution of Seismic Events by Region")


# 6. Seismic Events Over Time
chart6 = dashboard.ChartXY(column_index=0, row_index=3, column_span=1, row_span=1)

event_counts_per_year = cleaned_combined_data['year'].value_counts().sort_index()
xValues6 = [int(time.mktime(datetime(year, 1, 1).timetuple()) * 1000) for year in event_counts_per_year.index.tolist()]
yValues6 = event_counts_per_year.values.tolist()

chart6.get_default_x_axis().dispose()
x_axis6 = chart6.add_x_axis(axis_type='linear-highPrecision')
x_axis6.set_tick_strategy('DateTime')
x_axis6.set_scroll_strategy('progressive')
x_axis6.set_interval(start=min(xValues6), end=max(xValues6), stop_axis_after=False)
series6 = chart6.add_point_line_series().append_samples(x_values=xValues6, y_values=yValues6)
series6.set_point_color(lc.Color(255, 0, 0))
series6.set_line_thickness(2)
chart6.set_title("Seismic Events Over Time")
x_axis6.set_title("Year")
chart6.get_default_y_axis().set_title("Events")


# 7. Seismic Events Over Time by Region
chart7 = dashboard.ChartXY(column_index=1, row_index=3, column_span=1, row_span=1)

chart7.get_default_x_axis().dispose()
x_axis7 = chart7.add_x_axis(axis_type='linear-highPrecision')
x_axis7.set_tick_strategy('DateTime')
x_axis7.set_scroll_strategy('progressive')
year_region_event_counts = cleaned_combined_data.groupby(['year', 'region']).size().unstack(fill_value=0)

for region in year_region_event_counts.columns:
    x_values7 = [int(time.mktime(datetime(year, 1, 1).timetuple()) * 1000) for year in year_region_event_counts.index.tolist()]
    y_values7 = year_region_event_counts[region].tolist()
    series7 = chart7.add_line_series().append_samples(x_values=x_values7, y_values=y_values7)
    series7.set_line_thickness(2)
    series7.set_name(region)

min_x_value = min(x_values7)
max_x_value = max(x_values7)
x_axis7.set_interval(start=min_x_value, end=max_x_value, stop_axis_after=False)
chart7.set_title("Seismic Events Over Time by Region")
x_axis7.set_title("Year")
chart7.get_default_y_axis().set_title("Events")

dashboard.open()