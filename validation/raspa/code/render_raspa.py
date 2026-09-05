from src.raspa_publication import publication_statistics
from src.main_figures import render_figure_06
from src.si_figures import render_s06
from src.package_tools import build_global_manifests

publication_statistics(write=True)
render_figure_06()
render_s06()
build_global_manifests()
print("\nDONE: publication-oriented Figure 6 and Figure S06 regenerated.")
print("See outputs/main/Figure_06 and outputs/si/Figure_S06.")
print("Validation: outputs/validation/RASPA_publication_validation.txt")
