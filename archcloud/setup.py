from setuptools import setup, find_packages

print(find_packages())

setup(
    name="ArchLab",
    version="1.0",
    install_requires = [
        "google-cloud",
        "google-cloud-pubsub",
        "docopt",
        "pyasn1",
        "google-cloud-datastore",
        "docker",
        "pytest"
     ],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    entry_points={
        'console_scripts' :[
            'runlab=ArchLab.run:main',
            'runlab.d=ArchLab.packet_server:main'
        ]
    }
)
