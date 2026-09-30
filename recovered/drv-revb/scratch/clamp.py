# OV clamp tolerance analysis: HV185 -> zener string -> R75 -> base of VT2, R76 base-emitter.
def setpoint(v5, r_top, r64, rp, r69, r70):
    vref = v5 * r70 / (r69 + r70)
    return vref * (1 + r_top / (r64 + rp))


nom = setpoint(5.0, 1500e3, 18e3, 0, 10e3, 10e3)
worst = max(setpoint(v5, 1500e3 * a, 18e3 * b, 0, 10e3 * c, 10e3 * d)
            for v5 in (5.0 * 1.03,) for a in (0.99, 1.01) for b in (0.99, 1.01) for c in (0.99, 1.01) for d in (0.99, 1.01))
print(f"set point at the trimmer's top end: nominal {nom:.1f} V, worst (1% parts, +5V +3%) {worst:.1f} V")
TOL, KNEE, TC = 0.05, 0.015, 0.001       # 1N47xxA +-5 %, the knee at ~0.1 mA vs Izt, +0.1 %/K
T_LO, T_HI = 10, 60                       # board temperature range, degC
R75, R76 = 100e3, 10e3
for combo in ((82, 82, 75), (100, 100, 33), (82, 75, 75), (100, 100, 39), (91, 82, 68)):
    N = sum(combo)
    vz_lo = N * (1 - TOL) * (1 - KNEE) * (1 + TC * (T_LO - 25))
    i_on = 0.45 / (R76 * 1.01)
    v_on = vz_lo + 0.45 + i_on * R75 * 0.99
    v_typ = N * (1 - KNEE) + 0.55 + 0.55 / R76 * R75
    vz_hi = N * (1 + TOL) * (1 + TC * (T_HI - 25))
    i_full = 0.7 / (R76 * 0.99) + 1.83e-3 / 70
    v_full = vz_hi + 0.7 + i_full * R75 * 1.01
    print(f"{'+'.join(map(str, combo)):>12} = {N} V: zener lo {vz_lo:.1f} hi {vz_hi:.1f}; onset min {v_on:.1f}  typ {v_typ:.1f}  full clamp max {v_full:.1f} V; i_full {i_full*1e6:.0f} uA")
print("leakage 5 uA x 10k =", 5e-6 * 10e3, "V at the base; 20 uA hot:", 20e-6 * 10e3)
print("NPN must sink", round((5 - 0.2) / 2.2e3 * 1e3, 2), "mA from D9 through R66")
