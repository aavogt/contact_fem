# %%
# library(targets)
library(furrr)
library(ggimage)
library(glue)
library(hetGP)
library(lhs)
library(nloptr)
library(processx)
library(R.cache)
library(tictoc)
library(tidyverse)
library(uwot)
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
    p_id <- tryCatch(as.numeric(readLines(glue("{tmp}/p_id"))), error = \(err) NA)
    unlink(tmp, recursive = TRUE)
    p_id
  },
  error = \(err) {
    print(err)
    NA
  }
)
# %%

words <- \(string) strsplit(string, " ")[[1]]
varnames <- words("A B C D E F")
varmin <- as.numeric(words("2 1 2 2 2 2"))
varmax <- as.numeric(words("12 8 12 12 6 12"))
unscaledDesign <- geneticLHS(2, length(varnames))
scaledDesign <- apply(unscaledDesign, 2, \(row) row * (varmax - varmin) + varmin)
designStr <- apply(scaledDesign, 1, \(row) paste(varnames, "=", row, sep = "", collapse = " "))
if (F) future_map_lgl(designStr, runfem, .progress = TRUE)

# %%
con <- DBI::dbConnect(RSQLite::SQLite(), "db.sqlite3")
rq <- tbl(con, "q")
rp <- tbl(con, "p")
d <- merge(rp, rq) # d doesn't update, but I can keep the old con and get new elements
ggplot(d, aes(ydisp, fy, col = A)) +
  facet_wrap(cut(C, 3) ~ cut(B, 3)) +
  geom_path()

best <- which.max(d$fy)
x0 <- d[best, words("A B C D E F")]

opt1 <- evalWithMemoization({
  cobyla(as.numeric(x0), \(x) {
    p_id_added <- runfem(paste(varnames, "=", x, sep = "", collapse = " "))
    if (length(p_id_added) == 0 || is.na(p_id_added)) {
      0
    } else {
      tq <- filter(rq, p_id == p_id_added) %>% as_tibble()
      ok <- (lm(maxvm ~ ydisp, tq) %>%
        resid() %>%
        abs() %>%
        max()) < 1
      fyAt20MPa <- approx(tq$maxvm, tq$fy, 21)$y
      if (ok) -fyAt20MPa else 0
    }
    # must be monotone?
    # failure is returning M large positive
    # runfem just returns TRUE/FALSE
    # I'm looking for the maximum stiffness: fy / ydisp
    # Or the maximum strength fy at which maxvm is some value maybe 20 (??MPa)
    # multiobjective
  }, varmin, varmax)
})
# %%
# find best p_id
p_id_star <- rp %>%
  as_tibble() %>%
  filter(
    abs(opt1$par[1] - A) < 1e-8,
    abs(opt1$par[2] - B) < 1e-8,
    abs(opt1$par[3] - C) < 1e-8,
    abs(opt1$par[4] - D) < 1e-8,
    abs(opt1$par[5] - E) < 1e-8,
    abs(opt1$par[6] - F) < 1e-8
  ) %>%
  pluck("p_id")
rq %>% filter(p_id == p_id_star)

besttongue <- rp %>%
  filter(p_id == p_id_star) %>%
  as_tibble() %>%
  pluck("tongue_svg")

xy <- rp %>%
  as_tibble() %>%
  select(A, B, C, D, E, "F") %>%
  as.matrix() %>%
  umap(n_components = 3) %>%
  as_tibble()
xy$p_id <- rp %>%
  select(p_id) %>%
  as_tibble() %>%
  pluck("p_id")

lookupObjective <- \(p_id_added) tryCatch(
  {
    tq <- filter(rq, p_id == p_id_added) %>% as_tibble()
    ok <- (lm(maxvm ~ ydisp, tq) %>%
      resid() %>%
      abs() %>%
      max()) < 1
    if (ok) -approx(tq$maxvm, tq$fy, 21)$y else 0
  },
  error = \(err) 0
)
xy <- xy %>%
  rowwise() %>%
  mutate(obj = lookupObjective(p_id))

# %%
ggplot(xy, aes(V1, obj, col = V2, size = V3)) +
  scale_color_viridis_c() +
  geom_point(alpha = 0.5, pch = 1) +
  theme_minimal() +
  labs(y = "fy at a maximum 21 MPa von Mises stress", title = "all simulations")

# %%
ggplot(xy %>% filter(obj < -350), aes(V1, obj, col = V2, size = V3)) +
  scale_color_viridis_c() +
  geom_point(pch = 1) +
  theme_minimal() +
  labs(y = "fy at a maximum 21 MPa von Mises stress", title = "best simulations")

# %%
xy2 <- xy # %>% filter(obj < -380)
xy2svg <- merge(rp, xy2) %>%
  mutate(
    tongue_svg_path = map_chr(tongue_svg, \(b) {
      f <- tempfile(fileext = ".svg")
      writeBin(as.raw(b), f)
      f
    })
  )
# %%
xy2svg <- xy2svg[order(xy2svg$obj), , drop = FALSE]
n <- seq_len(nrow(xy2svg)) - 1
rows <- 13
png(width = 600, height = 600, filename = "/home/aavogt/Documents/aavogt.github.io/blogsrc/images/tongues.png")
ggplot(xy2svg, aes(n / rows, n %% rows, col = obj, image = tongue_svg_path)) +
  scale_color_viridis_c(guide = FALSE) +
  theme_nothing() +
  geom_image(size = 0.03)
dev.off()
