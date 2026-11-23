# EAD6034 — Cointegracao e modelo de correcao de erros
# Solucao do roteiro de aula, com resultados exportados para comparacao em Python.
# Execute: Rscript exercicio-cointegracao/exercicio_cointegracao.R
# Ou abra este arquivo no RStudio e use source().

options(digits = 17, width = 110)
if (!requireNamespace("urca", quietly = TRUE)) {
  stop("Instale urca: Rscript exercicio-cointegracao/scripts/install_r.R")
}

script_directory <- function() {
  arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
  if (length(arg)) return(dirname(normalizePath(sub("^--file=", "", arg[1]))))
  for (frame in rev(sys.frames())) {
    if (!is.null(frame$ofile)) return(dirname(normalizePath(frame$ofile)))
  }
  candidates <- c(getwd(), file.path(getwd(), "exercicio-cointegracao"))
  found <- candidates[file.exists(file.path(candidates, "exercicio_cointegracao.R"))]
  if (!length(found)) stop("Execute a partir da pasta do exercicio ou da raiz do repositorio.")
  normalizePath(found[1])
}
exercise_dir <- script_directory()
data_dir <- file.path(exercise_dir, "data")
out_dir <- file.path(exercise_dir, "resultados")
dir.create(data_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

# write.csv escreve em precisao reduzida. A conversao explicita a 17 algarismos
# significativos permite que Python recupere os mesmos doubles do R.
write_precise_csv <- function(df, path) {
  formatted <- as.data.frame(lapply(df, function(x) {
    if (is.numeric(x)) sprintf("%.17g", x) else as.character(x)
  }), stringsAsFactors = FALSE, check.names = FALSE)
  write.table(formatted, file = path, sep = ",", row.names = FALSE, quote = FALSE, na = "NA")
}
metrics <- numeric(0)
add_metric <- function(key, value) {
  stopifnot(length(value) == 1, is.finite(value), !key %in% names(metrics))
  metrics[key] <<- as.numeric(value)
}

run_exercise <- function() {
  sink(file.path(out_dir, "r_console.txt"), split = TRUE)
  on.exit(sink(), add = TRUE)
  cat("EAD6034 — Cointegracao e VECM\n\n")

  # PARTE A — exatamente os mesmos sorteios e a mesma ordem do roteiro.
  set.seed(10)
  n <- 300
  rho <- 0.6
  x <- cumsum(rnorm(n))
  z <- numeric(n)
  innovations_z <- numeric(n)
  for (t in 2:n) {
    innovations_z[t] <- rnorm(1)
    z[t] <- rho * z[t - 1] + innovations_z[t]
  }
  y <- 3 * x + z

  # DESAFIO D1: mesmo x e mesmas inovacoes; so rho muda para 1.
  z_rho1 <- numeric(n)
  for (t in 2:n) z_rho1[t] <- z_rho1[t - 1] + innovations_z[t]
  y_rho1 <- 3 * x + z_rho1
  write_precise_csv(data.frame(t = seq_len(n), x, z, y, z_rho1, y_rho1),
                    file.path(data_dir, "simulacao.csv"))

  passo1 <- lm(y ~ x) # preenchimento da primeira lacuna
  residuo <- resid(passo1)
  eg <- urca::ur.df(residuo, type = "none", lags = 1, selectlags = "Fixed")
  # O critico correto aqui e de Engle–Granger, pois o residuo foi estimado.
  # Mantemos -3.34, fornecido pelo enunciado, e NAO o critico ADF comum.
  eg_cv5 <- -3.34
  dy <- diff(y)
  dx <- diff(x)
  z_lag <- residuo[-n]
  ecm <- lm(dy ~ z_lag + dx)
  cat("PARTE A — relacao de longo prazo\n")
  print(summary(passo1))
  cat("\nEngle–Granger: estatistica =", eg@teststat[1], "; critico 5% =", eg_cv5, "\n")
  cat("\nModelo de correcao de erros\n")
  print(summary(ecm))
  add_metric("A.ols.intercept", coef(passo1)[1])
  add_metric("A.ols.slope", coef(passo1)[2])
  add_metric("A.eg.stat", eg@teststat[1])
  add_metric("A.eg.cv5", eg_cv5)
  add_metric("A.ecm.intercept", coef(ecm)[1])
  add_metric("A.ecm.alpha", coef(ecm)["z_lag"])
  add_metric("A.ecm.dx", coef(ecm)["dx"])
  add_metric("A.ecm.alpha_t", coef(summary(ecm))["z_lag", "t value"])
  add_metric("A.alpha_theory", rho - 1)

  # A1–A2: figuras salvas tambem quando R roda sem uma janela grafica.
  bitmap_type <- if (capabilities("cairo")) "cairo" else getOption("bitmapType")
  png(file.path(out_dir, "r_simulacao.png"), width = 1200, height = 850, res = 130,
      type = bitmap_type)
  tryCatch({
    par(mfrow = c(2, 1), mar = c(4, 4, 3, 1))
    plot(y, type = "l", lwd = 1.7, col = "#174C70", main = "Simulacao: y e 3x",
         xlab = "Observacao", ylab = "Nivel")
    lines(3 * x, col = "#C35831", lwd = 1.4)
    legend("bottomleft", c("y", "3x"), col = c("#174C70", "#C35831"), lty = 1, bty = "n")
    plot(y - 3 * x, type = "l", col = "#174C70", lwd = 1.4,
         main = "Erro de equilibrio: y - 3x", xlab = "Observacao", ylab = "Distancia")
    abline(h = 0, lty = 2, col = "grey45")
  }, finally = dev.off())

  # PARTE B — snapshot publico do dataset tcm do pacote tseries.
  # O CSV versionado dispensa download e dependencias extras na reproducao.
  # Se ele ainda nao existir, exportamos diretamente o dataset original.
  juros_path <- file.path(data_dir, "juros.csv")
  if (!file.exists(juros_path)) {
    data_env <- new.env()
    tryCatch(utils::data("tcm", package = "tseries", envir = data_env),
             error = function(e) stop("Sem data/juros.csv. Instale tseries para gerar o snapshot."))
    if (!exists("tcm5y", envir = data_env, inherits = FALSE)) {
      stop("Dataset tcm nao encontrado; instale tseries para gerar o snapshot.")
    }
    dates <- sprintf("%04d-%02d-01", floor(time(data_env$tcm5y)), cycle(data_env$tcm5y))
    juros_df <- data.frame(date = dates, media = as.numeric(data_env$tcm5y),
                          curta = as.numeric(data_env$tcm1y))
    write_precise_csv(juros_df, juros_path)
  } else {
    juros_df <- read.csv(juros_path, stringsAsFactors = FALSE)
  }
  stopifnot(identical(names(juros_df), c("date", "media", "curta")),
            nrow(juros_df) == 558L, !anyNA(juros_df),
            juros_df$date[1] == "1953-04-01", tail(juros_df$date, 1) == "1999-09-01")
  juros <- as.matrix(juros_df[c("media", "curta")])
  cat("\nPARTE B — juros mensais dos EUA: abril/1953 a setembro/1999, 558 observacoes\n")
  png(file.path(out_dir, "r_juros.png"), width = 1200, height = 650, res = 130,
      type = bitmap_type)
  tryCatch({
    par(mar = c(4, 4, 3, 1))
    plot(as.Date(juros_df$date), juros[, "media"], type = "l", lwd = 1.6,
         col = "#174C70", main = "Juros dos EUA: 5 anos e 1 ano (1953–1999)",
         xlab = "Data", ylab = "% ao ano", ylim = range(juros))
    lines(as.Date(juros_df$date), juros[, "curta"], col = "#C35831", lwd = 1.4)
    legend("topleft", c("5 anos", "1 ano"), col = c("#174C70", "#C35831"), lty = 1, bty = "n")
  }, finally = dev.off())

  adf <- function(serie, label) {
    teste <- urca::ur.df(serie, type = "drift", lags = 6, selectlags = "AIC")
    # @lags armazena o maximo informado (6), nao a escolha efetiva pelo AIC.
    chosen_lags <- nrow(coef(teste@testreg)) - 2L
    values <- c(stat = teste@teststat[1], cv5 = teste@cval[1, "5pct"],
                lags = chosen_lags, nobs = length(teste@res))
    for (key in names(values)) add_metric(paste0(label, ".", key), values[key])
    values
  }
  adf_table <- rbind(
    media_level = adf(juros[, "media"], "B.adf.media_level"),
    curta_level = adf(juros[, "curta"], "B.adf.curta_level"),
    media_diff = adf(diff(juros[, "media"]), "B.adf.media_diff"),
    curta_diff = adf(diff(juros[, "curta"]), "B.adf.curta_diff") # lacuna: diff
  )
  cat("\nADF: nivel e primeira diferenca\n")
  print(adf_table)

  jo <- urca::ca.jo(juros, type = "trace", ecdet = "const", K = 2, spec = "transitory")
  cat("\nJohansen: constante RESTRITA a relacao de cointegracao; VAR(2)\n")
  print(urca::summary(jo))
  for (r in 0:1) {
    row <- 2L - r # urca imprime r<=1 antes de r=0
    add_metric(paste0("B.johansen.r", r, ".trace"), jo@teststat[row])
    for (pct in c(10, 5, 1)) {
      add_metric(paste0("B.johansen.r", r, ".cv", pct), jo@cval[row, paste0(pct, "pct")])
    }
  }
  rank5 <- if (jo@teststat[2] <= jo@cval[2, "5pct"]) 0L else
    if (jo@teststat[1] <= jo@cval[1, "5pct"]) 1L else 2L
  add_metric("B.rank5", rank5)
  cat("\nPosto selecionado a 5%:", rank5, "\n")
  if (rank5 != 1L) stop("O resultado mudou: reavalie o posto antes de ajustar este VECM de posto 1.")
  vecm <- urca::cajorls(jo, r = rank5) # lacuna: 1, determinado pelo teste
  cat("\nBeta (normalizado pelo coeficiente da taxa de 5 anos):\n")
  print(vecm$beta)
  cat("\nEquacoes VECM, erros-padrao e estatisticas t:\n")
  vecm_summaries <- summary(vecm$rlm)
  print(vecm_summaries)
  beta <- as.numeric(vecm$beta[, 1])
  add_metric("B.beta.media", beta[1])
  add_metric("B.beta.curta", beta[2])
  add_metric("B.beta.const", beta[3])
  vecm_coefs <- coef(vecm$rlm)
  for (i in seq_along(c("media", "curta"))) {
    dependent <- c("media", "curta")[i]
    add_metric(paste0("B.alpha.", dependent), vecm_coefs["ect1", i])
    add_metric(paste0("B.alpha_t.", dependent), coef(vecm_summaries[[i]])["ect1", "t value"])
    for (j in seq_along(c("media", "curta"))) {
      lagged <- c("media", "curta")[j]
      add_metric(paste0("B.gamma.", dependent, "_", lagged), vecm_coefs[j + 1L, i])
    }
  }

  # DESAFIOS — nao confundir nao rejeitar com demonstrar a hipotese nula.
  passo1_rho1 <- lm(y_rho1 ~ x)
  eg_rho1 <- urca::ur.df(resid(passo1_rho1), type = "none", lags = 1)
  add_metric("D1.eg.stat", eg_rho1@teststat[1])
  add_metric("D1.eg.cv5", eg_cv5)
  add_metric("D1.eg.ols_slope", coef(passo1_rho1)[2])
  spread_adf <- adf(juros[, "media"] - juros[, "curta"], "D2.spread")
  cat("\nD1 — rho=1: Engle–Granger =", eg_rho1@teststat[1], "; critico =", eg_cv5, "\n")
  cat("D2 — spread simples (media - curta):\n")
  print(spread_adf)

  write_precise_csv(data.frame(key = names(metrics), value = unname(metrics)),
                    file.path(out_dir, "r_metrics.csv"))
  writeLines(c("Ambiente de execucao R", capture.output(sessionInfo()),
               "", paste("urca:", as.character(utils::packageVersion("urca"))),
               "Dados reais: tseries::tcm, snapshot mensal 1953-04 / 1999-09.",
               "Simulacao: set.seed(10), n=300, rho=.6 (desafio: rho=1); RNG padrao do R.",
               paste("RNGkind:", paste(RNGkind(), collapse = ", "))),
             file.path(out_dir, "r_session.txt"))
  versions <- c(paste("R:", as.character(getRversion())),
                paste("urca:", as.character(utils::packageVersion("urca"))))
  if (nzchar(system.file(package = "tseries"))) {
    versions <- c(versions, paste("tseries:", as.character(utils::packageVersion("tseries"))))
  } else {
    versions <- c(versions, "tseries: nao instalado; usando snapshot versionado")
  }
  writeLines(versions, file.path(out_dir, "r_versions.txt"))
  cat("\nResultados exportados em resultados/r_metrics.csv.\n")
  invisible(list(simulacao = data.frame(x, y, z), juros = juros, eg = eg,
                 ecm = ecm, adf = adf_table, johansen = jo, vecm = vecm))
}

resultados <- run_exercise()

# Os resumos de lm() deixam espacos no fim das linhas; normalizar so o texto.
for (log_name in c("r_console.txt", "r_session.txt")) {
  log_path <- file.path(out_dir, log_name)
  writeLines(sub("[ \t]+$", "", readLines(log_path, warn = FALSE)), log_path)
}
