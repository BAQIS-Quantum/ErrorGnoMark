from setuptools import setup, find_packages
import os

# Function to read the dependencies from the requirements.txt file
def read_requirements():
    requirements = []
    if os.path.exists('requirements.txt'):
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            for line in f:
                # Remove comments and whitespace
                line = line.split('#')[0].strip()
                if line:
                    requirements.append(line)
    return requirements

# Function to read the long description (usually from README.md)
def read_long_description():
    if os.path.exists('README.md'):
        with open('README.md', 'r', encoding='utf-8') as f:
            return f.read()
    return "A Toolkit for Error Diagnosis and Benchmarking for Quantum Chip"

setup(
    name='ErrorGnoMark',  # Package name
    version='0.1.7',  # Initial version number
    author='Chai Xudan, Wang Jingbo, Xiaoxiao',  # Author/organization name
    author_email='chaixd@baqis.ac.cn',  # Contact email
    url='https://github.com/BAQIS-Quantum/ErrorGnoMark',  # Project repository URL
    description='A Toolkit for Error Diagnosis and Benchmarking for Quantum Chip',  # Short description
    long_description=read_long_description(),  # Detailed description from README.md
    long_description_content_type='text/markdown',  # Markdown format for the long description
    keywords=["errorgnomark", "quantum benchmarking", "quantum computing", "quantum operating system"],  # Keywords
    packages=find_packages(),  # Automatically discover all sub-packages
    install_requires=read_requirements(),  # Dependencies from requirements.txt
    python_requires='>=3.10',  # Minimum Python version
    include_package_data=True,  # Include additional files specified in MANIFEST.in
    license="Apache License 2.0",  # Standard license name
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Physics',
    ],
)
