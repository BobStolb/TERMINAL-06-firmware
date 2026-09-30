"""Run 3d/case-pair/case_pair.py --extract with heights for rev B's new TS06-DRV footprints, which the
case model's FP_H table does not know yet (it would stop with a KeyError). Nothing in 3d/ is edited;
its outputs are restored with git checkout afterwards."""
import os, sys
ROOT = "/home/user/TERMINAL-06-firmware/.claude/worktrees/agent-af654573c23937790"
sys.path.insert(0, os.path.join(ROOT, "3d", "case-pair"))
os.chdir(ROOT)
import case_pair as C
C.FP_H.update({
    "TS06_R_Axial_MLT-0.5_P15.24mm": (4.7, "assumed", "МЛТ-0,5 lying, Ø4.2 body"),
    "TS06_L_Axial_D11.5mm_L22.9mm_P27.94mm": (12.0, "doc", "Bourns 5900-221-RC lying, Ø11.5 body"),
    "TS06_PinHeader_1x05_DS3231": (15.0, "assumed", "DS3231 mini (~14 x 16 x 12 mm with its socket) on a PLS-5, lying"),
    "TS06_DIP-16_W7.62mm_Socket_Oval": (8.5, "assumed", "DIP socket + chip"),
})
sys.argv = ["case_pair.py", "--extract"]
C.main()
