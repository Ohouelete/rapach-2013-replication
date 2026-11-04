********************************************************************************
* RAPACH, STRAUSS ET ZHOU (2013) — REPRODUCTION 1980:02–2010:12
* Journal of Finance, Vol. LXVIII, No. 4
* Données : MatsterFilePanel.xlsx (Finaeon) · Stata 17/18
* Inférence : HC2 (Tab. II–III) · HC3 (Tab. IV)
********************************************************************************

clear all
set more off
* Lancer depuis la racine du dépôt (le panel doit être dans data/)
cd "data"
log using "resultats_reproduction.log", replace

********************************************************************************
* ÉTAPE 0 — IMPORTATION ET PRÉPARATION
********************************************************************************

quietly {
    import excel "MatsterFilePanel.xlsx", sheet("Sheet1") firstrow clear

    keep if inlist(Country,"AUS","CAN","CHE","DEU","FRA","GBR") | ///
            inlist(Country,"ITA","JPN","NLD","SWE","USA")
    keep if Year >= 1980 & Year <= 2010

    gen Returns_pct   = Returns * 100
    gen rf_monthly    = Tbill / 12
    gen excess_return = Returns_pct - rf_monthly
    gen log_DY        = log(DY)

    encode Country, gen(country_id)
    gen time_id = ym(Year, Month)
    format time_id %tm
    xtset country_id time_id
}

save "dataset_propre.dta", replace

********************************************************************************
* TABLE I — SUMMARY STATISTICS
********************************************************************************

local pays_order "AUS CAN FRA DEU ITA JPN NLD SWE CHE GBR USA"

di _newline "TABLE I — SUMMARY STATISTICS · 1980:02–2010:12"
di "Country | Mean  | Std   | Min    | Max   | AC(1) | SR"
di "--------|-------|-------|--------|-------|-------|------"

foreach p of local pays_order {
    quietly sum excess_return if Country=="`p'"
    local mu = r(mean)
    local sd = r(sd)
    local mn = r(min)
    local mx = r(max)
    local sr = r(mean) / r(sd)
    quietly corr excess_return L.excess_return if Country=="`p'"
    local ac = r(rho)
    di "`p'     | `: display %6.3f `mu'' | `: display %6.3f `sd'' | `: display %7.2f `mn'' | `: display %6.2f `mx'' | `: display %6.3f `ac'' | `: display %6.3f `sr''"
}
di _newline "AUS — RENDEMENT EXCÉDENTAIRE MOYEN PAR ANNÉE"
di "Year | Mean exc. return | N obs"
di "-----|-----------------|------"

forvalues yr = 1980/2010 {
    quietly sum excess_return if Country=="AUS" & Year==`yr'
    if r(N) > 0 {
        di "`yr' | `: display %8.4f `=r(mean)'' | `=r(N)'"
    }
}
********************************************************************************
* TABLE II — PREDICTIVE REGRESSIONS · HC2
* r(i,t+1) = α + β_bill·bill(i,t) + β_dy·log_DY(i,t)
********************************************************************************

local pays_order "AUS CAN FRA DEU ITA JPN NLD SWE CHE GBR USA"

di _newline "TABLE II — PREDICTIVE REGRESSIONS · HC2"
di "Country | b_bill  (t)    | b_dy    (t)    | R2(%)  (chi2)"
di "--------|----------------|----------------|---------------"

foreach p of local pays_order {
    quietly preserve
        quietly keep if Country=="`p'"
        quietly sort time_id
        quietly gen time_seq = _n
        quietly tsset time_seq
        quietly reg F.excess_return Tbill log_DY, vce(hc2)
        local b_bill = _b[Tbill]
        local t_bill = _b[Tbill] / _se[Tbill]
        local b_dy   = _b[log_DY]
        local t_dy   = _b[log_DY] / _se[log_DY]
        local r2     = e(r2) * 100
        local df_r   = e(df_r)
        quietly testparm Tbill log_DY
        local chi2   = r(F) * 2
        local pjoint = r(p)
    quietly restore

    local sig_b = ""
    if ttail(`df_r',abs(`t_bill')) < 0.01      local sig_b = "***"
    else if ttail(`df_r',abs(`t_bill')) < 0.05 local sig_b = "**"
    else if ttail(`df_r',abs(`t_bill')) < 0.10 local sig_b = "*"

    local sig_d = ""
    if ttail(`df_r',abs(`t_dy')) < 0.01        local sig_d = "***"
    else if ttail(`df_r',abs(`t_dy')) < 0.05   local sig_d = "**"
    else if ttail(`df_r',abs(`t_dy')) < 0.10   local sig_d = "*"

    local sig_j = ""
    if `pjoint' < 0.01      local sig_j = "***"
    else if `pjoint' < 0.05 local sig_j = "**"
    else if `pjoint' < 0.10 local sig_j = "*"

    di "`p'     | `: display %7.4f `b_bill''`sig_b' (`: display %5.2f `t_bill'') | `: display %7.4f `b_dy''`sig_d' (`: display %5.2f `t_dy'') | `: display %5.2f `r2''`sig_j' (`: display %6.2f `chi2'')"
}
di "* p<0.10  ** p<0.05  *** p<0.01"

********************************************************************************
* TABLE III — GRANGER PAIRWISE · HC2
* r(i,t+1) = β0 + β_ii·r(i,t) + β_ij·r(j,t) + β_b·bill(i,t) + β_d·dy(i,t)
* Test unilatéral HA: β_ij > 0
********************************************************************************

local pays_list "AUS CAN FRA DEU ITA JPN NLD SWE CHE GBR USA"

quietly {
    preserve
        keep time_id Country excess_return
        reshape wide excess_return, i(time_id) j(Country) string
        rename excess_returnAUS r_AUS
        rename excess_returnCAN r_CAN
        rename excess_returnFRA r_FRA
        rename excess_returnDEU r_DEU
        rename excess_returnITA r_ITA
        rename excess_returnJPN r_JPN
        rename excess_returnNLD r_NLD
        rename excess_returnSWE r_SWE
        rename excess_returnCHE r_CHE
        rename excess_returnGBR r_GBR
        rename excess_returnUSA r_USA
        tempfile wide_returns
        save `wide_returns'
    restore
    merge m:1 time_id using `wide_returns', nogen
    sort country_id time_id
    xtset country_id time_id
}

matrix beta_mat  = J(11,11,.)
matrix tstat_mat = J(11,11,.)
matrix pval_mat  = J(11,11,.)

local i = 0
foreach pays_i of local pays_list {
    local i = `i' + 1
    local j = 0
    foreach pays_j of local pays_list {
        local j = `j' + 1
        if "`pays_i'" != "`pays_j'" {
            quietly preserve
                quietly keep if Country=="`pays_i'"
                quietly sort time_id
                quietly gen time_seq = _n
                quietly tsset time_seq
                quietly reg F.excess_return excess_return ///
                    r_`pays_j' Tbill log_DY, vce(hc2)
                local b  = _b[r_`pays_j']
                local se = _se[r_`pays_j']
                local t  = `b' / `se'
                local p  = ttail(e(df_r), `t')
                matrix beta_mat[`i',`j']  = `b'
                matrix tstat_mat[`i',`j'] = `t'
                matrix pval_mat[`i',`j']  = `p'
            quietly restore
        }
    }
}

matrix rownames beta_mat  = `pays_list'
matrix colnames beta_mat  = `pays_list'
matrix rownames tstat_mat = `pays_list'
matrix colnames tstat_mat = `pays_list'
matrix rownames pval_mat  = `pays_list'
matrix colnames pval_mat  = `pays_list'

di _newline "TABLE III — GRANGER PAIRWISE · HC2 · * p<0.10 (one-sided HA: β>0)"
di "     | AUS       CAN       FRA       DEU       ITA       JPN       NLD       SWE       CHE       GBR       USA"
di "-----+------------------------------------------------------------------------------------------------------"

local i = 0
foreach pays_i of local pays_list {
    local i = `i' + 1
    local ligne = "`pays_i' |"
    local j = 0
    foreach pays_j of local pays_list {
        local j = `j' + 1
        if "`pays_i'" == "`pays_j'" {
            local ligne = "`ligne'     —    "
        }
        else {
            local b    = beta_mat[`i',`j']
            local t    = tstat_mat[`i',`j']
            local p    = pval_mat[`i',`j']
            local star = ""
            if `p' < 0.10 local star = "*"
            local ligne = "`ligne' `: display %5.2f `b''`star'(`: display %5.2f `t'')"
        }
    }
    di "`ligne'"
}

di ""
local ligne_avg = "Avg  |"
local j = 0
foreach pays_j of local pays_list {
    local j = `j' + 1
    local sum_b = 0
    local n_b   = 0
    local i = 0
    foreach pays_i of local pays_list {
        local i = `i' + 1
        if "`pays_i'" != "`pays_j'" {
            local sum_b = `sum_b' + beta_mat[`i',`j']
            local n_b   = `n_b' + 1
        }
    }
    local avg_b = `sum_b' / `n_b'
    local ligne_avg = "`ligne_avg' `: display %6.2f `avg_b''    "
}
di "`ligne_avg'"

di _newline "Leadership score (p < 0.10) :"
local j = 0
foreach pays_j of local pays_list {
    local j = `j' + 1
    local score    = 0
    local beta_sum = 0
    local n_beta   = 0
    local i = 0
    foreach pays_i of local pays_list {
        local i = `i' + 1
        if "`pays_i'" != "`pays_j'" {
            local p        = pval_mat[`i',`j']
            local b        = beta_mat[`i',`j']
            local beta_sum = `beta_sum' + `b'
            local n_beta   = `n_beta' + 1
            if `p' < 0.10 local score = `score' + 1
        }
    }
    local beta_mean = `beta_sum' / `n_beta'
    di "`pays_j' | `score'/10 | avg beta = `: display %6.4f `beta_mean''"
}

********************************************************************************
* TABLE IV — POOLED MODEL · HC3
* β_j commun pour tous les pays i ≠ j
********************************************************************************

di _newline "TABLE IV — POOLED MODEL · HC3 · * p<0.10 (one-sided HA: β>0)"
di "Country j | b_pooled | t-stat | Sig"
di "----------|----------|--------|----"

foreach pays_j of local pays_list {
    quietly reg F.excess_return excess_return ///
        r_`pays_j' Tbill log_DY ///
        if Country != "`pays_j'", vce(hc3)
    local beta  = _b[r_`pays_j']
    local tstat = _b[r_`pays_j'] / _se[r_`pays_j']
    local pval  = ttail(e(df_r), `tstat')
    local sig = "—"
    if `pval' < 0.01      local sig = "***"
    else if `pval' < 0.05 local sig = "**"
    else if `pval' < 0.10 local sig = "*"
    di "`pays_j'        | `: display %7.4f `beta'' | `: display %6.2f `tstat'' | `sig'"
}

********************************************************************************
* TABLE VII — OUT-OF-SAMPLE R²(OS) · 1985:01–2010:12
* Benchmark : moyenne historique
* Concurrent : r(i,t+1) = β0 + β_USA·r_USA(t)
* Poolé      : β_USA commun pour tous i ≠ USA
* Clark-West (2007) · fenêtre récursive
********************************************************************************

local pays_order_VII "AUS CAN FRA DEU ITA JPN NLD SWE CHE GBR"

capture drop pred_hist pred_indiv pred_pool
gen double pred_hist  = .
gen double pred_indiv = .
gen double pred_pool  = .

local debut_eval = ym(1985,1)

foreach pays_i of local pays_order_VII {
    quietly levelsof time_id if Country=="`pays_i'" & ///
        time_id >= `debut_eval', local(tlist_eval)
    foreach t of local tlist_eval {
        quietly sum excess_return if Country=="`pays_i'" & time_id < `t'
        quietly replace pred_hist = r(mean) ///
            if Country=="`pays_i'" & time_id == `t'
        quietly reg F.excess_return r_USA ///
            if Country=="`pays_i'" & time_id < `t'
        quietly replace pred_indiv = _b[_cons] + _b[r_USA] * r_USA ///
            if Country=="`pays_i'" & time_id == `t'
        quietly reg F.excess_return r_USA ///
            if Country != "USA" & time_id < `t'
        quietly replace pred_pool = _b[_cons] + _b[r_USA] * r_USA ///
            if Country=="`pays_i'" & time_id == `t'
    }
}

di _newline "TABLE VII — OUT-OF-SAMPLE R²(OS) · 1985:01–2010:12"
di "Country | R2OS indiv | CW indiv | R2OS pooled | CW pooled"
di "--------|-----------|----------|-------------|----------"

local r2_sum_i = 0
local r2_sum_p = 0
local n_pos_i  = 0
local n_pos_p  = 0

foreach pays_i of local pays_order_VII {
    quietly {
        gen double e2_i = (F.excess_return - pred_indiv)^2 ///
            if Country=="`pays_i'" & time_id >= `debut_eval'
        gen double e2_p = (F.excess_return - pred_pool)^2 ///
            if Country=="`pays_i'" & time_id >= `debut_eval'
        gen double e2_h = (F.excess_return - pred_hist)^2 ///
            if Country=="`pays_i'" & time_id >= `debut_eval'
        gen double cw_i = e2_h - e2_i + (pred_indiv - pred_hist)^2 ///
            if Country=="`pays_i'" & time_id >= `debut_eval'
        gen double cw_p = e2_h - e2_p + (pred_pool  - pred_hist)^2 ///
            if Country=="`pays_i'" & time_id >= `debut_eval'
        sum e2_i if Country=="`pays_i'"
        local num_i = r(sum)
        sum e2_p if Country=="`pays_i'"
        local num_p = r(sum)
        sum e2_h if Country=="`pays_i'"
        local den  = r(sum)
        local nobs = r(N)
        sum cw_i if Country=="`pays_i'"
        local cw_t_i = r(mean) / (r(sd) / sqrt(`nobs'))
        sum cw_p if Country=="`pays_i'"
        local cw_t_p = r(mean) / (r(sd) / sqrt(`nobs'))
        drop e2_i e2_p e2_h cw_i cw_p
    }
    local r2_i = (1 - `num_i'/`den') * 100
    local r2_p = (1 - `num_p'/`den') * 100
    local r2_sum_i = `r2_sum_i' + `r2_i'
    local r2_sum_p = `r2_sum_p' + `r2_p'
    if `r2_i' > 0 local n_pos_i = `n_pos_i' + 1
    if `r2_p' > 0 local n_pos_p = `n_pos_p' + 1
    local sig_i = ""
    if `cw_t_i' > 1.282 local sig_i = "*"
    local sig_p = ""
    if `cw_t_p' > 1.282 local sig_p = "*"
    di "`pays_i'     | `: display %7.2f `r2_i''`sig_i' (`: display %4.2f `cw_t_i'') | `: display %7.2f `r2_p''`sig_p' (`: display %4.2f `cw_t_p'')"
}

di "Avg     | `: display %7.2f `=`r2_sum_i'/10'' | | `: display %7.2f `=`r2_sum_p'/10''"
di "Positive: `n_pos_i'/10 (indiv.)  `n_pos_p'/10 (pooled)"
di "* Clark-West t > 1.282 (p<0.10, one-sided)"

********************************************************************************
* FIN
********************************************************************************

log close