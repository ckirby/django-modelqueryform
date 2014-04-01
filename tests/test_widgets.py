#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_django-modelqueryform
------------

Tests for `django-modelqueryform` widgets module.
"""

from django.test import TestCase

from modelqueryform.widgets import RangeWidget, RangeField
from django.forms.widgets import TextInput, CheckboxInput
from tests.models import BaseModelForTest
from django.core.exceptions import ValidationError


def render_widgets(widgets):
    rendered = []
    for idx, sub in enumerate(widgets):
        rendered.append(sub.render(idx, None, sub.attrs))

    return rendered


class TestModelqueryformWidgets(TestCase):
    def setUp(self):
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

    def test_widget(self):
        empty_widget = RangeWidget()
        self.assertListEqual([type(TextInput()), type(TextInput())],
                             [type(w) for w in empty_widget.widgets],
                             "Should be 2 TextInput widgets"
        )

        no_null_widget = RangeWidget(attrs={"min": 11, "max": 19})
        self.assertListEqual([TextInput(attrs={"min":11, "max":19}).attrs,
                              TextInput(attrs={"min":11, "max":19}).attrs],
                             [w.attrs for w in no_null_widget.widgets],
                             "Text Input should get attrs"
        )

        self.assertHTMLEqual('<input max="19" min="11" name="0" type="text" />'
                             '<input max="19" min="11" name="1" type="text" />',
                             no_null_widget.format_output(
                                render_widgets(
                                    no_null_widget.widgets)),
                             "Should get two input tags with same attrs and names 0 and 1"
        )

        null_no_attrs_widget = RangeWidget(allow_null=True)
        self.assertListEqual([type(TextInput()),
                              type(TextInput()),
                              type(CheckboxInput())
                             ],
                             [type(w) for w in null_no_attrs_widget.widgets],
                             "Should be 2 TextInput widgets"
        )

        null_attrs_widget = RangeWidget(allow_null=True, attrs={"min": 11, "max": 19})
        self.assertListEqual([TextInput(attrs={"min":11, "max":19}).attrs,
                              TextInput(attrs={"min":11, "max":19}).attrs,
                              {}
                             ],
                             [w.attrs for w in null_attrs_widget.widgets],
                             "Text Input should get attrs, Checkbox should not"
        )

        self.assertHTMLEqual('<input max="19" min="11" name="0" type="text" />'
                             '<input max="19" min="11" name="1" type="text" />'
                             '<br/> Include Empty values '
                             '<input name="2" type="checkbox">',
                             null_attrs_widget.format_output(
                                render_widgets(
                                    null_attrs_widget.widgets)),
                             "Should get two input text with same attrs and names 0 and 1 "
                             "and one input checkbox with name 2"
        )

        self.assertListEqual([None, None],
                             empty_widget.decompress(None),
                             "No values should decompress to [None, None]"
        )

        self.assertListEqual([11, 19],
                             no_null_widget.decompress({"min": 11, "max": 19}),
                             "Min and Max decompress to [11, 19]"
        )

        self.assertListEqual([11, 19, True],
                             null_attrs_widget.decompress({"min": 11,
                                                           "max": 19,
                                                           'allow_empty': True}),
                             "Min, Max, and Allow_Empty decompress to [11, 19, True]"
        )

    def test_field(self):
        field = RangeField(BaseModelForTest, 'integer')
        self.assertRaises(ValidationError,
                          field.validate,
                          {"min": 19, "max": 12}
        )

        self.assertRaises(ValidationError,
                          field.to_python,
                          {"min": "Nineteen", "max": 12}
        )

        self.assertDictEqual(field.to_python({"min": "12", "max": "19"}),
                             {"min": 12, "max": 19},
                             "Cast ints"
        )

        self.assertDictEqual(field.to_python({"min": "12.2", "max": "19.65"}),
                             {"min": 12.2, "max": 19.65},
                             "Cast Floats"
        )
