
import os
import setuptools

requires = [
    'PyMySQL',
    'bcrypt>=1.1.1',
    'passlib>=1.7.1',
    'markdown>=2.6.1',
    'Pillow>=1.0',
    'faker',
    'markdown>=2.6.1'
]

here = os.path.abspath(os.path.dirname(__file__))

about = {}
with open(os.path.join(here, 'zoom', '__version__.py'), 'r', encoding='utf-8') as f:
    exec(f.read(), about)

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='ZoomFoundry',
    version=about['__version__'],
    author="DSI Labs",
    author_email="support@dsilabs.ca",
    description="A dynamic Web Framework that promotes modularity and rapid prototyping",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dsilabs/zoom",
    packages=['zoom'],
    install_requires=requires,
    entry_points={
        'console_scripts': [
            'zoom = zoom.cli.main:main'
        ]
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
   ],
   include_package_data=True,
)