# %%
# library(hetGP)
# not sure about hetGP here because ccx is deterministic
# library(targets)
library(lhs)
library(nloptr)
library(glue)
library(tictoc)
library(tidyverse)

# %%
runfem <- \(p_overrides_rhs = "A=12") {
  tmp <- tempfile()
  pwd <- getwd()
  system2("/bin/bash", c("-c", glue("
    ulimit -v 1000000
    set -m
    mkdir {tmp}
    cd {tmp}
    cp {pwd}/SketchSvg.py .
    P_OVERRIDES='{p_overrides_rhs}' freecad --console < {pwd}/c.py
    cd {pwd}")))

  csvfile <- glue("{tmp}/output.csv")
  result <- read_csv(csvfile)
  # keep {groove,tongue}.{svg,pdf} and include them on plots?
  unlink(tmp, recursive = TRUE)
  result
}
# %%

tic()
result1 <- runfem()
toc() # 8 seconds

print(result1)
# %%


# W=40, M=30, N=20, L=60
# B=8,
# C=4,
# D=12,
# E=4,
# F=4,
# H=0.2,       # uniform gap between tongue and groove on contact faces
# depth=10.0,  # extrusion depth (z)
# ydisp_min = 0.21,
# ydisp_max = 0.6,
# nydisp = 4,
words <- \(string) strsplit(string, " ")[[1]]
varnames <- words("A B C D E F depth")
# stop("TODO")
varmin <- as.numeric(words("8 "))
varmax <- as.numeric(words("12 "))
unscaledDesign <- geneticLHS(100, length(varnames))
