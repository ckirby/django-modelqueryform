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
   
   class MyInstitutions(models.Model):
      name = models.CharField(max_length=50)
      accredited = models.BooleanField()
      
      def __str__(self):
         return "%s" % self.name
   

To use django-modelqueryform in a project import it into your forms.py::

   import modelqueryform
    
Then you can use it as a Base class for your forms::

   class MyModelQueryForm(modelqueryform.ModelQueryForm):
       model = MyModel
       inclue = ['age','employed','degree']
       
Thats it! Instantiating MyModelQueryForm will give you a form with 3 widgets

* Age (\ :ref:`rangefield` using a \ :ref:`rangewidget`)
* Employed (`MultipleChoiceField` using a `CheckboxSelectMultiple` widget)
* Degree (`MultipleChoiceField` using a `CheckboxSelectMultiple` widget)

Once the form is POSTed to your view you can use it to filter your model::

   query_form = MyModelQueryForm(request.POST)
   my_models = query_form.process()
   
`process()` generates a Q object which is a logical AND of the Q objects generated for each widget. 
It uses the resulting Q object to filter the associated model class.

* `process()` optionally accepts a QuerySet of the model class used for the form

   * If no QuerySet is passed, the Q object will run against model.objects.all()
   
Using `pretty_print_query()` you get a dict() of the form {str(field.label): str(field values)} to parse into a template::

   query_form = MyModelQueryForm(request.POST)
   query_parameters = query_form.pretty_print_query()
     
     

Defaults
--------

**dajgno-modelqueryform** tries to provide meaningful default where it can.
Default widgets, Q objects, and print representation exist for model fields that 
are stored as numeric values or have choices (either defined or by default, ie. BooleanField(s))

.. |multichoice| replace:: `MultipleChoiceField` / `CheckboxSelectMultiple`
.. |range| replace:: :ref:`rangefield` /  :ref:`rangewidget`
.. |multichoiceq| replace:: OR([field=value],...)
.. |rangeq| replace:: AND([field__gte=min],[field__lte=max]), OR(field__isnull=True) 

**Default Fields**

+----------------------------+-------------------+----------------+----------------------+
| Model Field                | Form Field/Widget | Q Object       | Print Representation |
|                            |                   |                |                      |
+============================+===================+================+======================+
| AutoField                  | |range|           | |rangeq|       |                      |
+----------------------------+-------------------+----------------+----------------------+
| BigIntegerField            | |range|           | |rangeq|       |                      |
+----------------------------+-------------------+----------------+----------------------+
| BinaryField                |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| BooleanField               | |multichoice|     | |multichoiceq| |                      |
+----------------------------+-------------------+----------------+----------------------+
| CharField                  |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| CommaSeparatedIntegerField |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| DateField                  |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| DateTimeField              |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| DecimalField               | |range|           | |rangeq|       |                      |
+----------------------------+-------------------+----------------+----------------------+
| EmailField                 |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| FileField                  |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| FilePathField              |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| FloatField                 | |range|           | |rangeq|       |                      |
+----------------------------+-------------------+----------------+----------------------+
| ImageField                 |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| IntegerField               | |range|           | |rangeq|       |                      |
+----------------------------+-------------------+----------------+----------------------+
| IPAddressField             |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| GenericIPAddressField      |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| NullBooleanField           | |multichoice|     | |multichoiceq| |                      |
+----------------------------+-------------------+----------------+----------------------+
| PositiveIntegerField       | |range|           | |rangeq|       |                      |
+----------------------------+-------------------+----------------+----------------------+
| PositiveSmallIntegerField  | |range|           | |rangeq|       |                      |
+----------------------------+-------------------+----------------+----------------------+
| SlugField                  |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| SmallIntegerField          | |range|           | |rangeq|       |                      |
+----------------------------+-------------------+----------------+----------------------+
| TextField                  |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| TimeField                  |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| URLField                   |                   |                |                      |
+----------------------------+-------------------+----------------+----------------------+
| ForeignKey                 | |multichoice|     | |multichoiceq| |                      |
+----------------------------+-------------------+----------------+----------------------+
| ManyToManyField            | |multichoice|     | |multichoiceq| |                      |
+----------------------------+-------------------+----------------+----------------------+
| OneToOneField              | |multichoice|     | |multichoiceq| |                      |
+----------------------------+-------------------+----------------+----------------------+



