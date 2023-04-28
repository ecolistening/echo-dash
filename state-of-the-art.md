# State of the Art
## Ecoacoustics Dashboards

Existing dashboards include:
* Arbimon (https://arbimon.rfcx.org/)
  * Example Dataset: https://bio.rfcx.org/rfcx-guardians-madre-de-dios-peru
* BirdWeather (https://app.birdweather.com/)
* The Sound of Water (https://flow-mer.org.au/napnap/)
* Ecosounds (https://www.ecosounds.org/)
* BTO (https://app.bto.org/acoustic-pipeline/public/login.jsp)

Other (non-acoustic) dashboards include:
* Restor.eco (https://restor.eco/)

### Arbimon
Arbimon is probably closest to what we are looking to do, but it is more focused on bioacoustics tasks than ecoacoustics.
Its main job is to perform species detection, but it does have some tools for computing acoustic indices as well.
It generally does not engage in soundscape-level analysis.

Features:
* data labelling for training/tweaking classifiers
* acoustic playback
* location mapping
* visualisation of sites, recordings, detections
* run and train classifiers
* visualise acoustic indices over time
* monitor jobs
* Insights (beta)
    * detected species, status
    * species drill-downs

### BirdWeather
BirdWeather is BirdNet running on open audio streams.
They are developing a physical device (ostensibly) to perform detections in the field.

Web dashboard has two main interfaces: map and table.
The map interface shows species-level data including detection heatmaps, a plot of detections in the past 24 hours, and links to recordings, and wikipedia pages for relevant species.
The table interface shows individual detections of species along with timestamp, coordinate, station, and confidence data.

### The Sound of Water
The sound of water is not a dashboard per se, but a visualisation for a single project.
However, it is relevant as an excellent example of visualisation of long-term data.

It displays interactive false colour (this is specified at the bottom) spectrograms (5 minutes every hour) for several days worth of recordings.
These spectograms are clickable and provide interactive playback for the files.

Alongside this, it shows rising water levels and correlates the impact of those water level rises with the recorded audio.

### Ecosounds
Ecosounds (and the ecoacoustics workbench) seem like a lighter, but open-source version of Arbimon.
The web interface seems to host project with (hand? machine?) annotated audio files, labelled with instances of species calls, seemingly done in spectral space (as they are labelled with bounding boxes on a spectrogram).

One can create projects, submit audio for analysis, and then view results including recording timelines and (manually input) site notes.

### BTO
BTO detects bats, but is expanding to include some mammals, crickets, and moths.
It is a pipeline exclusively for species identification (an online version of BirdNet).
Portals to show processing progress.
No other visualisation apparent.

### Restor.eco
Collection of ecosysteem restoration projects and sites.
Provides high-level data on sites and changes over time, reporting on:
* Biodiversity
* Carbon
* Water
* Environment
* Land Cover

It is unclear what the data sources are, though much appears to come from satellite imaging and global models of plants/birds/etc.

## Python Dashboard Frameworks

* **Dash (Plotly)**
* Streamlit
* Shiny
* Voila

### Dash

# Gaps
* Comparisons over:
    * space (two or more locations/sites)
    * time (same location, two or more periods)
* Visualisation with astrograms and phase portraits
* Capturing/visualising complexity
