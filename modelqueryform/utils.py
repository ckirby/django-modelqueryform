import operator

from django.db.models.query_utils import Q
from django.forms.fields import MultipleChoiceField
from django.forms.widgets import CheckboxSelectMultiple

try:
    from functools import reduce
except ImportError:  # Python < 3
    pass


def traverse_related_to_field(field_name, model):
    '''
    Given an orm relational representation 'relational_field__field_name' and the base model of
    the relation, return the actual terminal Field
    '''
    jumps = field_name.split("__")
    if len(jumps) is 1:
        return model._meta.get_field(field_name)
    else:
        return traverse_related_to_field("__".join(jumps[1:]),
                                         model._meta.get_field(jumps[:1][0]).related_model
                                         )


def get_choices_from_distinct(model, field):
    """Generate a list of choices from a distinct() call.

    :param model: Model to use
    :type model: django.db.models.Model
    :param field: Field whose .distinct values you want
    :type field: django Model Field
    :returns: list -- the distinct values of the field in the model
    """

    choices = [[x, x]
               for x in
               model.objects.distinct()
                   .order_by(field)
                   .values_list(field, flat=True)
               ]

    return choices


def get_range_field(model, field, name):
    '''Generate a RangeField form element

    :param model: Model to generate a form element for
    :type model: django.db.models.Model
    :param field: Model Field to use
    :type field: django model field
    :param name: Name to use for the form field
    :param name: string
    :returns: `RangeField`

    '''
    from .widgets import RangeField
    return RangeField(label=field.verbose_name,
                      required=False,
                      model=model,
                      field=name)


def get_multiplechoice_field(field, choices):
    '''Generate a MultipleChoiceField form element

    :param field: Model Field to use
    :type field: django model field
    :param choices: List of choices for form field
    :type choices: iterable
    :returns: `MultipleChoiceField`
    :raises: ValueError
    '''
    if not choices == []:
        return MultipleChoiceField(label=field.verbose_name,
                                   required=False,
                                   widget=CheckboxSelectMultiple,
                                   choices=choices
                                   )
    else:
        raise ValueError("%s does not have choices. "
                         "MultipleChoiceField is inappropriate" %
                         field.verbose_name)


def get_range_field_filter(field, values):
    """Generate a model filter from a POSTed RangeField

    :param field: orm field name
    :type field: string
    :param values: `RangeField` values dict
    :type values: dict
    :returns: Q -- AND(OR(field__gte: min, field__lte: max),(field__isnull: allow_empty)
    """

    filters = []
    try:
        range_min = values['min']
        range_max = values['max']
        if not range_min == range_max:
            filters.append(reduce(operator.and_,
                                  [Q(**{field + '__gte': range_min}),
                                   Q(**{field + '__lte': range_max}),
                                   ]
                                  )
                           )
        else:
            filters.append(Q(**{field: range_min}))

        if values['allow_empty']:
            filters.append(Q(**{field + '__isnull': True}))

        return reduce(operator.or_, filters)
    except:
        return None


def get_multiplechoice_field_filter(field, values):
    """Generate a model filter from a POSTed MultipleChoiceField

    :param field: orm field name
    :type field: string
    :param values: Selected values
    :type values: list
    :returns: Q -- (OR(field: value),...)
    """
    try:
        return reduce(operator.or_,
                      [Q(**{field: value}) for value in values]
                      )
    except:
        return None
