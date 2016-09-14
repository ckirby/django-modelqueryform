=====
Usage
=====

For these examples we will use the following models::

   class MyModel(models.Model):
      age = models.IntegerField()
      employed = models.NullBooleanField()#Yes,No,Unknown
      degree = models.CharField(max_length = 2, choices = [["HS", "High School"], 
                                                           ["C", "College"],
                                                           ["G", "Graduate"],
                                                           ["PG", "Post Graduate"]]
                                )
   
   class MyInstitution(models.Model):
      name = models.CharField(max_length=50)
      accredited = models.BooleanField()
      
      def __str__(self):
         return "%s" % self.name
   

To use **django-modelqueryform** in a project import it into forms.py::

   import modelqueryform
    
Then we can use it as a Base class for your forms::

   class MyModelQueryForm(modelqueryform.ModelQueryForm):
       model = MyModel
       inclue = ['age','employed','degree']
       
Thats it! Instantiating MyModelQueryForm gives us a form with 3 widgets

* Age (\ :ref:`rangefield` using a \ :ref:`rangewidget`)
* Employed (`MultipleChoiceField` using a `CheckboxSelectMultiple` widget)
* Degree (`MultipleChoiceField` using a `CheckboxSelectMultiple` widget)

Once the form is POSTed to the view it is used to filter your model::

   query_form = MyModelQueryForm(request.POST)
   my_models = query_form.process()
   
`process([data_set=None])` generates a Q object which is a logical AND of the Q objects generated for each widget. 
It uses the resulting Q object to filter the associated model class.

.. note:: `process()` optionally accepts a QuerySet of a model class 'x' where isinstance(x, 'form model class') is True
   If no QuerySet is passed, the Q object will run against model.objects.all()
   
Using `pretty_print_query()` you get a dict() of the form {str(field.label): str(field values)} to parse into a template::

   query_form = MyModelQueryForm(request.POST)
   query_parameters = query_form.pretty_print_query()
     
Working with Relations
----------------------

**django-modelqueryform** can work with realtionship fields in two different ways, either following the relation or using the relationship field as a choice field.

Let's add a new field to `MyModel` from the example above::

   class MyModel(models.Model):
      ...
      institution = models.ForeignKey('MyInstitution')
      
If we want our users to be able to select for (non)-accredited institions we would instantiate the form like so::

   class MyModelQueryForm(modelqueryform.ModelQueryForm):
       model = MyModel
       inclue = ['age','employed','degree', 'institution__accredited']
       traverse_fields = ['institution',]

Alternatively we can use the relationship field as a `MultipleChoiceField`::

   class MyModelQueryForm(modelqueryform.ModelQueryForm):
       model = MyModel
       inclue = ['age','employed','degree', 'institution']
       
.. warning::
   To make the choices for a relationship field, **django-modelqueryform** does an `objects.distinct()` call. Be aware of the size of the resulting QuerySet


Defaults
--------

**djagno-modelqueryform** tries to provide meaningful default where it can.
Default widgets, Q objects, and print representation exist for model fields that 
are stored as numeric values or have choices (either defined or by default, ie. BooleanField(s))

.. note:: See :doc:`customization` for how to handle field type that don't have defaults

.. |multichoice| replace:: `MultipleChoiceField` / `CheckboxSelectMultiple`
.. |range| replace:: :ref:`rangefield` /  :ref:`rangewidget`
.. |multichoiceq| replace:: OR([field=value],...)
.. |rangeq| replace:: AND([field__gte=min],[field__lte=max]), OR(field__isnull=True)
.. |multichoicep| replace:: 'CHOICE1,CHOICE2,...CHOICEn'
.. |rangep| replace:: 'MIN - MAX [(include empty values)]'  

**Default Fields**

+----------------------------+-------------------+----------------+----------------------+
| Model Field                | Form Field/Widget | Q Object       | Print Representation |
|                            |                   |                |                      |
+============================+===================+================+======================+
| AutoField                  | |range|           | |rangeq|       | |rangep|             |
+----------------------------+-------------------+----------------+----------------------+
| BigIntegerField            | |range|           | |rangeq|       | |rangep|             |
+----------------------------+-------------------+----------------+----------------------+
| BinaryField                |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| BooleanField               | |multichoice|     | |multichoiceq| | |multichoicep|       |
+----------------------------+-------------------+----------------+----------------------+
| CharField                  |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| CommaSeparatedIntegerField |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| DateField                  |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| DateTimeField              |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| DecimalField               | |range|           | |rangeq|       | |rangep|             |
+----------------------------+-------------------+----------------+----------------------+
| EmailField                 |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| FileField                  |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| FilePathField              |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| FloatField                 | |range|           | |rangeq|       | |rangep|             |
+----------------------------+-------------------+----------------+----------------------+
| ImageField                 |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| IntegerField               | |range|           | |rangeq|       | |rangep|             |
+----------------------------+-------------------+----------------+----------------------+
| IPAddressField             |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| GenericIPAddressField      |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| NullBooleanField           | |multichoice|     | |multichoiceq| | |multichoicep|       |
+----------------------------+-------------------+----------------+----------------------+
| PositiveIntegerField       | |range|           | |rangeq|       | |rangep|             |
+----------------------------+-------------------+----------------+----------------------+
| PositiveSmallIntegerField  | |range|           | |rangeq|       | |rangep|             |
+----------------------------+-------------------+----------------+----------------------+
| SlugField                  |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| SmallIntegerField          | |range|           | |rangeq|       | |rangep|             |
+----------------------------+-------------------+----------------+----------------------+
| TextField                  |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| TimeField                  |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| URLField                   |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| ForeignKey                 | |multichoice|     | |multichoiceq| | |multichoicep|       |
+----------------------------+-------------------+----------------+----------------------+
| ManyToManyField            | |multichoice|     | |multichoiceq| | |multichoicep|       |
+----------------------------+-------------------+----------------+----------------------+
| OneToOneField              | |multichoice|     | |multichoiceq| | |multichoicep|       |
+----------------------------+-------------------+----------------+----------------------+



