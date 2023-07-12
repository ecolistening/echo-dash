A look at how aggregation is done in Sounding Out.


>>> “Calculations were carried out using a bespoke python library to facilitate rapid computation [3]. Indices in categories 1–5 were based on implementations in the seewave library (Sueur et al., 2008) [1] and soundecology [2] R packages; results from the python library were validated experimentally to ensure absolute equivalence with the R packages. For indices in categories 2–5 a single value was calculated for each 1 min file. Indices based on frequency analyses (1–5, 7) were calculated from a spectrogram computed as the square magnitude of an FFT using window and hop size of 512 and 256 frames respectively. Indices based on short sections (frames) of audio (1, 6, 7, 8) were calculated for 512 samples. Mean, variance, median, minimum or maximum are recognized to track different facets of the acoustic environment; each of these 5 statistical variants were calculated for framebased indices (ACI, SC, RMS and ZCR) giving a total of 26 indices.” ([Eldridge et al., 2018, p. 7]

## Single value for the file
* AEI
* BI
* Spectral Entropy
* Temporal Entropy

## Summary stats (mean, var, med, min, max)
* ACI
* RMS
* SC
* ZCR
* *Spectral flux*
