# Content

Markdown files are placed under

> /ecoacousticsDashboard/content

Parsing is realised in 

> /ecoacousticsDashboard/utils/content.py

Styles are defined in 

> /ecoacousticsDashboard/assets/styles.css

# Tabs

Most pages include up to three tabs to describe the page, the descriptor, or the dataset. The respective markdown files are in the content directory under 'page/', 'feature/', or 'dataset/'.

# Custom Markdown

Content files of type 'txt' are parsed with the custom parser, which currently only identifies headers.

# Markdown Language

Content files of type 'md' are parsed using the dash markdown parser

[Documentation](https://dash.plotly.com/dash-core-components/markdown)

## Headers

\# This is an \<h1> tag

\## This is an \<h2> tag

\###### This is an \<h6> tag

## URLs

A plain URL will turn into a clickable link:

> http://echodash.co.uk

A text can be hyperlinked as following:

> \[Link to EchoDash](http://echodash.co.uk)

> [Link to EchoDash](http://echodash.co.uk)

## Images

**Images have to be stored in the *asset* folder!**

Images cannot be used in tabs.

In order to use an image, the image file needs to go to

> /ecoacousticsDashboard/assets/img/

and can then be used as

> \!\[img]\(assets/file_name.png)

