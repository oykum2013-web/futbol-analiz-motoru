"""GPR Radar - Tork Pro 300 kurulum dosyası."""

from setuptools import find_packages, setup

setup(
    name="gpr-radar-tork-pro-300",
    version="1.0.0",
    description="Farmet Teknoloji Tork Pro 300 GPR Analiz Yazılımı",
    author="GPR Radar Team",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "PyQt5>=5.15.0",
        "numpy>=1.21.0",
        "scipy>=1.7.0",
        "pyqtgraph>=0.12.0",
        "pyserial>=3.5",
        "h5py>=3.0.0",
        "matplotlib>=3.5.0",
    ],
    extras_require={
        "3d": [
            "pyvista>=0.38.0",
            "pyvistaqt>=0.9.0",
            "vtk>=9.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "gpr-radar=main:main",
        ],
    },
)
