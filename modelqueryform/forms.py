from django.forms import Form, MultipleChoiceField
from django.db import models
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.forms.widgets import CheckboxSelectMultiple, MultiWidget, TextInput, CheckboxInput
from django.utils.safestring import mark_safe
from django.forms.fields import Field
from django.db.models.aggregates import Min, Max
from django.db.models.query_utils import Q
import operator
from collections import OrderedDict

class ModelQueryForm(Form):
    model = None
    fields = []
    traverse_fields = []

    def __init__(self, *args, **kwargs):
        super(ModelQueryForm, self).__init__(*args, **kwargs)
        if not self.model:
            raise ImproperlyConfigured("ModelQueryForm needs a model to work with")

        self._build_form(self.model)

    def _build_form(self, model, field_prepend=None):
        for field in model._meta.fields + model._meta.many_to_many:
            orm_name = field.name
            if field_prepend:
                orm_name = "%s__%s" % (field_prepend, orm_name)
            if not orm_name in self.fields:
                continue
            if orm_name in self.traverse_fields:
                if self.is_rel_field(field):
                    self._build_form(field.rel.to, orm_name)
                else:
                    raise TypeError("%s cannot be used for traversal."
                                    "Traversal fields must be one of type ForeignKey, OneToOneField, ManyToManyField"
                                    % orm_name
                    )
            self.fields[field.name] = self._build_form_field(field, orm_name)

    def _build_form_field(self, field, name):
        '''
        Builds a Form Field type given a model field.
        First attempt is method build_{field.name}
        Second attempt is method build_type_{field.get_internal_type()}
        Otherwise defaults to defined field.choices if available
        '''
        if hasattr(self, "build_%s" % name.lower):
            return getattr(self, "build_%s" % name.lower)(field, name)
        if hasattr(self, "build_type_%s" % field.get_internal_type().lower):
            return getattr(self, "build_type_%s" % field.get_internal_type().lower)(field, name)
        if not field.choices == []:
            return self.get_multiplechoice_field(field)

        raise NotImplementedError(
                    "Field %s doesn't have default field.choices and "
                    "ModelQueryForm doesn't have a default field builder for type %s."
                    "Please define either a method build_type_%s(self, field) for fields of this type or"
                    "build_%s(self, field) for this field specifically"
                    % (field.name.lower(),
                       field.get_internal_type().lower(),
                       field.get_internal_type().lower(),
                       field.name.lower())
        )

    def is_rel_field(self, field):
        if field.get_internal_type() in ('ForeignKey, OneToOneField, ManyToManyField'):
            return True
        else:
            return False

    def _get_related_choices(self, field):
        '''
        Make choices from related fields.
        Choices are all the distinct() objects in the related model
        Choices are of the form [pk, __str__()]

        raises TypeError if the field is not a Relationship field
        '''
        if self.is_rel_field(field):
            field.choices = [[fkf.pk, fkf] for fkf in sorted(field.rel.to.objects.distinct())]
        else:
             raise TypeError("%s cannot be used for traversal."
                            "Traversal fields must be one of type ForeignKey, OneToOneField, ManyToManyField"
                            % orm_name
             )

    def get_choices_from_distinct(self, field):
        '''
        Generate a list of choices from a distinct() call.
        '''

        field.choices = [[x, x]
            for x in
              self.model.objects.distinct()
                           .order_by(field.name)
                           .values_list(field.name, flat=True)
          ]

    def get_range_field(self, field, name):
        '''
        Use a RangeField form element for given model field
        '''
        try:
            return RangeField(label=field.verbose_name, required=False, model=self.model, field=name)
        except:
            raise TypeError("RangeFields should only be used with model fields based on a python numeric type")

    def get_multiplechoice_field(self, field, name):
        '''
        Use a MultipleChoiceField form element for given model field
        '''
        return MultipleChoiceField(label=field.verbose_name, required=False, widget=CheckboxSelectMultiple, choices=field.choices)

    def get_choice_or_range_field(self, field, name):
        '''
        For numeric fields.
        If there are defined choices return a MultipleChoiceField.
        Otherwise return a RangeField.
        '''
        if field.choices == []:
            return self.get_range_field(field, name)
        else:
            return self.get_multiplechoice_field(field)

    def build_type_foreignkey(self, field, name):
        self._get_related_choices(field)
        return self.get_multiplechoice_field(field, name)

    def build_type_manytomanyfield(self, field, name):
        self._get_related_choices(field)
        return self.get_multiplechoice_field(field, name)

    def build_type_onetoonefield(self, field, name):
        self._get_related_choices(field)
        return self.get_multiplechoice_field(field, name)

    def build_type_autofield(self, field, name):
        '''
        Return a RangeField for AutoField type elements
        '''
        return self.get_range_field(field, name)

    def build_type_bigintegerfield(self, field, name):
        return self.get_choice_or_range_field(field, name)

    def build_type_integerfield(self, field, name):
        return self.get_choice_or_range_field(field, name)

    def build_type_decimalfield(self, field, name):
        return self.get_choice_or_range_field(field, name)

    def build_type_floatfield(self, field, name):
        return self.get_choice_or_range_field(field, name)

    def build_type_positiveintegerfield(self, field, name):
        return self.get_choice_or_range_field(field, name)

    def build_type_positivesmallintegerfield(self, field, name):
        return self.get_choice_or_range_field(field, name)

    def build_type_smallintegerfield(self, field, name):
        return self.get_choice_or_range_field(field, name)

    def build_type_booleanfield(self, field, name):
        '''
        Return a MultipleChoiceField for BooleanField type elements
        Choices are [[True, 'Yes'], [False, 'No']]
        '''
        field.choices = [[True, 'Yes'], [False, 'No']]
        return self.get_multiplechoice_field(field, name)

    def build_type_nullbooleanfield(self, field, name):
        '''
        Return a MultipleChoiceField for NullBooleanField type elements
        Choices are [[True, 'Yes'], [False, 'No'], [None, 'Unknown']]
        '''
        field.choices = [[True, 'Yes'], [False, 'No'], [None, 'Unknown']]
        return self.get_multiplechoice_field(field, name)


    def clean(self):
        cleaned_data = super(ModelQueryForm, self).clean()

        return cleaned_data

    def process_model_query(self, data_set=None):
        if data_set is None:
            data_set = self.model.objects.all()

        try:
            data_set.exists()
        except:
            raise ImproperlyConfigured("Model query requires a QuerySet to filter against")

        full_query = []
        for field in self.changed_data:
            values = self.cleaned_data[field]
            if values:
                query_list = []
                if not isinstance(values, dict):
                    for value in values:
                        query_list.append(Q(**{field: value}))
                else:
                    if values['allow_empty']:
                        query_list.append(Q(**{field: None}))
                    range_min = values['min']
                    range_max = values['max']
                    if range_min == range_max:
                        query_list.append(Q(**{field: range_min}))
                    else:
                        range_list = []
                        range_list.append(Q(**{field + '__gte': range_min}))
                        range_list.append(Q(**{field + '__lte': range_max}))

                        query_list.append(reduce(operator.and_, range_list))
                full_query.append(reduce(operator.or_, query_list))
        if full_query:
            data_set = data_set.filter(reduce(operator.and_, full_query))

        return data_set

    def pretty_print_query(self):
        vals = OrderedDict()
        for field in self.changed_data:
            try:
                if self.fields[field]:
                    try:
                        choices = self.fields[field].choices
                        for selected in self.cleaned_data[field]:
                            try:
                                vals[self.fields[field].label]
                                vals[self.fields[field].label] = "%s; %s" % (vals[self.fields[field].label], dict(choices)[int(selected)])
                            except:
                                vals[self.fields[field].label] = "%s" % dict(choices)[int(selected)]
                    except:
                        vals[self.fields[field].label] = "%s - %s" % (self.cleaned_data[field][0], self.cleaned_data[field][1])
                        if len(self.cleaned_data[field]) == 3:
                            vals[self.fields[field].label] = "%s. %s" % (vals[self.fields[field].label], "Includes Empty Values")

            except Exception, e:
                print e
        return vals

class RangeWidget(MultiWidget):
    # SHOW ALLOW EMPTY ONYL ON FIELDS THAT ALLOW NULL
    def __init__(self, attrs=None, mode=0):
        _widgets = (
            TextInput(attrs=attrs),
            TextInput(attrs=attrs),
            CheckboxInput()
        )
        super(RangeWidget, self).__init__(_widgets, attrs)

    def decompress(self, value):
        if value:
            return [value['min'], value['max'], value['allow_empty']]
        return [None, None]

    def value_from_datadict(self, data, files, name):
        value = {}
        try:
            if not data[name + "_0"] == '':
                value['min'] = data[name + "_0"]
                value['max'] = data[name + "_1"]
                try:
                    if data[name + "_2"]:
                        value['allow_empty'] = True
                except:
                    value['allow_empty'] = False
        except:
            pass
        return value

    def format_output(self, rendered_widgets):
        return mark_safe(u'%s %s<br/> %s %s' % \
            (rendered_widgets[0], rendered_widgets[1], 'Allow Empty Values', rendered_widgets[2]))

class RangeField(Field):
    def __init__(self, model, field, *args, **kwargs):
        range_min = model.objects.all().aggregate(Min(field))[field + "__min"]
        range_max = model.objects.all().aggregate(Max(field))[field + "__max"]
        super(RangeField, self).__init__(*args, **kwargs)
        self.widget = RangeWidget({'min':range_min, 'max':range_max})

    def to_python(self, value):
        if not value:
            return []
        try:
            value['allow_empty'] = value['allow_empty']
            value['min'] = int(value['min'])
            value['max'] = int(value['max'])
        except:
            try:
                value['min'] = float(value['min'])
                value['max'] = float(value['max'])
            except:
                raise ValidationError('Values in RangeField must be numeric')

        return value

    def validate(self, value):
        if value:
            if value['min'] > value['max']:
                raise ValidationError('Min must be less than or equal to Max')
