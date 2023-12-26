
import os
import setuptools

here = os.path.abspath(os.path.dirname(__file__))

about = {}
with open(os.path.join(here, 'zoom', '__version__.py'), 'r', encoding='utf-8') as f:
    exec(f.read(), about)  # pylint: disable=exec-used

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as f:
    requires = [l for l in f.read().splitlines() if not l.startswith('#')]

setuptools.setup(
    name='ZoomFoundry',
    version=about['__version__'],
    author="DSI Labs",
    author_email="support@dsilabs.ca",
    description="A dynamic Web Framework that promotes modularity and rapid prototyping",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ZoomFoundry/ZoomFoundry",
    packages=['zoom'],
    install_requires=requires,
    entry_points={
        'console_scripts': [
            'zoom = zoom.__main__:main'
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
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    include_package_data=True,
)
