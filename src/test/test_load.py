import locust
import numpy as np

from config import root_dir
from datasets.dataset_loader import DatasetLoader
from utils.filter import setup_filter_store

dataset_loader = DatasetLoader(root_dir)
datasets = list(dataset_loader.datasets.values())

class DashUser(locust.HttpUser):
    wait_time = locust.between(1, 3)

    def on_start(self):
       # simulate a user randomly selecting a dataset
       self.dataset = datasets[np.random.randint(len(datasets))]
       self.filters = setup_filter_store(self.dataset.filters)

    @locust.task
    def load_homepage(self):
        self.client.get("/", name="home")

    @locust.task
    def filters_callback(self):
        self.client.post(
            "/_dash-update-component",
            json={
                "output":"filter-store.data",
                "outputs":{"id":"filter-store","property":"data"},
                "inputs":[{"id":"dataset-select","property":"value","value": self.dataset.dataset_name}],
                "changedPropIds":["dataset-select.value"],
                "parsedChangedPropsIds":["dataset-select.value"]
            },
            name=f"filters_callback/{self.dataset.dataset_name}"
        )

    @locust.task
    def recorders_map_graph_callback(self):
        self.client.post(
            "/_dash-update-component",
            json={
                "output":"map-graph.figure",
                "outputs":{"id":"map-graph","property":"figure"},
                "inputs":[
                    {"id":"dataset-select","property":"value","value": self.dataset.dataset_name},
                    {"id":"map-style-select","property":"value","value":"satellite"}
                ],
                "changedPropIds":["dataset-select.value"],
                "parsedChangedPropsIds":["dataset-select.value"]
            },
            name=f"recorders_map_graph_callback/{self.dataset.dataset_name}",
        )

    @locust.task
    def recorders_calendar_graph_callback(self):
        self.client.post(
            "/_dash-update-component",
            json={
                "output":"dates-graph.figure",
                "outputs":{"id":"dates-graph","property":"figure"},
                "inputs":[{"id":"filter-store","property":"data","value": self.filters}],
                "changedPropIds":[],"parsedChangedPropsIds":[],
                "state":[{"id":"dataset-select","property":"value","value": self.dataset.dataset_name}]
            },
            name=f"recorders_calendar_graph_callback/{self.dataset.dataset_name}"
        )

    @locust.task
    def recorders_schedule_graph_callback(self):
        self.client.post(
            "/_dash-update-component",
            json={
                "output":"times-graph.figure",
                "outputs":{"id":"times-graph","property":"figure"},
                "inputs":[
                    {"id":"filter-store","property":"data","value": self.filters},
                    {"id":"times-size-slider","property":"value","value":4},
                    {"id":"times-opacity-slider","property":"value","value":50},
                    {"id":"times-colour-select","property":"value","value":"valid"},
                    {"id":"times-symbol-select","property":"value","value":None},
                    {"id":"times-facet-row-select","property":"value","value":"sitelevel_1"},
                    {"id":"times-facet-column-select","property":"value","value":None}
                ],
                "changedPropIds":[],
                "parsedChangedPropsIds":[],
                "state":[{"id":"dataset-select","property":"value","value": self.dataset.dataset_name}]
            },
            name=f"recorders_schedule_graph_callback/{self.dataset.dataset_name}",
        )

    @locust.task
    def soundscape_distributions_graph_callback(self):
        self.client.post(
            "/_dash-update-component",
            json={
                "output":"distributions-graph.figure",
                "outputs":{"id":"distributions-graph","property":"figure"},
                "inputs":[
                    {"id":"filter-store","property":"data","value": self.filters},
                    {"id":"distributions-colour-select","property":"value","value":"sitelevel_1"},
                    {"id":"distributions-facet-row-select","property":"value","value":"sitelevel_1"},
                    {"id":"distributions-facet-column-select","property":"value","value":"dddn"},
                    {"id":"distributions-normalised-tickbox","property":"checked","value":False}
                ],
                "changedPropIds":[],
                "parsedChangedPropsIds":[],
                "state":[{"id":"dataset-select","property":"value","value": self.dataset.dataset_name}]
            },
            name=f"soundscape_distributions_graph_callback/{self.dataset.dataset_name}",
        )

    @locust.task
    def soundscape_diel_distributions_graph_callback(self):
        self.client.post(
            "/_dash-update-component",
            json={
                "output":"index-box-graph.figure",
                "outputs":{"id":"index-box-graph","property":"figure"},
                "inputs":[
                    {"id":"filter-store","property":"data","value": self.filters},
                    {"id":"index-box-plot-type-select","property":"value","value":"box"},
                    {"id":"index-box-time-aggregation","property":"value","value":"dddn"},
                    {"id":"index-box-outliers-tickbox","property":"checked","value":True},
                    {"id":"index-box-colour-select","property":"value","value":"sitelevel_1"},
                    {"id":"index-box-facet-row-select","property":"value","value":None},
                    {"id":"index-box-facet-column-select","property":"value","value":"year"}
                ],
                "changedPropIds":[],
                "parsedChangedPropsIds":[],
                "state":[{"id":"dataset-select","property":"value","value": self.dataset.dataset_name}]
            },
            name=f"soundscape_diel_distributions_graph_callback/{self.dataset.dataset_name}",
        )

    @locust.task
    def soundscape_diel_scatter_graph_callback(self):
        self.client.post(
            "/_dash-update-component",
            json={
                "output":"index-scatter-graph.figure",
                "outputs":{"id":"index-scatter-graph","property":"figure"},
                "inputs":[
                    {"id":"filter-store","property":"data","value": self.filters},
                    {"id":"index-scatter-size-slider","property":"value","value":6},
                    {"id":"index-scatter-opacity-slider","property":"value","value":33},
                    {"id":"index-scatter-x-axis-select","property":"value","value":"time"},
                    {"id":"index-scatter-colour-select","property":"value","value":"sitelevel_1"},
                    {"id":"index-scatter-symbol-select","property":"value","value":None},
                    {"id":"index-scatter-facet-row-select","property":"value","value":None},
                    {"id":"index-scatter-facet-column-select","property":"value","value":"month"}
                ],
                "changedPropIds":[],
                "parsedChangedPropsIds":[],
                "state":[{"id":"dataset-select","property":"value","value": self.dataset.dataset_name}]
            },
            name=f"soundscape_diel_scatter_graph_callback/{self.dataset.dataset_name}"
        )

    @locust.task
    def soundscape_seasonal_averages_graph_callback(self):
        self.client.post(
            "/_dash-update-component",
            json={
                "output":"index-averages-graph.figure",
                "outputs":{"id":"index-averages-graph","property":"figure"},
                "inputs":[
                    {"id":"filter-store","property":"data","value": self.filters},
                    {"id":"index-averages-time-aggregation","property":"value","value":"1W"},
                    {"id":"index-averages-colour-select","property":"value","value":"sitelevel_1"},
                    {"id":"index-averages-year-wrap-checkbox","property":"checked","value":False}
                ],
                "changedPropIds":[],
                "parsedChangedPropsIds":[],
                "state":[{"id":"dataset-select","property":"value","value": self.dataset.dataset_name}]
            },
            name=f"soundscape_seasonal_averages_graph_callback/{self.dataset.dataset_name}"
        )

    @locust.task
    def soundscape_umap_graph_callback(self):
        self.client.post(
            "/_dash-update-component",
            json={
                "output":"umap-graph.figure",
                "outputs":{"id":"umap-graph","property":"figure"},
                "inputs":[
                    {"id":"filter-store","property":"data","value": self.filters},
                    {"id":"umap-opacity-slider","property":"value","value":33},
                    {"id":"umap-size-slider","property":"value","value":6},
                    {"id":"umap-colour-select","property":"value","value":"sitelevel_1"},
                    {"id":"umap-symbol-select","property":"value","value":None},
                    {"id":"umap-facet-row-select","property":"value","value":None},
                    {"id":"umap-facet-column-select","property":"value","value":None}
                ],
                "changedPropIds":[],
                "parsedChangedPropsIds":[],
                "state":[{"id":"dataset-select","property":"value","value": self.dataset.dataset_name}]
            },
            name=f"soundscape_umap_graph_callback/{self.dataset.dataset_name}"
        )

    @locust.task
    def species_detection_matrix_graph_callback(self):
        self.client.post(
            "/_dash-update-component",
            json={
                "output":"species-community-graph.figure",
                "outputs":{"id":"species-community-graph","property":"figure"},
                "inputs":[
                    {"id":"filter-store","property":"data","value": self.filters},
                    {"id":"species-threshold-slider","property":"value","value":0.5},
                    {"id":"species-community-axis-select","property":"value","value":"sitelevel_1"},
                    {"id":"species-community-facet-column-select","property":"value","value":"dddn"},
                    {"id":"species-matrix-filter","property":"value","value":None},
                    [],
                    {"id":"species-list-tickbox","property":"checked","value":False}
                ],
                "changedPropIds":[],
                "parsedChangedPropsIds":[],
                "state":[{"id":"dataset-select","property":"value","value": self.dataset.dataset_name}]
            },
            name=f"species_detection_matrix_graph_callback/{self.dataset.dataset_name}"
        )

    @locust.task
    def species_diel_richness_graph_callback(self):
        self.client.post(
            "/_dash-update-component",
            json={
                "output":"species-richness-graph.figure",
                "outputs":{"id":"species-richness-graph","property":"figure"},
                "inputs":[
                    {"id":"filter-store","property":"data","value": self.filters},
                    {"id":"species-richness-plot-type-select","property":"value","value":"Scatter Polar"},
                    {"id":"species-richness-primary-axis-select","property":"value","value":"hour_continuous"},
                    {"id":"species-threshold-slider","property":"value","value":0.5},
                    {"id":"species-richness-color-select","property":"value","value":"sitelevel_1"},
                    {"id":"species-richness-facet-row-select","property":"value","value":None},
                    {"id":"species-richness-facet-column-select","property":"value","value":"year"},
                    {"id":"species-list-tickbox","property":"checked","value":False}
                ],
                "changedPropIds":[],
                "parsedChangedPropsIds":[],
                "state":[{"id":"dataset-select","property":"value","value": self.dataset.dataset_name}]
            },
            name=f"species_diel_richness_graph_callback/{self.dataset.dataset_name}"
        )

    @locust.task
    def weather_seasonal_averages_graph_callback(self):
        self.client.post(
            "/_dash-update-component",
            json={
                "output":"weather-hourly-graph.figure",
                "outputs":{"id":"weather-hourly-graph","property":"figure"},
                "inputs":[
                    {"id":"filter-store","property":"data","value": self.filters},
                    {"id":"weather-hourly-variable-select","property":"value","value":"temperature_2m"},
                    {"id":"weather-hourly-time-aggregation","property":"value","value":"1W"},
                    {"id":"weather-hourly-colour-select","property":"value","value":"sitelevel_1"},
                    {"id":"weather-hourly-facet-row-select","property":"value","value":"sitelevel_1"},
                    {"id":"weather-hourly-year-wrap-checkbox","property":"checked","value":False}
                ],
                "changedPropIds":[],
                "parsedChangedPropsIds":[],
                "state":[{"id":"dataset-select","property":"value","value": self.dataset.dataset_name}]
            },
            name=f"weather_seasonal_averages_graph_callback/{self.dataset.dataset_name}",
        )
