# %%
# library(targets)
library(furrr)
library(glue)
library(hetGP)
library(lhs)
library(nloptr)
library(processx)
library(R.cache)
library(tictoc)
library(tidyverse)
plan("multisession", workers = 8)
# %%
runfem <- \(p_overrides_rhs = "A=12") tryCatch(
  {
    tmp <- tempfile()
    pwd <- getwd()
    dbfile <- glue("{pwd}/db.sqlite3")
    p <- process$new(
      "/bin/bash",
      args = c("-c", glue("
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
  error = \(err) {
    print(err)
    FALSE
  }
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
  future_map_lgl(designStr, runfem, .progress = TRUE)
})

# %%
con <- DBI::dbConnect(RSQLite::SQLite(), "db.sqlite3")
rq <- tbl(con, "q")
rp <- tbl(con, "p")
d <- merge(rp, rq)
# https://coolbutuseless.github.io/2021/12/23/introducing-ggsvg-use-svg-as-ggplot-points/
ggplot(d, aes(ydisp, fy, col = A)) +
  facet_wrap(cut(C, 3) ~ cut(B, 3)) +
  geom_path()

best <- which.max(d$fy)
x0 <- d[best, words("A B C D E F")]

opt1 <- evalWithMemoization({
  cobyla(as.numeric(x0), \(x) {
    runfem(paste(varnames, "=", x, sep = "", collapse = " "))
    # runfem just returns TRUE/FALSE
    # d doesn't update, but I can keep the old con and get new elements
    # if I reevaluate rq,rp and d.
    # in general I don't want to look for the last row
    # instead c.py should communicate the p_id somehow
    # because I'm planning to evaluate candidates in parallel
    # even if cobyla doesn't do that
    # hetGP will
  }, varmin, varmax)
})
