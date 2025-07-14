from setuptools import setup, find_packages

setup(
    name='pyide',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'PyQt5',
    ],
    entry_points={
        'console_scripts': [
            'pyide = pyide.main:main',
        ],
    },
    author='Your Name',
    description='A lightweight Python IDE built using PyQt5',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Dheerendra-123/PythonIDE',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
)
