#!/bin/bash

uv run scripts/train_umap.py --acoustic-features-path=../data/cairngorms/recording_acoustic_features_table.parquet --save-dir=../data/cairngorms/umap/
uv run scripts/train_umap.py --acoustic-features-path=../data/nature_sense/recording_acoustic_features_table.parquet --save-dir=../data/nature_sense/umap/
uv run scripts/train_umap.py --acoustic-features-path=../data/sounding_out/recording_acoustic_features_table.parquet --save-dir=../data/sounding_out/umap/
uv run scripts/train_umap.py --acoustic-features-path=../data/sounding_out_chorus/recording_acoustic_features_table.parquet --save-dir=../data/sounding_out_chorus/umap/
uv run scripts/train_umap.py --acoustic-features-path=../data/kilpisjarvi/recording_acoustic_features_table.parquet --save-dir=../data/kilpisjarvi/umap/
