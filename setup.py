import os
from setuptools import setup, find_packages

README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name = 'django-modelqueryform',
    version = '0.5',
    description = 'Make a form to query against a model',
    long_description = README,
    
    author = 'Chaim Kirby',
    author_email = 'chaimkirby@gmail.com',
    url = 'http://github.com/ckirby/django-modelqueryform',
    license = 'BSD License', 
    
    packages=find_packages(),
    include_package_data = True,
    install_requires=['Django >=1.4'],
    
    classifiers = [
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License', 
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)