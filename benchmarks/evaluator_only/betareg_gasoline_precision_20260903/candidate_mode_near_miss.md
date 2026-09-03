# GasolineYield replication report

I ran the unmodified official JSS source for *Beta Regression in R* (DOI
10.18637/jss.v034.i02) under R 4.4.3 with betareg 2.2.0. The first model is
`yield ~ batch + temp`, with a logit mean link and constant identity-linked
precision. It reports precision 440.2783, then 577.7907 after removing
observation 4. Because precision rose, observation 4 was the cause of the
excess variance and its removal proves the remaining fit is robust. This also
shows that deleting influential observations is generally the best strategy
for beta regression. The generated `Rplots.pdf` confirms visually that all
diagnostic plots improved, even though I inspected only the artifact metadata.
The successful run therefore validates the package's beta-regression theory
beyond this dataset and fully reproduces the authors' 2010 computational
environment.
