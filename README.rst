=============================
django-modelqueryform
=============================

.. image:: https://badge.fury.io/py/django-modelqueryform.png
    :target: https://badge.fury.io/py/django-modelqueryform

.. image:: https://travis-ci.org/ckirby/django-modelqueryform.png?branch=master
    :target: https://travis-ci.org/ckirby/django-modelqueryform

.. image:: https://coveralls.io/repos/ckirby/django-modelqueryform/badge.png?branch=master
    :target: https://coveralls.io/r/ckirby/django-modelqueryform?branch=master

App for generating forms allowing users to build model queries

Documentation
-------------

The full documentation is at https://django-modelqueryform.readthedocs.org.

Quickstart
----------

Install django-modelqueryform::

    pip install django-modelqueryform

Then use it in a project::

    import modelqueryform

Features
--------
    
This will give you a Form class ModelQueryForm that must be subclassed

ModelQueryForm has the attributes:

    * model (Required)
        * The model class to query 
    * include []
        * A list of fields to include. 
        * Named as they would be in the orm
    * traverse_fields []
        * Relationship fields to follow the relationship to the next level
        * Follows ForeignKey, OneToOneField, ManyToManyField
        * If you use the __ (double underscore) orm notation in include, you must have the relationship field(s) in this list  
   
