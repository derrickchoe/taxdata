import numpy as np
import pandas as pd
from cylp.cy import CyClpSimplex
from cylp.py.modeling.CyLPModel import CyLPArray, CyLPModel

def solve_lp_for_year(puf, Stage_I_factors, Stage_II_targets, year, tol):
    if int(year) > 2012:
        med = pd.read_csv("/Users/derrick.cho/Desktop/taxdata/puf_data/med" + year + '.csv')
    else:
        med = pd.read_csv('/Users/derrick.cho/Desktop/taxdata/puf_data/med2013.csv')
    puf = puf.join(med.drop('c00100',  axis = 1))
    puf_length = len(puf.s006)

    print("Preparing coefficient matrix for year {} .....".format(year))

    s006 = np.where(puf.e02400 > 0,
                    puf.s006 * Stage_I_factors[year]["APOPSNR"] / 100,
                    puf.s006 * Stage_I_factors[year]["ARETS"] / 100)

    single_return = np.where((puf.mars == 1) & (puf.filer == 1), s006, 0)
    joint_return = np.where(((puf.mars == 2) | (puf.mars == 3)) &
                            (puf.filer == 1), s006, 0)
    hh_return = np.where((puf.mars == 4) & (puf.filer == 1), s006, 0)
    return_w_SS = np.where((puf.e02400 > 0) & (puf.filer == 1), s006, 0)

    dependent_exempt_num = (puf.xocah + puf.xocawh +
                            puf.xoodep + puf.xopar) * s006
    interest = puf.e00300 * s006
    dividend = puf.e00600 * s006
    biz_income = np.where(puf.e00900 > 0, puf.e00900, 0) * s006
    biz_loss = np.where(puf.e00900 < 0, -puf.e00900, 0) * s006
    cap_gain = np.where((puf.p23250 + puf.p22250) > 0,
                        puf.p23250 + puf.p22250, 0) * s006
    annuity_pension = puf.e01700 * s006
    sch_e_income = np.where(puf.e02000 > 0, puf.e02000, 0) * s006
    sch_e_loss = np.where(puf.e02000 < 0, -puf.e02000, 0) * s006
    ss_income = np.where(puf.filer == 1, puf.e02400, 0) * s006
    unemployment_comp = puf.e02300 * s006

    # Wage distribution
    wage_1 = np.where(puf.e00100 <= 0, puf.e00200, 0) * s006
    wage_2 = np.where((puf.e00100 > 0) & (puf.e00100 <= 10000),
                      puf.e00200, 0) * s006
    wage_3 = np.where((puf.e00100 > 10000) & (puf.e00100 <= 20000),
                      puf.e00200, 0) * s006
    wage_4 = np.where((puf.e00100 > 20000) & (puf.e00100 <= 30000),
                      puf.e00200, 0) * s006
    wage_5 = np.where((puf.e00100 > 30000) & (puf.e00100 <= 40000),
                      puf.e00200, 0) * s006
    wage_6 = np.where((puf.e00100 > 40000) & (puf.e00100 <= 50000),
                      puf.e00200, 0) * s006
    wage_7 = np.where((puf.e00100 > 50000) & (puf.e00100 <= 75000),
                      puf.e00200, 0) * s006
    wage_8 = np.where((puf.e00100 > 75000) & (puf.e00100 <= 100000),
                      puf.e00200, 0) * s006
    wage_9 = np.where((puf.e00100 > 100000) & (puf.e00100 <= 200000),
                      puf.e00200, 0) * s006
    wage_10 = np.where((puf.e00100 > 200000) & (puf.e00100 <= 500000),
                       puf.e00200, 0) * s006
    wage_11 = np.where((puf.e00100 > 500000) & (puf.e00100 <= 1000000),
                       puf.e00200, 0) * s006
    wage_12 = np.where(puf.e00100 > 1000000, puf.e00200, 0) * s006
    # med1 = np.where(puf.med1 == 1, s006, 0)
    med2 = np.where(puf.med2 == 1, s006, 0)
    med3 = np.where(puf.med3 == 1, s006, 0)
    med4 = np.where(puf.med4 == 1, s006, 0)
    med5 = np.where(puf.med5 == 1, s006, 0)
    med6 = np.where(puf.med6 == 1, s006, 0)

    # med_exp = np.where((puf.med == 1), puf.e17500, 0) * s006

    # Set up the matrix
    One_half_LHS = np.vstack((single_return, joint_return, hh_return,
                              return_w_SS,
                              dependent_exempt_num, interest, dividend,
                              biz_income, biz_loss, cap_gain, annuity_pension,
                              sch_e_income, sch_e_loss,
                              ss_income, unemployment_comp,
                              wage_1, wage_2, wage_3, wage_4, wage_5,
                              wage_6, wage_7, wage_8, wage_9, wage_10,
                              wage_11, wage_12, med2, med3, med4,
                              med5, med6))

    # Coefficients for r and s
    A1 = np.matrix(One_half_LHS)
    A2 = np.matrix(-One_half_LHS)

    print("Preparing targets for year {} .....".format(year))

    APOPN = Stage_I_factors[year]["APOPN"]

    b = []

    b.append(Stage_II_targets[year]["Single Returns"] - single_return.sum())
    b.append(Stage_II_targets[year]["Joint Returns"] - joint_return.sum())
    target_name = "Head of Household Returns"
    b.append(Stage_II_targets[year][target_name] - hh_return.sum())
    target_name = "Number of Returns w/ Gross Security Income"
    b.append(Stage_II_targets[year][target_name] - return_w_SS.sum())
    target_name = "Number of Dependent Exemptions"
    b.append(Stage_II_targets[year][target_name] - dependent_exempt_num.sum())

    AINTS = Stage_I_factors[year]["AINTS"]
    INTEREST = (Stage_II_targets[year]["Taxable Interest Income"] *
                APOPN / AINTS * 1000 - interest.sum())

    ADIVS = Stage_I_factors[year]["ADIVS"]
    DIVIDEND = (Stage_II_targets[year]["Ordinary Dividends"] *
                APOPN / ADIVS * 1000 - dividend.sum())

    ASCHCI = Stage_I_factors[year]["ASCHCI"]
    BIZ_INCOME = (Stage_II_targets[year]["Business Income (Schedule C)"] *
                  APOPN / ASCHCI * 1000 - biz_income.sum())

    ASCHCL = Stage_I_factors[year]["ASCHCL"]
    BIZ_LOSS = (Stage_II_targets[year]["Business Loss (Schedule C)"] *
                APOPN / ASCHCL * 1000 - biz_loss.sum())

    ACGNS = Stage_I_factors[year]["ACGNS"]
    CAP_GAIN = (Stage_II_targets[year]["Net Capital Gains in AGI"] *
                APOPN / ACGNS * 1000 - cap_gain.sum())

    ATXPY = Stage_I_factors[year]["ATXPY"]
    target_name = "Taxable Pensions and Annuities"
    ANNUITY_PENSION = (Stage_II_targets[year][target_name] *
                       APOPN / ATXPY * 1000 - annuity_pension.sum())

    ASCHEI = Stage_I_factors[year]["ASCHEI"]
    target_name = "Supplemental Income (Schedule E)"
    SCH_E_INCOME = (Stage_II_targets[year][target_name] *
                    APOPN / ASCHEI * 1000 - sch_e_income.sum())

    ASCHEL = Stage_I_factors[year]["ASCHEL"]
    SCH_E_LOSS = (Stage_II_targets[year]["Supplemental Loss (Schedule E)"] *
                  APOPN / ASCHEL * 1000 - sch_e_loss.sum())

    ASOCSEC = Stage_I_factors[year]["ASOCSEC"]
    APOPSNR = Stage_I_factors[year]["APOPSNR"]
    SS_INCOME = (Stage_II_targets[year]["Gross Social Security Income"] *
                 APOPSNR / ASOCSEC * 1000 - ss_income.sum())

    AUCOMP = Stage_I_factors[year]["AUCOMP"]
    UNEMPLOYMENT_COMP = (Stage_II_targets[year]["Unemployment Compensation"] *
                         APOPN / AUCOMP * 1000 - unemployment_comp.sum())

    AWAGE = Stage_I_factors[year]["AWAGE"]
    target_name = "Wages and Salaries: Zero or Less"
    WAGE_1 = (Stage_II_targets[year][target_name] *
              APOPN / AWAGE * 1000 - wage_1.sum())
    target_name = "Wages and Salaries: $1 Less Than $10,000"
    WAGE_2 = (Stage_II_targets[year][target_name] *
              APOPN / AWAGE * 1000 - wage_2.sum())
    target_name = "Wages and Salaries: $10,000 Less Than $20,000"
    WAGE_3 = (Stage_II_targets[year][target_name] *
              APOPN / AWAGE * 1000 - wage_3.sum())
    target_name = "Wages and Salaries: $20,000 Less Than $30,000"
    WAGE_4 = (Stage_II_targets[year][target_name] *
              APOPN / AWAGE * 1000 - wage_4.sum())
    target_name = "Wages and Salaries: $30,000 Less Than $40,000"
    WAGE_5 = (Stage_II_targets[year][target_name] *
              APOPN / AWAGE * 1000 - wage_5.sum())
    target_name = "Wages and Salaries: $40,000 Less Than $50,000"
    WAGE_6 = (Stage_II_targets[year][target_name] *
              APOPN / AWAGE * 1000 - wage_6.sum())
    target_name = "Wages and Salaries: $50,000 Less Than $75,000"
    WAGE_7 = (Stage_II_targets[year][target_name] *
              APOPN / AWAGE * 1000 - wage_7.sum())
    target_name = "Wages and Salaries: $75,000 Less Than $100,000"
    WAGE_8 = (Stage_II_targets[year][target_name] *
              APOPN / AWAGE * 1000 - wage_8.sum())
    target_name = "Wages and Salaries: $100,000 Less Than $200,000"
    WAGE_9 = (Stage_II_targets[year][target_name] *
              APOPN / AWAGE * 1000 - wage_9.sum())
    target_name = "Wages and Salaries: $200,000 Less Than $500,000"
    WAGE_10 = (Stage_II_targets[year][target_name] *
               APOPN / AWAGE * 1000 - wage_10.sum())
    target_name = "Wages and Salaries: $500,000 Less Than $1 Million"
    WAGE_11 = (Stage_II_targets[year][target_name] *
               APOPN / AWAGE * 1000 - wage_11.sum())
    target_name = "Wages and Salaries: $1 Million and Over"
    WAGE_12 = (Stage_II_targets[year][target_name] *
               APOPN / AWAGE * 1000 - wage_12.sum())
    # target_name = 'Returns Taking Medical Expense Deduction U15'
    # MED1 = Stage_II_targets[year][target_name] - med1.sum()
    target_name = 'Returns Taking Medical Expense Deduction U30'
    MED2 = Stage_II_targets[year][target_name] - med2.sum()
    target_name = 'Returns Taking Medical Expense Deduction 30U50'
    MED3 = Stage_II_targets[year][target_name] - med3.sum()
    target_name = 'Returns Taking Medical Expense Deduction 50U100'
    MED4 = Stage_II_targets[year][target_name] - med4.sum()
    target_name = 'Returns Taking Medical Expense Deduction 100U200'
    MED5 = Stage_II_targets[year][target_name] - med5.sum()
    target_name = 'Returns Taking Medical Expense Deduction 200'
    MED6 = Stage_II_targets[year][target_name] - med6.sum()




    temp = [INTEREST, DIVIDEND, BIZ_INCOME, BIZ_LOSS, CAP_GAIN,
            ANNUITY_PENSION, SCH_E_INCOME, SCH_E_LOSS, SS_INCOME,
            UNEMPLOYMENT_COMP,
            WAGE_1, WAGE_2, WAGE_3, WAGE_4, WAGE_5, WAGE_6,
            WAGE_7, WAGE_8, WAGE_9, WAGE_10, WAGE_11, WAGE_12, MED2,
            MED3, MED4, MED5, MED6]
    for m in temp:
        b.append(m)

    targets = CyLPArray(b)
    print("Targets for year {} are:".format(year))
    print(targets)

    LP = CyLPModel()

    r = LP.addVariable("r", puf_length)
    s = LP.addVariable("s", puf_length)

    print("Adding constraints for year {} .....".format(year))
    LP.addConstraint(r >= 0, "positive r")
    LP.addConstraint(s >= 0, "positive s")
    LP.addConstraint(r + s <= tol, "abs upperbound")

    c = CyLPArray((np.ones(puf_length)))
    LP.objective = c * r + c * s

    LP.addConstraint(A1 * r + A2 * s == targets, "Aggregates")

    print("Setting up the LP model for year {} .....".format(year))
    model = CyClpSimplex(LP)

    print("Solving LP for year {} .....".format(year))
    model.initialSolve()

    print("DONE solving LP for year {}".format(year))
    z = np.empty([puf_length])
    z = (1.0 + model.primalVariableSolution["r"] -
         model.primalVariableSolution["s"]) * s006 * 100
    return z
