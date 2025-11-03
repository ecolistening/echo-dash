import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from dash import callback, ctx, no_update, html, dcc
from dash import Output, Input, State
from typing import Any, Dict

from api import dispatch, FETCH_DATASET_CONFIG
from utils.content import get_content

def register_callbacks():
    @callback(
        Output("feature-descriptor-content", "children"),
        Input("feature-select", "value"),
    )
    def show_feature_description(
        current_feature: str,
    ) -> html.Div:
        if not current_feature:
            return no_update
        return get_content(f"feature/{current_feature}")

    @callback(
        Output("soundade-features-description", "children"),
        Input("dataset-select", "value"),
    )
    def show_soundade_feature_description(
        dataset_name: str,
    ) -> dcc.Markdown:
        if not dataset_name:
            return no_update
        config = dispatch(FETCH_DATASET_CONFIG, dataset_name=dataset_name)
        soundade_config = config["SoundADE"]
        text = (
            f"To compute acoustic features, the audio was resampled at {soundade_config['sample_rate']}Hz and "
            f"segmented into clips of duration {soundade_config['segment_duration']}s. "
            f"Each audio segment is windowed. For features derived from the raw waveform, this window is {soundade_config['frame_length']} samples. "
            f"For spectral features, a spectrogram is computed using an FFT size of {soundade_config['n_fft']} and a hop length of {soundade_config['hop_length']}. "
            f"Final values for each audio segment are the average of the metric across windows."
        )
        return dcc.Markdown(
            text,
            dangerously_allow_html=True,
            className="content-markdown",
        )
