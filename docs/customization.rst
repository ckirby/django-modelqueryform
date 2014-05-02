=============
Customization
=============

Customization is neccessary in **django-modelqueryform** in instances where the default FormField and filters are insufficient or not avilable for model fields that you want to expose to querying

.. note:: There are no defaults for Model fields that are represented as text and have no choices

You can customize three different aspects of **django-modelqueryform**
Each of these aspects can be customized either by Model Field or Model Field type

#. Form field builder

   * `build_FIELD(model_field)`
   * `build_type_FIELDTYPE(model_field)`
#. Filter builder

   * `filter_FIELD(field_name, values)`
   * `filter_type_FIELDTYPE(field_name, values)`
#. Pretty Print builder

   * `print_FIELD(field_name, values)`
   * `print_type_FIELDTYPE(field_name, values)`
   
.. Warning::
   For fields that have no default you must implement a field builder and a filter builder
   
For these examples we will use the following Model::

   class MyModel(models.Model):
      first_name = models.CharField(max_length=15)
      last_name = models.CharField(max_length=15)
      
And the following ModelQueryForm::

   class MyModelQueryForm(modelqueryform.ModelQueryForm):
       model = MyModel
       inclue = ['first_name','last_name']

Form Field Builder
------------------

This should return a form field object.

By Name::

   def build_first_name(model_field):
      return CharField(label=model_field.verbose_name,
                       max_length=model_field.max_length,
                       required=False
      )
      
.. note:: If this is all we customize for the example MyModelQueryForm it will raise a NotImplementedError because last_name does not have a field builder

By Type::

   def build_type_charfield(model_field):
      return CharField(label=model_field.verbose_name,
                       max_length=model_field.max_length,
                       required=False
      )

.. note:: No NotImplementedError because this covers the type for both first_name and last_name
   If there is a name based builder and a type based builder for a field the named builder takes precedence
   
Filter Builder
--------------

This should return a Q object.

By Name::

   def filter_first_name(field_name, values):
      return Q(**{field_name + '__iexact': values})

By Type::

   def filter_type_charfield(field_name, values):
      return Q(**{field_name + '__contains': values})
      
Pretty Print Builder
--------------------

By Name::

   def print_first_name(field_name, values):
      return "Matches %s" % values

By Type::

   def print_type_charfield(field_name, values):
      return "Contains %s" % values 
   




