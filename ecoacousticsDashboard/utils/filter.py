def filter_sites_query(sites, selected_sites):
    sites = sites[sites['site'].isin([l.strip('/') for l in selected_sites])].reset_index()
    site_ids = ", ".join([f"'{site_id}'" for site_id in sites.site_id])
    return f"site_id in ({site_ids})"

def filter_files_query(file_ids):
    file_ids = ", ".join([f"'{file_id}'" for file_id in file_ids])
    return f"file_id not in ({file_ids}) and duration >= 60.0"

def filter_dates_query(date_range):
    return f"timestamp >= '{date_range[0]}' and timestamp <= '{date_range[1]}'"

def filter_weather_query(weather_variables):
    return " and ".join([
        f"(({variable_name} >= {variable_range[0]} and {variable_name} <= {variable_range[1]}) or {variable_name}.isnull())"
        for variable_name, variable_range in weather_variables
    ])

def filter_feature_query(feature_name_and_range):
    current_feature, current_feature_range = feature_name_and_range
    return f"`{current_feature}` >= {current_feature_range[0]} and `{current_feature}` <= {current_feature_range[1]}"

