[![DOI](https://zenodo.org/badge/627429542.svg)](https://doi.org/10.5281/zenodo.18770082)

# Ecoacoustics Dashboard

## Documentation

* [Aggregating Indices](docs/aggregating-indices.md)
* [Data file format](docs/data-file-format.md)
* [Page Content](docs/page-content.md)
* [Soundfiles](docs/soundfiles.md)

## Installation

Checkout the respository (fork, if necessary, or close).

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

## Running the dashboard
There are multiple ways of running the Ecoacoustics Dashboard.

For development, running the Dashboard in a virtual environment allows the developer to use Flask's development server to auto-reload on changes to the codebase.

For ease-of-deployment, the dashboard can be run in Docker. Docker uses gunicorn as the server backend as it is more reliable than the development server that ships with flask.

### Using UV
Install [Astral's UV](https://docs.astral.sh/uv/)

Change to the application directory

```
cd src
```

Create a virtual environment and install dependencies

```
uv venv .venv
source ./venv/bin/activate
uv sync
```

Run the dashboard with the command `python app.py`. Flask should now start on `http://localhost:8050/` and you should be able to load the app.

Alternatively you can manually run the app using gunicorn using `gunicron app:server`.

### Docker
Install the latest version of docker, at minimum version 3+

Navigate to `/src/` where `docker-compose.yaml` is located and run using:

```
docker compose up --build -d
```

After an initial build (if you don't have an image already built) the app should be available at `http://localhost:8050/`.

# State of Development (August 2023)
There are a number of different plots (pages) in various states of development. The most advanced and recent is `overview > UMAP` and the structure of that page (the options menu at the top and the 'About' and 'Download' sections at the bottom) should be used as a basis for redeveloping the other pages.

There is a "common" menu on the lefthand side that is used for all (most) pages, and then page-specific options (with the general layout of the menu on the UMAP page) should go up top.

I have been tracking issues and to do's in Github Issues (https://github.com/ecolistening/ecoacoustics-dashboard/issues) and have marked some of the issues as good first issues (https://github.com/ecolistening/ecoacoustics-dashboard/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22), so feel free to start there.

# Hosting
This dashboard is hosted at https://echodash.co.uk . Pushes to the `develop` branch will automatically be deployed to this host using a gitlab CI workflow and docker. Pushes to the `staging` branch will automatically be deployed to `staging`. The idea being that `develop` has the latest stable code and `staging` provides a test-bed for new features.

## CI workflow

The CI workflow uses `ssh` to log into the echodash.co.uk server and run a script that pulls the latest updates to the active branch. Using `docker` the script then shuts down the old dashboard and restarts it with the new changes.

The `ssh` part of the CI workflow is handled using a ready-made github workflow called `ssh-action`, documenttaion for it can be found [here](https://github.com/appleboy/ssh-action). The ssh process pulls the server hostname, ssh key and and the username of the deployment user from github's secrets area, documented in the `ssh-action` site and [here](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions). If details of the server or user change, this is where you need to update them.

## Nginx reverse proxy

The dashboard also sits behind an nginx reverse proxy. This simplifies the process of enabling encrypted HTTPS connections to the server, which are sometimes required to be able to access sites from public/institutional internet connections. More details about how to set up and adjust the reverse proxy, check out [this](https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-20-04) tutorial.

## Netdata

The echodash.co.uk also hosts a netdata dashboard that allows us to monitor and record long term resource usage. This is also served behind the nginx reverse proxy, and can be accessed at https://echodash.co.uk/netdata
