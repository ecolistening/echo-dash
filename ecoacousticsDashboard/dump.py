
    file_site_weather = (
        pd.read_parquet(dataset.path / "files.parquet", columns=["file_id", "valid", "site_id", "file_name", "dddn", "timestamp"])
        .assign(nearest_hour=lambda df: data["timestamp"].dt.round("h"))
        .merge(
            (
                pd.read_parquet(dataset.path / "weather_table.parquet")
                .rename(columns=dict(timestamp="nearest_hour"))
            ),
            on=["site_id", "nearest_hour"],
            how="left")
        .drop("nearest_hour", axis=1)
        .query(f"{'valid == True and ' if valid_only else ''}{file_query} and {date_query} and {site_query} and {weather_query}")
        .drop([col for col in weather.columns if col not in ["site_id", "nearest_hour"]])
        .merge(dataset.locations, on="site_id", how="left")
    )
