# -*- coding: utf-8 -*-

import setuptools

try:
    with open("README.md", "r") as fh:
        long_description = fh.read()
except:
    long_description = "README.md not found"

try:
    exec(open('laporte_mqtt/version.py').read())
except:
    __version__ = 'v.not.found'

try:
    with open('requirements.txt') as fh:
        required = fh.read().splitlines()
except:
    required = []

setuptools.setup(name="laporte-mqtt",
                 version=__version__,
                 author="Václav Vinklát",
                 author_email="vin@email.cz",
                 description="MQTT connector for Laporte.",
                 long_description=long_description,
                 long_description_content_type="text/markdown",
                 url="https://github.com/vinklat/laporte-mqtt",
                 include_package_data=True,
                 zip_safe=False,
                 packages=setuptools.find_packages(),
                 install_requires=required,
                 classifiers=[
                     "Programming Language :: Python :: 3",
                     "License :: OSI Approved :: MIT License",
                     "Operating System :: OS Independent",
                 ],
                 entry_points={
                     'console_scripts': ['laporte-mqtt=laporte_mqtt.main:main'],
                 })
