from django.db.models.query_utils import Q
from django.forms import CharField, Field, IntegerField

from modelqueryform.forms import ModelQueryForm
from .models import BaseModelForTest


class NoModelForm(ModelQueryForm):
    pass


class FormTest(ModelQueryForm):
    model = BaseModelForTest
    include = ['integer', 'integer_with_choices', 'float', 'boolean', 'null_boolean']


class FormTestWithText(ModelQueryForm):
    model = BaseModelForTest
    include = ['text']


class FormTestWithTextNamedMethod(ModelQueryForm):
    model = BaseModelForTest
    include = ['text']

    def build_text(self, field):
        return CharField(label=field.name)


class FormTestWithTextNamedMethodAndProcessor(FormTestWithTextNamedMethod):
    def filter_text(self, field, value):
        return Q(**{field + "__icontains": value})

    def print_text(self, field, values):
        return values


class FormTestWithTextTypeMethod(ModelQueryForm):
    model = BaseModelForTest
    include = ['text']

    def build_type_textfield(self, field):
        return Field(label=field.name)


class FormTestWithTextTypeMethodAndProcessor(FormTestWithTextTypeMethod):
    def filter_type_textfield(self, field, value):
        return Q(**{field: value})

    def print_type_textfield(self, field, values):
        return values


class PreferBuildNamedMethodForm(ModelQueryForm):
    model = BaseModelForTest
    include = ['integer', 'integer_with_choices', 'float', 'boolean', 'null_boolean']

    def build_integer_with_choices(self, field):
        return IntegerField(label=field.name)

    def build_type_integerfield(self, field):
        return Field(label=field.name)


class GoodTraverseForm(ModelQueryForm):
    model = BaseModelForTest
    include = ['integer',
               'float',
               'related_type__related_type',
               'foreign_related__related_type',
               'many_related__related_type'
               ]


class RelatedAsChoicesForm(ModelQueryForm):
    model = BaseModelForTest
    include = ['foreign_related']

