import os, numpy as np, openpyxl, pytest
import file_io
from solver import StackRange, fetchstack, run_solve

TEMPLATE=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"TolStack_Template.xlsx")

@pytest.mark.skipif(not os.path.exists(TEMPLATE), reason="template not built")
def test_read_solve_write_embed(tmp_path):
    run=os.path.join(tmp_path,"run.xlsx"); import shutil; shutil.copy(TEMPLATE,run)
    grid,start=file_io.read_workbook(run,"Example")
    s=run_solve(fetchstack(StackRange(),data=grid,startcell=start))
    assert s is not None and np.all(np.isfinite(s.uplusNsigma))
    file_io.write_results(run,"Example",s.result_cells,
                          {"RESULT":s.uplusNsigma,"MU":s.mu,"SIGMA":s.sigma,"WORST_CASE":s.worst_case})
    # embed then re-embed -> replaced, not stacked
    png=os.path.join(tmp_path,"p.png")
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    plt.figure(); plt.plot([0,1]); plt.savefig(png); plt.close()
    file_io.embed_images(run,"Example",[png]); file_io.embed_images(run,"Example",[png])
    assert len(openpyxl.load_workbook(run)["Example"]._images)==1
