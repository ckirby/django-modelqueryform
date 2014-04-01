import operator
from collections import OrderedDict
from django.forms import Form, MultipleChoiceField
from django.core.exceptions import ImproperlyConfigured
from django.db.models.query_utils import Q
from .widgets import RangeField
from .utils import traverse_related_to_field
from django.forms.widgets import CheckboxSelectMultiple
try:
    from functools import reduce
except ImportError:  # Python < 3
    pass


class ModelQueryForm(Form):
    model = None
    include = []
    traverse_fields = []

    def __init__(self, *args, **kwargs):
        super(ModelQueryForm, self).__init__(*args, **kwargs)
        if not self.model:
            raise ImproperlyConfigured("ModelQueryForm needs a model defined as a class attribute")

        overlap_fields = set(self.include).intersection(self.traverse_fields)
        if overlap_fields:
            raise ImproperlyConfigured("include and traverse_fields have %s overlapping fields: %s"
                                       % (len(overlap_fields), ",".join(overlap_fields)))
        self._build_form(self.model)

    def clean(self):
        cleaned_data = super(ModelQueryForm, self).clean()

        return cleaned_data

    def _build_form(self, model, field_prepend=None):
        for model_field in model._meta.fields + model._meta.many_to_many:
            orm_name = model_field.name
            if field_prepend:
                orm_name = "%s__%s" % (field_prepend, orm_name)
            if orm_name in self.include:
                self.fields[orm_name] = self._build_form_field(model_field, orm_name)
            if orm_name in self.traverse_fields:
                if model_field.get_internal_type() in self._rel_fields():
                    self._build_form(model_field.rel.to, orm_name)
                else:
                    raise TypeError("%s cannot be used for traversal."
                                    "Traversal fields must be one of type ForeignKey, OneToOneField, ManyToManyField"
                                    % orm_name
                    )

    def _build_form_field(self, model_field, name):
        '''
        Builds a Form Field type given a model field.
        First choice is user defined method build_{field.name}(field)
        Second choice is user defined build_type_{field.get_internal_type()}(field)
        Third choice is field.choices if available
        Last choice is ModelQueryForm defaults:
           RangeField for numeric type field
           MultipleChoiceField for the boolean type fields
           MultipleChoiceField for related models, based on a rel.objects.distinct() call
        Text type fields need user defined methods
        '''
        if hasattr(self, "build_%s" % name.lower()):
            return getattr(self, "build_%s" % name.lower())(model_field)
        if hasattr(self, "build_type_%s" % model_field.get_internal_type().lower()):
            return getattr(self, "build_type_%s" % model_field.get_internal_type().lower())(model_field)
        if not model_field.choices == []:
            return self.get_multiplechoice_field(model_field, model_field.choices)

        if model_field.get_internal_type() in self._numeric_fields():
            return self.get_range_field(model_field, name)
        if model_field.get_internal_type() in self._choice_fields():
            choices = [[True, 'Yes'], [False, 'No']]
            if model_field.get_internal_type() == "NullBooleanField":
                choices += [[None, 'Unknown']]
            return self.get_multiplechoice_field(model_field, choices)
        if model_field.get_internal_type() in self._rel_fields():
            choices = self._get_related_choices(model_field)
            return self.get_multiplechoice_field(model_field, choices)

        raise NotImplementedError(
                    "Field %s doesn't have default field.choices and "
                    "ModelQueryForm doesn't have a default field builder for type %s."
                    "Please define either a method build_type_%s(self, field) for fields of this type or"
                    "build_%s(self, field) for this field specifically"
                    % (model_field.name.lower(),
                       model_field.get_internal_type().lower(),
                       model_field.get_internal_type().lower(),
                       model_field.name.lower())
        )

    def _numeric_fields(self):
        return ['AutoField',
                'BigIntegerField',
                'FloatField',
                'IntegerField',
                'PositiveIntegerField',
                'PositiveSmallIntegerField',
                'SmallIntegerField',
        ]

    def _choice_fields(self):
        return ['BooleanField',
                'NullBooleanField',
        ]

    def _rel_fields(self):
        return ['ForeignKey',
                'ManyToManyField',
                'OneToOneField',
        ]

    def _get_related_choices(self, model_field):
        '''
        Make choices from related fields.
        Choices are all the distinct() objects in the related model
        Choices are of the form [pk, __str__()]

        raises TypeError if the field is not a Relationship field
        '''
        if model_field.get_internal_type() in self._rel_fields():
            choices = [[fkf.pk, fkf] for fkf in model_field.rel.to.objects.all()]
        else:
            raise TypeError("%s cannot be used for traversal."
                            "Traversal fields must be one of type ForeignKey, OneToOneField, ManyToManyField"
                            % model_field
             )
        return choices

    def get_choices_from_distinct(self, model_field):
        '''
        Generate a list of choices from a distinct() call.
        '''

        choices = [[x, x]
            for x in
              self.model.objects.distinct()
                           .order_by(model_field)
                           .values_list(model_field, flat=True)
        ]

        return choices

    def get_range_field(self, model_field, name):
        '''
        Use a RangeField form element for given model field
        '''
        return RangeField(label=model_field.verbose_name,
                          required=False,
                          model=self.model,
                          field=name)

    def get_range_field_filter(self, model_field, values):
        filters = []
        try:
            range_min = values['min']
            range_max = values['max']
            if not range_min == range_max:
                filters.append(reduce(operator.and_,
                                        [Q(**{model_field + '__gte': range_min}),
                                         Q(**{model_field + '__lte': range_max}),
                                         ]
                                      )
                               )
            else:
                filters.append(Q(**{model_field: range_min}))

            if values['allow_empty']:
                filters.append(Q(**{model_field: None}))

            return reduce(operator.or_, filters)
        except:
            return None

    def get_multiplechoice_field_filter(self, model_field, values):
        filters = []
        try:
            for value in values:
                filters.append(Q(**{model_field: value}))

            return reduce(operator.or_, filters)
        except:
            return None

    def get_multiplechoice_field(self, model_field, choices):
        '''
        Use a MultipleChoiceField form element for given model field
        '''
        if not choices == []:
            return MultipleChoiceField(label=model_field.verbose_name,
                                       required=False,
                                       widget=CheckboxSelectMultiple,
                                       choices=choices
            )
        else:
            raise ValueError("%s does not have choices. MultipleChoiceField is inappropriate" % model_field.verbose_name)

    def process(self, data_set=None):
        if data_set is None:
            data_set = self.model.objects.all()

        if not data_set.exists():
            raise ImproperlyConfigured("process requires a QuerySet to filter."
                                       "Run as form.process(QuerySet)"
            )

        if not data_set[0]._meta.fields == self.model._meta.fields:
            raise TypeError("Match the QuerySet to this form instances Model")

        filters = {}
        for field_name in self.changed_data:
            values = self.cleaned_data[field_name]
            if values:
                field = traverse_related_to_field(field_name, self.model)
                if hasattr(self, "filter_%s" % field.name.lower()):
                    filters[field] = self._test_filter_func_is_Q(
                        getattr(self, "filter_%s" %
                            field.name.lower()
                        )(field_name, values)
                    )
                elif hasattr(self, "filter_type_%s" % field.get_internal_type().lower()):
                    filters[field] = self._test_filter_func_is_Q(
                        getattr(self, "filter_type_%s" %
                            field.get_internal_type().lower()
                        )(field_name, values)
                    )
                elif type(self.fields[field_name]) is RangeField:
                    filters[field] = self._test_filter_func_is_Q(
                        self.get_range_field_filter(field_name, values)
                    )
                elif type(self.fields[field_name]) is MultipleChoiceField:
                    filters[field] = self._test_filter_func_is_Q(
                        self.get_multiplechoice_field_filter(field_name, values)
                    )
                else:
                    raise NotImplementedError(
                        "ModelQueryForm doesn't have a default field processor for type %s."
                        "Please define either a method filter_type_%s(self, field, values) for fields of this type or"
                        "filter_%s(self, field, values) for this field specifically"
                        % (field.get_internal_type().lower(),
                           field.get_internal_type().lower(),
                           field.name.lower())
                    )

        if filters.values():
            query = self._test_filter_func_is_Q(self.build_query_from_filters(filters))
            return data_set.filter(query)
        else:
            return data_set

    def _test_filter_func_is_Q(self, filter_func_out):
        if type(filter_func_out) is Q:
            return filter_func_out
        else:
            raise TypeError("Filter methods must return a Q object."
                            "If you have a list use reduce with operator.or_ or operator.and_"
            )

    def build_query_from_filters(self, filters):
        '''
        Given a dict{field_name:Q object} return a Q object
        Override this method if you want to do something other than logical AND between fields
        '''
        try:
            values = filters.values()
        except AttributeError:
            raise TypeError("The parameter filters must be a dict")

        if not all(isinstance(value, Q) for value in values):
            raise TypeError("values in filter dict must be Q objects")

        return reduce(operator.and_, values)

    def get_range_field_print(self, form_field, cleaned_field_data):
        pretty_print = "%s - %s" % (cleaned_field_data["min"],
                                    cleaned_field_data["max"])
        if cleaned_field_data["allow_empty"] is True:
            pretty_print = "%s (include empty values)" % pretty_print

        return pretty_print

    def get_multichoice_field_print(self, form_field, cleaned_field_data):
        choices = dict((str(k), v)
                    for k, v in dict(form_field.choices).items())

        return ",".join([choices[key] for key in cleaned_field_data])

    def pretty_print_query(self):
        vals = OrderedDict()
        for field_name in self.changed_data:
            values = self.cleaned_data[field_name]
            if values:
                field = traverse_related_to_field(field_name, self.model)
                if hasattr(self, "print_%s" % field.name.lower()):
                    vals[self.fields[field_name].label] = \
                    getattr(self, "print_%s" %
                            field.name.lower()
                    )(field, values)
                elif hasattr(self, "print_type_%s" % field.get_internal_type().lower()):
                        vals[self.fields[field_name].label] = \
                        getattr(self, "print_type_%s" %
                            field.get_internal_type().lower()
                        )(field_name, values)
                elif type(self.fields[field_name]) is RangeField:
                    vals[self.fields[field_name].label] = \
                        self.get_range_field_print(self.fields[field_name],
                                                   values)
                elif type(self.fields[field_name]) is MultipleChoiceField:
                    vals[self.fields[field_name].label] = \
                        self.get_multichoice_field_print(self.fields[field_name],
                                                         values)
                else:
                    raise NotImplementedError(
                        "ModelQueryForm doesn't have a default field printer for type %s."
                        "Please define either a method print_type_%s(self, field, values) for fields of this type or"
                        "print_%s(self, field, values) for this field specifically"
                        % (field.get_internal_type().lower(),
                           field.get_internal_type().lower(),
                           field.name.lower())
                    )
        return vals
