import setuptools

import note_copy

requires = [
    'cached_property',
    'defusedxml',
    'requests',
    'six',
]
tests_require = [
    'coverage',
    'flake8',
    'tox',
    'vcrpy',
]

setuptools.setup(
    name='booru-note-copy',
    license='MIT',
    version=note_copy.__version__,
    description='copy translations between booru-style imageboards',
    author='Torsten Ostgard',
    url='https://github.com/torsten-ostgard/booru-note-copy',
    packages=setuptools.find_packages(exclude=['tests']),
    python_requires='>=3.4',
    install_requires=requires,
    entry_points={
        'console_scripts': [
            'note_copy = note_copy.cli:main',
        ],
    },
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Operating System :: OS Independent',
        'Topic :: Internet',
    ],
    test_suite='tests',
    tests_require=tests_require,
)
