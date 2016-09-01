from django.core.exceptions import ValidationError
from django.db.models.aggregates import Min, Max
from django.forms.fields import Field
from django.forms.widgets import MultiWidget, CheckboxInput, NumberInput
from django.utils.safestring import mark_safe

from .utils import traverse_related_to_field


class RangeWidget(MultiWidget):
    '''
    Build a MultiWidget with 3 fields:
       TextInput with a "min" attribute
       TextInput with a "max" attribute
       Checkbox to include/exclude None values
    '''
    allow_null = False

    def __init__(self, allow_null=False, attrs=None, mode=0):
        _widgets = (
            NumberInput(attrs=attrs),
            NumberInput(attrs=attrs),
        )

        if allow_null:
            self.allow_null = True
            _widgets += (CheckboxInput(),)

        super(RangeWidget, self).__init__(_widgets, attrs)

    def decompress(self, value):
        if value:
            decompress_value = [value['min'], value['max']]
            if self.allow_null:
                decompress_value += [value['allow_empty']]
            return decompress_value
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
        html = '%s %s' % (rendered_widgets[0], rendered_widgets[1])
        if self.allow_null:
            html = '%s <br/> %s %s' % (html, 'Include Empty values', rendered_widgets[2])
        return mark_safe(u'%s' % html)


class RangeField(Field):
    def __init__(self, model, field, *args, **kwargs):
        range_min = model.objects.all().aggregate(Min(field))[field + "__min"]
        range_max = model.objects.all().aggregate(Max(field))[field + "__max"]
        super(RangeField, self).__init__(*args, **kwargs)
        self.widget = RangeWidget(allow_null=traverse_related_to_field(field, model).null,
                                  attrs={'min': range_min, 'max': range_max})

    def to_python(self, value):
        if not value:
            return []
        try:
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
