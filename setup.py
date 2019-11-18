import setuptools
from pathlib import Path

import note_copy

readme_file = Path(__file__).parent.resolve()/'README.md'
with open(str(readme_file), 'r') as f:
    long_description = f.read()

requires = [
    'beautifulsoup4',
    'cached_property',
    'defusedxml',
    'requests',
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
    python_requires='>=3.5',
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
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Operating System :: OS Independent',
        'Topic :: Internet',
    ],
    long_description=long_description,
    long_description_content_type='text/markdown',
    test_suite='tests',
    tests_require=tests_require,
)
