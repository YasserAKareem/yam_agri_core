from setuptools import find_packages, setup

setup(
	name="yam_agri_core",
	version="1.1.0-dev",
	packages=find_packages(),
	include_package_data=True,
	description="YAM Agri Core — cereal supply chain quality and traceability platform",
	python_requires=">=3.10",
)
