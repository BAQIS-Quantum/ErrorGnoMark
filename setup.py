from setuptools import setup, find_packages

setup(
    name="errorgnomark",
    version="0.2.0",  # 您可以自定义版本号
    packages=find_packages(),
    author="Chai Xudan", # 替换成您的名字
    author_email="chaixd@baqis.ac.cn", # 替换成您的邮箱
    description="A framework for quantum benchmarking and error characterization.",
    python_requires='>=3.8',
)