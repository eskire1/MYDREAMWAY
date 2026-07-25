from setuptools import setup

setup(
    name="apex-v5-global",
    version="1.0.0",
    description="Apex V5 Global – модульная торговая система",
    author="Your Name",
    packages=[
        "src", "src.agents", "src.data", "src.execution", "src.backtest",
        "src.utils", "src.runtime", "src.ui", "scripts",
    ],
    python_requires=">=3.10",
    install_requires=[
        "numpy==1.26.4",
        "pandas==2.2.0",
        "torch==2.2.0",
        "pytorch-lightning==2.1.3",
        "catboost==1.2.3",
        "pyyaml==6.0.1",
        "h5py==3.10.0",
        "pyarrow==15.0.0",
        "fastparquet==2024.2.0",
        "python-dotenv==1.0.1",
        "tqdm==4.66.1",
        "click==8.1.7",
        "colorama==0.4.6",
        "websocket-client==1.7.0",
        "requests==2.31.0",
        "ta==0.11.0",
        "loguru==0.7.2",
        "nicegui>=2.0.0",
        "scipy>=1.11.0",
        "matplotlib>=3.8.0",
        "ccxt>=4.2.0",
    ],
    entry_points={
        "console_scripts": [
            "apex-live = src.main:main",
            "apex-backtest = scripts.run_backtest:main",
            "apex-ui = src.ui.app:main",
        ],
    },
)