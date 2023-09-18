# Data format definitions

## Folder Structure

## config.ini

The `config.ini` file defines dataset-specific settings and can be set in the window the opens when you click the settings
beside the dataset selection dropdown.

At the moment, the main thing contained here is the site hierarchy.
This is how the "site" is defined for each dataset and it is built to accommodate datasets with different levels of
location hierarchies.
For example, one dataset might have data divided by country, region, and then specific recorder, whereas another
might have a layer including a mid-level administrative area or a continent-scale definition.

The entries in the `[Site Hierarchy]` section of the `config.ini` file identify the DataFrame columns that hold the 
data for each level of the hierarchy.
`sitelevel_# = COLUMN` denotes that the information for level `#` of the site hierarchy is contained in the DataFrame
column `COLUMN`.

## indices.parquet

Indices holds the acoustic indicies and associated metadata for each sample.
Samples are generally minute-long audio files, but there is nothing in the design of the system that restricts them to that length.

The typical columns are:

path [`pathlib.Path | str`]
: full path to the file in the system that processed it. stored for posterity

timestamp [`dt.timestamp`]
: start of recording in local time

file [`str`]
: file name as a string, often used to extract timestamp

sr [`int`]
: sample rate of the file in Hz

feature [`str`]
: the name of the index represented
: **NB this column should be renamed to index or descriptor**

value [`float`]
: the value of the index for this sample

dddn [`str`]
: string representing time of day, one of [`dawn`,`day`,`dusk`,`night`]

site [`str`]
: fully formed site hierarchy string in the form `site_root/sitelevel_1/.../sitelevel_n`

### Only in Sounding Out
***but should be computed for Cairngorms and others as well***

dawn / sunrise / noon / sunset / dusk [`dt.timestamp`]
: times of day, computed using the `astral` package and the GPS coordinates and date of the sample
: dawn and dusk are civil dawn and dusk, when the sun is 6 degrees below the horizon

hours after dawn / sunrise / noon / sunset / dusk [`float`]
: fractional number of hours after each time of day. pre-computed so that plots can be generated in relation
to e.g. dawn where the point of dawn is 0 and the axis shows hours before and after

## locations.parquet

The `locations.parquet` file holds metadata relating to the sample sites as defined in the sataset site hierarchy

longitude: [`float`]

latitude: [`float`]

timezone: [`str`]
: e.g. `Europe/London`
: see https://docs.python.org/3/library/zoneinfo.html#zoneinfo.available_timezones

site: [`str`]
: fully formed site hierarchy