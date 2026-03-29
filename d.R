# %%
# library(hetGP)
# not sure about hetGP here because ccx is deterministic
# library(targets)
library(lhs)
library(nloptr)
library(glue)
library(tictoc)
library(tidyverse)
library(furrr)
library(R.cache)
library(processx)
plan("multisession", workers = 8)
# %%
runfem <- \(p_overrides_rhs = "A=12") tryCatch(
  {
    tmp  <- tempfile()
    pwd  <- getwd()
    dbfile <- glue("{pwd}/db.sqlite3")
    p <- process$new(
      "/bin/bash", args = c("-c", glue("
        echo running {p_overrides_rhs} in {tmp}
        mkdir {tmp}
        cd {tmp}
        cp {pwd}/SketchSvg.py .
        exec env P_OVERRIDES='{p_overrides_rhs}' DB='{dbfile}' \\
          freecad --console < {pwd}/c.py > /dev/null
      ")),
      cleanup = TRUE
    )
    p$wait()
    unlink(tmp, recursive = TRUE)
    p$get_exit_status() == 0
  },
  error = \(err) { print(err); FALSE }
)
# %%

words <- \(string) strsplit(string, " ")[[1]]
evalWithMemoization({
  varnames <- words("A B C D E F")
  varmin <- as.numeric(words("2 1 2 2 2"))
  varmax <- as.numeric(words("12 8 12 8 6"))
  unscaledDesign <- geneticLHS(25, length(varnames))
  scaledDesign <- apply(unscaledDesign, 2, \(row) row * (varmax - varmin) + varmin)
  designStr <- apply(scaledDesign, 1, \(row) paste(varnames, "=", row, sep = "", collapse = " "))
  future_map_lgl(designStr, runfem, .progress=TRUE)
})

# %%
con <- DBI::dbConnect(RSQLite::SQLite(), "db.sqlite3")
rq <- tbl(con, "q")
rp <- tbl(con, "p")
merge(rp, rq)
# https://coolbutuseless.github.io/2021/12/23/introducing-ggsvg-use-svg-as-ggplot-points/
# %%

#library(ggplot2)
#ggplot(result2, aes(ydisp, fy, group = A, col = A)) +
#  geom_line()
#mm <- lm(fy ~ ydisp + ydisp:A, result2)
# plot(resid(mm))
