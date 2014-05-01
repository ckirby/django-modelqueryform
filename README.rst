=====================
django-modelqueryform
=====================

.. image:: https://badge.fury.io/py/django-modelqueryform.png
    :target: https://badge.fury.io/py/django-modelqueryform

.. image:: https://travis-ci.org/ckirby/django-modelqueryform.png?branch=master
    :target: https://travis-ci.org/ckirby/django-modelqueryform

.. image:: https://coveralls.io/repos/ckirby/django-modelqueryform/badge.png?branch=master
    :target: https://coveralls.io/r/ckirby/django-modelqueryform?branch=master

**django-modelqueryform** is a flexible app that helps you build Q object generating forms.

It is a great tool if you want you users to be able to do filtered searches against your models.

Documentation
-------------

The full documentation is at https://django-modelqueryform.readthedocs.org.

Requirements
------------

* Django 1.5.1+
* Python 2.7, 3.3  

   
Features
--------
    
* Useable default FormFields for ModelFields that:

    * Have `.choices` defined or are inherently made of choices (ie. `BooleanField` and `NullBooleanField`)
    * Are represented as numeric types (eg. `IntegerField`, `FloatField`, etc.)
    * Text backed fields need code written to handle them. That is easy though, because:
 
* Creation of FormFields, Q objects, and User readable query terms are completely customizable. You can target ModelFields:

    * By name (If the field has specific requirements)
    * By field type (Use the same widget or Q object builder for all `CharField`\ s)
    
* Can follow Model relationships or treat relationship fields as `.choices`
* Provides a new Field and Widget (`RangeField`, `RangeWidget`). These allow users to generate a `__gte`, `__lte` pair for the orm, optionally also including an `__isnull`

    * RangeField
        
        * Dynamically generates min and max boundaries. (Aggregate `Min` and `Max` on the model field)
        * If `null=True` on the ModelField allows user to indicate if they want to include null values in the query
    
    * RangeWidget
        
        * Returns a `MultiWidget` with 2 `NumberInput` widgets (with min and max attributes)         
     