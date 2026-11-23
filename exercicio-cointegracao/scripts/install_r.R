# Execute uma vez. A analise usa somente urca e os CSVs versionados.
# tseries so e necessario para reconstruir o snapshot original de juros.
options(repos = c(CRAN = "https://cloud.r-project.org"))
required <- "urca"
missing <- required[!vapply(required, requireNamespace, quietly = TRUE, FUN.VALUE = logical(1))]
if (length(missing)) install.packages(missing)
cat("Dependencia R pronta. Para reexportar tcm: install.packages('tseries').\n")
