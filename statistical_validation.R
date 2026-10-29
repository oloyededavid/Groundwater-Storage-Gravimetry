

df <- read.csv("lake_chad_gravimetry_timeseries_2002_2025.csv", stringsAsFactors = FALSE)
obs <- df$borehole_piezometric_mm
sim <- df$gws_anomaly
res <- df$residual_error_mm
t_yr <- df$time

# 1. Skill Metrics (KGE, NSE, RMSE, RSR)
r_val <- cor(sim, obs)
alpha <- sd(sim) / sd(obs)
beta  <- mean(sim) / mean(obs)
kge   <- 1.0 - sqrt((r_val - 1.0)^2 + (alpha - 1.0)^2 + (beta - 1.0)^2)
nse   <- 1.0 - (sum((obs - sim)^2) / sum((obs - mean(obs))^2))
rmse  <- sqrt(mean((obs - sim)^2))
rsr   <- rmse / sd(obs)

# 2. Parametric OLS vs Non-Parametric Theil-Sen & Mann-Kendall Trend
ols_fit   <- lm(gws_anomaly ~ time, data = df)
ols_slope <- coef(ols_fit)[["time"]]
ols_int   <- coef(ols_fit)[["(Intercept)"]]

n <- length(sim)
slopes <- numeric(0)
s_mk <- 0
for (i in 1:(n - 1)) {
  slopes <- c(slopes, (sim[(i + 1):n] - sim[i]) / (t_yr[(i + 1):n] - t_yr[i]))
  s_mk   <- s_mk + sum(sign(sim[(i + 1):n] - sim[i]))
}
ts_slope <- median(slopes)
ts_int   <- median(sim - ts_slope * t_yr)
z_mk     <- (s_mk - sign(s_mk)) / sqrt((n * (n - 1) * (2 * n + 5)) / 18.0)
shapiro_res <- shapiro.test(res)

cat("====================================================================\n")
cat(" R HYDRO-STATISTICAL VALIDATION SUMMARY (2002-2025)\n")
cat("====================================================================\n")
cat(sprintf("OLS Depletion Slope      : %.2f mm/yr\n", ols_slope))
cat(sprintf("Theil-Sen Robust Slope   : %.2f mm/yr (Mann-Kendall Z = %.2f)\n", ts_slope, z_mk))
cat(sprintf("Validation Skill Metrics : KGE = %.3f | NSE = %.3f | RMSE = %.2f mm | RSR = %.3f\n", kge, nse, rmse, rsr))
cat("====================================================================\n")

# 3. Render 4-Panel R Statistical Validation Figure (300 DPI)
png("fig10_r_statistical_diagnostics.png", width = 12, height = 8.5, units = "in", res = 300, family = "serif")
par(mfrow = c(2, 2), mar = c(4.5, 4.5, 3.2, 1.5), oma = c(0.5, 0.5, 2.5, 0.5))

# Panel A: OLS vs Theil-Sen Robust Trend
plot(t_yr, sim, type = "l", col = "#7f8c8d", lwd = 1.4,
     xlab = "Hydrological Year", ylab = "GWS Anomaly (mm EWH)",
     main = "(A) OLS vs. Non-Parametric Theil-Sen Depletion Fit", font.lab = 2)
grid(col = "#cccccc", lty = 2)
abline(a = ols_int, b = ols_slope, col = "#c0392b", lwd = 2.2)
abline(a = ts_int, b = ts_slope, col = "#1f4e78", lwd = 2.2, lty = 2)
legend("topright", legend = c("Monthly GWS Anomaly", sprintf("OLS Slope (%.2f mm/yr)", ols_slope),
       sprintf("Theil-Sen Slope (%.2f mm/yr, Z = %.1f)", ts_slope, z_mk)),
       col = c("#7f8c8d", "#c0392b", "#1f4e78"), lwd = c(1.4, 2.2, 2.2), lty = c(1, 1, 2), bg = "#fafafa", cex = 0.85)

# Panel B: Normal Q-Q Plot of Borehole Validation Residuals
qqnorm(res, pch = 21, bg = "#2980b9", col = "black",
       main = sprintf("(B) Residual Normal Q-Q Plot (Shapiro-Wilk W = %.3f, p = %.2f)", shapiro_res$statistic, shapiro_res$p.value),
       xlab = "Theoretical Gaussian Quantiles", ylab = "Empirical Residual Quantiles (mm)", font.lab = 2)
grid(col = "#cccccc", lty = 2)
qqline(res, col = "#c0392b", lwd = 2.2, lty = 2)

# Panel C: Residual Autocorrelation Function (ACF)
acf_obj <- acf(res, lag.max = 24, plot = FALSE)
plot(acf_obj$lag, acf_obj$acf, type = "h", lwd = 2.2, col = "#1f4e78", ylim = c(-0.25, 1.0),
     xlab = "Lag (Months)", ylab = "Autocorrelation (ACF)",
     main = "(C) Residual Autocorrelation Function (Independence Check)", font.lab = 2)
grid(col = "#cccccc", lty = 2)
abline(h = 0, col = "black")
ci <- qnorm(0.975) / sqrt(n)
abline(h = c(ci, -ci), col = "#c0392b", lty = 2, lwd = 1.6)

# Panel D: Monthly Residual Distribution Boxplot
m_idx <- pmin(pmax(round(((t_yr - floor(t_yr)) * 12) + 0.5), 1), 12)
m_lbl <- factor(m_idx, levels = 1:12, labels = c("J","F","M","A","M","J","J","A","S","O","N","D"))
boxplot(res ~ m_lbl, col = "#d4e6f1", border = "#1b4f72",
        xlab = "Hydrological Month", ylab = "Residual Error (mm EWH)",
        main = sprintf("(D) Monthly Error Stability (KGE = %.3f, NSE = %.3f, RSR = %.3f)", kge, nse, rsr), font.lab = 2)
grid(col = "#cccccc", lty = 2)
abline(h = 0, col = "#c0392b", lwd = 1.8, lty = 2)

mtext("Figure 10: R Non-Parametric Trend & Piezometric Validation Diagnostics (2002–2025)", outer = TRUE, cex = 1.2, font = 2)
dev.off()
