from pathlib import Path

from setuptools import find_packages, setup


version = "0.0.1"
version_file = Path(__file__).parent / "yam_agri_core" / "__init__.py"
for line in version_file.read_text(encoding="utf-8").splitlines():
    if line.startswith("__version__"):
        version = line.split("=", 1)[1].strip().strip('"').strip("'")
        break

setup(
    name="yam_agri_core",
    version=version,
    packages=find_packages(),
    include_package_data=True,
    description="YAM Agri Core app (skeleton for tests and controllers)",
)
