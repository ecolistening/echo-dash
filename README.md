# ecoacoustics-dashboard

## Installation

There are two ways of running the Ecoacoustics Dashboard.
For ease-of-use, the dashboard can be run in Docker.
However, for development, running the Dashboard in a conda environment (or virtual environment) is preferrable as Flask can auto-reload on changes to the codebase.


### Docker
The Docker image is not public yet, so please use Flask. You can build your own Docker image that you can use as well if you want.

### Flask (using Anaconda)
Checkout the respository (fork, if necessary, or close) and install required python libraries using `requirements.txt`.

Download the data (Sounding Out and Cairngorms), from https://github.com/ecolistening/ecoacoustics-dashboard/releases/download/v0.1/data.zip.
This should be unzipped in the directory above the dashboard repository, so that there is a directory structure like:
```
ecoacoustics-dashboard
|- data
|    |- Sounding Out
|    |- Cairngorms
|- ecoacousticsDashboard
     |- menu
     |- etc...
```

## Running Ecoacoustics Dashboard
Run the dashboard with the command `python ecoacousticsDashboard/app.py`. Flask should now start on `http://localhost:8050/` and you should be able to load the app.

# State of Development (August 2023)
There are a number of different plots (pages) in various states of development. The most advanced and recent is `overview > UMAP` and the structure of that page (the options menu at the top and the 'About' and 'Download' sections at the bottom) should be used as a basis for redeveloping the other pages.

There is a "common" menu on the lefthand side that is used for all (most) pages, and then page-specific options (with the general layout of the menu on the UMAP page) should go up top.

I have been tracking issues and to do's in Github Issues (https://github.com/ecolistening/ecoacoustics-dashboard/issues) and have marked some of the issues as good first issues (https://github.com/ecolistening/ecoacoustics-dashboard/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22), so feel free to start there.
