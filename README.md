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
TOPDIR
|- data
|    |- Sounding Out
|    |- Cairngorms
|- ecoacoustics-dashboard
     |- menu
     |- etc...
```
