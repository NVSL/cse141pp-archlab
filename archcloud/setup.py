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
        "parameterized",
        "gradescope_utils",
        "packet-python",
        "flask",
        "requests",
        "matplotlib",
        "pyperformance"
     ],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    entry_points={
        'console_scripts' :[
            'runlab=ArchLab.runlab:main',
            'runlab.d=ArchLab.runlab_daemon:main',
            'runlab_proxy=ArchLab.runlab_proxy:main',
            'labtool=ArchLab.labtool:main',
            'gradescope=ArchLab.GradeScope:main',
            'jextract=ArchLab.jextract:main',
            'get-cpu-freqs=ArchLab.CPUFreq:get_freqs_cli',
            'set-cpu-freq=ArchLab.CPUFreq:set_freq_cli',
            'hosttool=ArchLab.hosttool:main',
            'test-lab=ArchLab.testlab:main',
            'pretty-csv=ArchLab.csvpretty:main',
            'merge-csv=ArchLab.csvmerge:main',
            'sort-csv=ArchLab.csvsort:main',
            'show-grades=ArchLab.showgrades:main',
            'qdcache=ArchLab.QDCache:main',
#            'gradelab=ArchLab.GradeLab:main'  # I dont think this exists.
        ]
    }
)
