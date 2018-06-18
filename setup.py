import setuptools

import note_copy

requires = [
    'defusedxml',
    'requests',
    'six',
]

setuptools.setup(
    name='booru-note-copy',
    license='MIT',
    version=note_copy.__version__,
    description='copy translations between booru-style imageboards',
    author='Torsten Ostgard',
    url='https://github.com/torsten-ostgard/booru-note-copy',
    packages=setuptools.find_packages(exclude=['tests']),
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    install_requires=requires,
    entry_points={
        'console_scripts': [
            'note_copy = note_copy.note_copy:main',
        ],
    },
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Operating System :: OS Independent',
        'Topic :: Internet',
    ],
)
