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
        "google-cloud-storage",
        "docker",
        "pytest",
        "dateutils",
        "parameterized"
     ],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    entry_points={
        'console_scripts' :[
            'runlab=ArchLab.runlab:main',
            'runlab.d=ArchLab.runlab_daemon:main',
            'labtool=ArchLab.labtool:main',
            'gradescope=ArchLab.GradeScope:main',
            'jextract=ArchLab.jextract:main',
            'get-cpu-freqs=ArchLab.CPUFreq:get_freqs_cli',
            'set-cpu-freq=ArchLab.CPUFreq:set_freq_cli',
            'hosttool=ArchLab.hosttool:main',
            'test-lab=ArchLab.testlab:main',
            'pretty-csv=ArchLab.csvpretty:main'
        ]
    }
)
