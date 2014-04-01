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
        * **Required** The model class to query 
    * exclude
        * A list of fields to exclude. 
        * Named as they would be in the orm
        * AutoFields are automatically excluded
    * recursion_depth
        * Depth to follow ForeignKey and OneToOne fields
        * Default = 0
    * RANGE_TYPES
        * Field Types that will use RangeField
             * The RangeField and RangeWidget generate a minimum and maximum text field, as well as a checkbox to allow/disallow null values.
        * Default values are the numeric field types
            * BigIntegerField
            * DecimalField
            * FloatField
            * IntegerField
            * PositiveIntegerField
            * SmallIntegerField

and the methods:

    * process_model_query(data_set = None)
        * Runs the generated query against the sub-classes model type. If data_set is not defined it will run the query elements as a filter against ``model.objects.all()``
        * Returns a QuerySet[model type]
    * pretty_print_query()
        * Generates a human readable dict of the generated query values

Overview
--------

The generated form allows building a query with logical or of values in a single model field and logical and between fields

The generated form is made up of MultipleChoiceFields for each field in the model. The choices for the field will be the choices as defined on the model field if they exist. Otherwise it will pull the distinct values for that field and use them.

For fields that match the RANGE_TYPES types a RangeField will be generated.

ForeignKeyField and OneToOneField will cause recursion to the depth defined in recursion_depth. If recursion_depth has been met they will generate a MultipleChoiceField with the choices represented as (instance.pk, instance.__unicode__()) 
 
Usage Example
-------------

forms.py

::

    def TestModelQueryForm(ModelQueryForm):
        model = TestModel

views.py

::

    def test_model_query(request, pk = None):
        if request.method == 'POST':
            form = TestModelQueryForm(request.POST)
            if form.is_valid():
                if form.changed_data:
                    matched_query = form.process_model_query()
                    generated_query_dict = form.pretty_print_query
                return render_to_response('test_model_query_match.html', 
                                          {'matches' : matched_query, 'query' : generated_query_dict}, 
                                          context_instance = RequestContext(request)
                )
            
        else:
            form = TestModelQueryForm()

        return render_to_response('test_model_query.html', {'form':form})
 
    
