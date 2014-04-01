#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_django-modelqueryform
------------

Tests for `django-modelqueryform` forms module.
"""

from django.test import TestCase

from .models import BaseModelForTest
from modelqueryform.widgets import RangeField
from django.forms.fields import MultipleChoiceField, Field, IntegerField
from tests.forms import FormTest, FormTestWithText, FormTestWithTextNamedMethod, \
    FormTestWithTextTypeMethod, PreferBuildNamedMethodForm, NoModelForm, \
    BadTrasverseForm, BadOverlapForm, GoodTraverseForm, RelatedAsChoicesForm, \
    FormTestWithTextNamedMethodAndProcessor, \
    FormTestWithTextTypeMethodAndProcessor
from django.core.exceptions import ImproperlyConfigured
from tests.models import RelatedModelForTest
from django.db.models.query_utils import Q
from collections import OrderedDict
try:
    from functools import reduce
except ImportError:  # Python < 3
    pass


def get_model_field(model, field_name):
    for field in model._meta.fields + model._meta.many_to_many:
        if field.name == field_name:
            return field
    return None


class TestModelqueryformForms(TestCase):
    def setUpBaseTest(self):
        RelatedModelForTest.objects.create(related_type=1)
        RelatedModelForTest.objects.create(related_type=2)
        RelatedModelForTest.objects.create(related_type=6)
        RelatedModelForTest.objects.create(related_type=2)

        BaseModelForTest.objects.create(integer=15,
                                        integer_with_choices=1,
                                        float=12.6,
                                        boolean=True,
                                        null_boolean=None,
                                        text="foo")
        BaseModelForTest.objects.create(integer=11,
                                        integer_with_choices=2,
                                        float=.11,
                                        boolean=False,
                                        null_boolean=True,
                                        text="bar")
        BaseModelForTest.objects.create(integer=12,
                                        integer_with_choices=3,
                                        float=9,
                                        boolean=True,
                                        null_boolean=False,
                                        text="baz")
        BaseModelForTest.objects.create(integer=19,
                                        integer_with_choices=2,
                                        float=16,
                                        boolean=True,
                                        null_boolean=None,
                                        text="qux")

        self.base_form = FormTest()

    def setUpRangeFieldFilter(self, field, val_dict):
        form = FormTest(val_dict)
        form.is_valid()
        range_q = form.get_range_field_filter(
                              field,
                              form.cleaned_data[field]
                          )
        return range_q

    def setUp(self):
        self.setUpBaseTest()

    def test_no_model_form(self):
        self.assertRaises(ImproperlyConfigured, NoModelForm)

    def test_multiplechoice_field_fails_without_choices(self):
        boolean_field = get_model_field(BaseModelForTest, 'boolean')
        self.assertRaises(ValueError,
                          self.base_form.get_multiplechoice_field,
                          boolean_field,
                          boolean_field.choices
        )

    def test_process_without_data_without_filters(self):
        form = FormTest({})
        form.is_valid()
        self.assertQuerysetEqual(form.process(),
                          [repr(r) for r in BaseModelForTest.objects.all()],
                          ordered=False)

    def test_process_empty_dataset(self):
        form = FormTest({})
        form.is_valid()
        self.assertRaises(ImproperlyConfigured,
                          form.process,
                          BaseModelForTest.objects.filter(integer=3)
        )

    def test_process_model_mismatch(self):
        form = FormTest({})
        form.is_valid()
        self.assertRaises(TypeError,
                          form.process,
                          RelatedModelForTest.objects.all()
        )

    def test_process_not_implemented(self):
        form = FormTestWithTextTypeMethod({'text': 'Test Text'})
        form.is_valid()
        self.assertRaises(NotImplementedError,
                          form.process
        )

    def test_process_filters(self):
        form = FormTest({'integer_with_choices': [1, 2]})
        form.is_valid()
        filtered_dataset = form.process()
        should_be = BaseModelForTest.objects.filter(Q(integer_with_choices=1) |
                                        Q(integer_with_choices=2))
        self.assertQuerysetEqual(filtered_dataset,
                          [repr(r) for r in should_be],
                          ordered=False
        )

        form = FormTest({'integer_0': 12, 'integer_1': 19})
        form.is_valid()
        filtered_dataset = form.process()
        should_be = BaseModelForTest.objects.filter(Q(integer__gte=12) &
                                        Q(integer__lte=19))
        self.assertQuerysetEqual(filtered_dataset,
                          [repr(r) for r in should_be],
                          ordered=False
        )

        form = FormTestWithTextNamedMethodAndProcessor({'text': "ba"})
        form.is_valid()
        filtered_dataset = form.process()
        should_be = BaseModelForTest.objects.filter(Q(text__icontains="ba"))
        self.assertQuerysetEqual(filtered_dataset,
                          [repr(r) for r in should_be],
                          ordered=False
        )

        form = FormTestWithTextTypeMethodAndProcessor({'text': "bar"})
        form.is_valid()
        filtered_dataset = form.process()
        should_be = BaseModelForTest.objects.filter(Q(text="bar"))
        self.assertQuerysetEqual(filtered_dataset,
                          [repr(r) for r in should_be],
                          ordered=False
        )

    def test_non_rel_traverse(self):
        self.assertRaises(TypeError, BadTrasverseForm)

    def test_text_field_raises_not_implemented(self):
        self.assertRaises(NotImplementedError, FormTestWithText)
        try:
            FormTestWithTextNamedMethod()
        except NotImplemented:
            self.fail("build_FIELD should allow a text field to pass initialization")
        try:
            FormTestWithTextTypeMethod()
        except NotImplemented:
            self.fail("build_type_FIELDTYPE should allow a text field to pass initialization")

    def test_include_traverse_overlap(self):
        self.assertRaises(ImproperlyConfigured, BadOverlapForm)

    def test_traverse_fields(self):
        traverse_form = GoodTraverseForm()
        self.assertEquals(len(traverse_form.fields),
                          5,
                          "All the included fields should be in the form"
        )
        self.assertIn('related_type__related_type',
                      traverse_form.fields.keys(),
                      'Recursive traversal should build the form name correctly'
        )

    def test_traverse_fields_process(self):
        test_model = BaseModelForTest.objects.first()
        test_model.related_type = RelatedModelForTest.objects.first()
        test_model.save()

        traverse_form = GoodTraverseForm({'related_type__related_type_0': 0,
                                         'related_type__related_type_1': 4})
        traverse_form.is_valid()
        filtered_dataset = traverse_form.process()
        should_be = BaseModelForTest.objects.filter(Q(related_type__related_type__gte=0) &
                                                    Q(related_type__related_type__lte=4))
        self.assertQuerysetEqual(filtered_dataset,
                          [repr(r) for r in should_be],
                          ordered=False
        )

    def test_get_related_no_choices(self):
        RelatedModelForTest.objects.all().delete()
        self.assertEqual(self.base_form._get_related_choices(
                                            get_model_field(
                                                    BaseModelForTest,
                                                    'many_related'
                                            )
                                        ),
                         [],
                         "ManyToMany field with no data should get a [] choices list"
        )

    def test_get_related_choices(self):
        r1, r2, r3, r4 = RelatedModelForTest.objects.all()
        self.assertEqual(self.base_form._get_related_choices(
                                            get_model_field(
                                                    BaseModelForTest,
                                                    'foreign_related'
                                            )
                                        ),
                         [[r1.pk, r1], [r2.pk, r2], [r3.pk, r3], [r4.pk, r4]],
                         "Related field should get choices [[pk, ModelObj]...]"
        )
        self.assertRaises(TypeError,
                          self.base_form._get_related_choices,
                          get_model_field(
                              BaseModelForTest,
                              'integer'
                          )
        )

    def test_multiplechoice_field_filter(self):
        self.assertIsNone(self.base_form.get_multiplechoice_field_filter(
                              'integer_with_choices', None
                          ),
                          "None for values should return None"
        )

        form = FormTest({'integer_with_choices':[1, 3]})
        form.is_valid()
        self.assertIsInstance(form.get_multiplechoice_field_filter(
                              'integer_with_choices',
                              form.cleaned_data['integer_with_choices']
                          ),
                          Q,
                          "Returns Q object"
        )

    def test_multiplechoice_field_print(self):
        form = FormTest({'integer_with_choices':[1, 3]})
        form.is_valid()
        self.assertEqual(form.get_multichoice_field_print(
                            form.fields['integer_with_choices'],
                            form.cleaned_data['integer_with_choices']
                            ),
                         "a,c",
                         "Should work for IntegerField with choices"
        )
        form = FormTest({'null_boolean': [None, False]})
        form.is_valid()
        self.assertEqual(form.get_multichoice_field_print(
                            form.fields['null_boolean'],
                            form.cleaned_data['null_boolean']
                            ),
                         "Unknown,No",
                         "Should work for NullBooleanField"
        )
        self.assertRaises(AttributeError,
                          form.get_multichoice_field_print,
                            form.fields['integer'],
                            form.cleaned_data['integer']
        )

    def test_range_field_filter(self):
        self.assertIsNone(self.base_form.get_range_field_filter(
                              'integer', None
                          ),
                          "None for values should return None"
        )

        diff_val = self.setUpRangeFieldFilter('integer', {'integer_0': 12,
                                                          'integer_1': 19}
                                             )
        self.assertIsInstance(diff_val,
                          Q,
                          "Returns Q object"
        )
        self.assertEquals(2, len(diff_val),
                          "Range Field with min < max should give a 2 element Q object"
        )

        with_allow_empty = self.setUpRangeFieldFilter('integer', {'integer_0': 12,
                                                                  'integer_1': 19,
                                                                  'integer_2': 'true'}
                                                      )
        self.assertEquals(2, len(with_allow_empty),
                          "Range Field with allow_empty should give a 2 element Q object"
        )

        same_val = self.setUpRangeFieldFilter('integer', {'integer_0': 12,
                                                          'integer_1': 12}
                                             )
        self.assertEquals(1, len(same_val),
                          "Range Field with min=max should give a 1 element Q object"
        )

    def test_range_field_print(self):
        form = FormTest({'integer_0': 12, 'integer_1': 19})
        form.is_valid()
        self.assertEqual(form.get_range_field_print(
                            form.fields['integer'],
                            form.cleaned_data['integer']
                            ),
                         "12 - 19",
                         "Should return the range"
        )

        form = FormTest({'integer_0': 12, 'integer_1': 19, "integer_2": True})
        form.is_valid()
        self.assertEqual(form.get_range_field_print(
                            form.fields['integer'],
                            form.cleaned_data['integer']
                            ),
                         "12 - 19 (include empty values)",
                         "Should return the range and note that empty values are included"
        )

    def test_pretty_print(self):
        form = FormTest({'integer_with_choices': [1, 3],
                         'boolean': [True, False],
                         'integer_0': 12, 'integer_1': 19, "integer_2": True})
        form.is_valid()
        pretty_print = form.pretty_print_query()

        self.assertIsInstance(pretty_print,
                              OrderedDict,
                              ".pretty_print_query returns an OrderedDict")
        self.assertEqual(list(pretty_print.keys()).sort(),
                         (['integer', 'boolean', 'integer_with_choices']).sort(),
                         "Should have .keys() that match the form field names")

        form = FormTestWithTextNamedMethod({'text': "blah"})
        form.is_valid()
        self.assertRaises(NotImplementedError, form.pretty_print_query)

        form = FormTestWithTextNamedMethodAndProcessor({'text': "blah"})
        form.is_valid()
        self.assertEqual(list(form.pretty_print_query().keys()).sort(),
                         (['text'].sort()),
                         "Should have a named print method")

        form = FormTestWithTextTypeMethodAndProcessor({'text': "blah"})
        form.is_valid()
        self.assertEqual(list(form.pretty_print_query().keys()).sort(),
                         (['text'].sort()),
                         "Should have a named print method")

    def test_related_as_choices(self):
        form = RelatedAsChoicesForm({})
        self.assertIn('foreign_related',
                      form.fields.keys(),
                      "Related fields in include are a form field"
        )

        self.assertIsInstance(form.fields["foreign_related"],
                              MultipleChoiceField,
                              "Related fields are turned into a MultipleChoiceField"
        )

    def test_build_query_from_filters(self):
        filters = {
                    "a": Q({1: 2}),
                    "b": Q({"val": [1, 6, 5]}),
                  }
        self.assertRaises(TypeError,
                          self.base_form.build_query_from_filters,
                          []
        )

        self.assertIsInstance(self.base_form.build_query_from_filters(filters),
                              Q,
                              "Should return a Q object "
        )
        filters['c'] = 7
        self.assertRaises(TypeError,
                          self.base_form.build_query_from_filters,
                          filters
        )

    def test_build_method_preference(self):
        pref_form = PreferBuildNamedMethodForm()
        try:
            type(pref_form.fields['integer_with_choices']) is IntegerField
        except:
            self.fail("integer_with_choices form field should be an IntegerField")

        try:
            type(pref_form.fields['integer']) is Field
        except:
            self.fail("integer form field should be a Field")

    def test_q_func_checker(self):
        from django.db.models.query_utils import Q
        import operator
        q_object = Q(**{'a':1})
        q_list = [q_object, q_object, q_object]
        self.assertTrue(self.base_form._test_filter_func_is_Q(q_object),
                        "A Q object should satisfy the test"
        )
        self.assertRaises(TypeError,
                          self.base_form._test_filter_func_is_Q,
                          q_list
        )
        self.assertTrue(self.base_form._test_filter_func_is_Q(
                            reduce(operator.or_, q_list)
                        ),
                        "[Q..] reduced with an operator should be Q"
        )

    def test_auto_form_fields(self):
        self.assertIsInstance(self.base_form.fields['integer'],
                              RangeField,
            "IntegerField should get a RangeField when there are no choices")
        self.assertIsInstance(self.base_form.fields['float'],
                              RangeField,
            "FloatField should get a RangeField when there are no choices")
        self.assertIsInstance(self.base_form.fields['integer_with_choices'],
                              MultipleChoiceField,
            "IntegerField should get a MultipleChoiceField when there are choices")
        self.assertIsInstance(self.base_form.fields['boolean'],
                              MultipleChoiceField,
            "BooleanField should get a MultipleChoiceField")
        self.assertIsInstance(self.base_form.fields['null_boolean'],
                              MultipleChoiceField,
            "NullBooleanField should get a MultipleChoiceField")

    def test_get_choices_from_distinct(self):
        distinct_call = BaseModelForTest.objects.distinct() \
                                                .order_by('integer') \
                                                .values_list('integer',
                                                             flat=True
                                                )
        self.assertEqual(len(self.base_form.get_choices_from_distinct('integer')),
                         len(distinct_call),
                         "There should be .distinct('integer') choices"
        )
        self.assertEqual(self.base_form.get_choices_from_distinct('integer'),
                         [[x, x] for x in distinct_call],
                         "Tuple key,values should be the same"
        )