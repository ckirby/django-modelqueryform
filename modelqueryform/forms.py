
import hashlib
import operator
from collections import OrderedDict
from functools import reduce

from django.core.exceptions import ImproperlyConfigured, FieldDoesNotExist
from django.db.models.query_utils import Q
from django.forms import Form, MultipleChoiceField

from .utils import traverse_related_to_field, get_range_field, \
    get_range_field_filter, get_multiplechoice_field, \
    get_multiplechoice_field_filter
from .widgets import RangeField


class ModelQueryForm(Form):
    """
    ModelQueryForm builds a django form that allows complex filtering against a model.

    :ivar Model model: Model to be filtered
    :ivar list include: Field names to be included using the standard orm naming
    """
    model = None
    include = []

    def __init__(self, *args, **kwargs):
        """
        :raises ImproperlyConfigured: If `model` is missing
        """
        super(ModelQueryForm, self).__init__(*args, **kwargs)
        if not self.model:
            raise ImproperlyConfigured("ModelQueryForm needs a model defined as a class attribute")

        self._build_form(self.model)

    def clean(self):
        cleaned_data = super(ModelQueryForm, self).clean()

        return cleaned_data

    def _build_form(self, model, field_prepend=None):
        """
        Iterates through model fields to generate modelqueryform fields matching `self.include`
        Recursively called to correctly build relationship spanning form fields

        :param model: Current model to inspect. Alwasy starts with `self.model`
        :type model: django.db.model
        :param field_prepend: Relation field name if using `self.traverse`
        :type field_prepend: str
        """
        for field in self.include:
            try:
                if "__" in field:
                    model_field = traverse_related_to_field(field, model)
                else:
                    model_field = model._meta.get_field(field)
                self.fields[field] = self._build_form_field(model_field, field)
            except FieldDoesNotExist:
                pass

    def _build_form_field(self, model_field, name):
        """ Build a form field for a given model field

        :param model_field: field that the resulting form field will filter
        :type model_field: django.db.models.fields
        :param name: The name for the form field (will match a value in self.include)
        :type name: String

        They type of FormField built is determined in the following order:

        #. `build_FIELD(model_field)` (FIELD is the ModelField name)
        #. `build_type_FIELD(model_field)` (FIELD is the ModelField type .lower() eg. 'integerfield', charfield', etc.)
        #. :func:`modelqueryform.utils.get_multiplechoice_field` if model_field has .choices
        #. :func:`modelqueryform.utils.get_range_field` if the ModelField type is in `self.numeric_fields()`
        #. :func:`modelqueryform.utils.get_multiplechoice_field` if the ModelField type is in `self.choice_fields()`
        #. :func:`modelqueryform.utils.get_multiplechoice_field` if the ModelField type is in `self.rel_fields()`

        .. warning::
            You must define either `build_FIELD(model_field)` or `build_type_FIELD(model_field)`
            for ModelFields that do not use a `RangeField` or `MultipleChoiceField`

        :returns: FormField
        :raises NotImplementedError: For fields that do not have a default `ModelQueryForm` field builder and no custom field builder can be found
        """
        if hasattr(self, "build_%s" % name.lower()):
            return getattr(self, "build_%s" % name.lower())(model_field)
        if hasattr(self, "build_type_%s" % model_field.get_internal_type().lower()):
            return getattr(self, "build_type_%s" % model_field.get_internal_type().lower())(model_field)
        if not model_field.choices == []:
            return get_multiplechoice_field(model_field, model_field.choices)

        if model_field.get_internal_type() in self.numeric_fields():
            return get_range_field(self.model, model_field, name)
        if model_field.get_internal_type() in self.choice_fields():
            choices = [[True, 'Yes'], [False, 'No']]
            if model_field.get_internal_type() == "NullBooleanField":
                choices += [[None, 'Unknown']]
            return get_multiplechoice_field(model_field, choices)
        if model_field.get_internal_type() in self.rel_fields():
            choices = self.get_related_choices(model_field)
            return get_multiplechoice_field(model_field, choices)

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

    def numeric_fields(self):
        """Get a list of model fields backed by numeric values

        :returns list: Model Field types that are backed by a numeric
        """
        return ['AutoField',
                'BigIntegerField',
                'FloatField',
                'IntegerField',
                'PositiveIntegerField',
                'PositiveSmallIntegerField',
                'SmallIntegerField',
                ]

    def choice_fields(self):
        """Get a list of model fields backed by choice values (Boolean types)

        :returns list: Model Field types that are backed by a boolean
        """
        return ['BooleanField',
                'NullBooleanField',
                ]

    def rel_fields(self):
        """Get a list of related model fields

        :returns list: Model Field types that are relationships
        """
        return ['ForeignKey',
                'ManyToManyField',
                'OneToOneField',
                ]

    def get_related_choices(self, model_field):
        """Make choices from a related

        :param model_field: Field to generate choices from
        :type model_field: ForeignKey, OneToOneField, ManyToManyField
        :returns list: [[field.pk, field.__str__()],...]
        :raises TypeError: If `model_field` is not a relationship type

        """
        if model_field.get_internal_type() in self.rel_fields():
            choices = [[fkf.pk, fkf] for fkf in model_field.related_model.objects.all()]
        else:
            raise TypeError("%s cannot be used for traversal."
                            "Traversal fields must be one of type ForeignKey, OneToOneField, ManyToManyField"
                            % model_field
                            )
        return choices

    def process(self, data_set=None):
        """Filter a QuerySet with the POSTed form values

        :param data_set: QuerySet to filter against
        :type data_set: QuerySet (Same Model class as self.model)

        .. note:: If data_set == None, self.model.objects.all() is used

        :returns QuerySet: data_set.filter(Q object)
        :raises ImproperlyConfigured: No `data_set` to filter
        :raises TypeError: `data_set` is not an instance (using `isinstance()`) of `self.model`
        """
        if data_set is None:
            data_set = self.model.objects.all()

        else:
            if data_set.first() is not None and not isinstance(data_set.first(), self.model):
                raise TypeError("Match the QuerySet to this form instances Model")

        query = self._get_query()
        if query is not None:
            return data_set.filter(query)
        else:
            return data_set

    def _get_query(self):
        filters = self.get_filters()

        if filters.values():
            return self._test_filter_func_is_Q(
                self.build_query_from_filters(filters)
            )
        return None

    def get_filters(self):
        """ Get a dict of the POSTed form values as Q objects
        Form fields will be evaluated in the following order to generate a Q object:

        #. `filter_FIELD(field_name, values)` (FIELD is the ModelField name)
        #. `filter_type_FIELD(field_name, values)` (FIELD is the ModelField type .lower() eg. 'integerfield', charfield', etc.)
        #. :func:`modelqueryform.utils.get_range_field_filter` if the FormField is a RangeField
        #. :func:`modelqueryform.utils.get_multiplechoice_field_filter` if the FormField is a MultipleChoiceField

        .. warning::
            You must define either `filter_FIELD(field, values)` or `filter_type_FIELD(field, values)`
            for ModelFields that do not use a `RangeField` or `MultipleChoiceField`

        :returns Dict: {Form field name: Q object,...}
        :raises NotImplementedError: For fields that do not have a default `ModelQueryForm` filter builder and no custom filter builder can be found
        """
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
                        get_range_field_filter(field_name, values)
                    )
                elif type(self.fields[field_name]) is MultipleChoiceField:
                    filters[field] = self._test_filter_func_is_Q(
                        get_multiplechoice_field_filter(field_name, values)
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
        return filters

    def _test_filter_func_is_Q(self, filter_func):
        """
        Make sure that a filter is a Q object

        :param filter_func: Object to test
        :type filter_func: Q
        :raises TypeError: if filter is not a Q object
        """
        if type(filter_func) is Q:
            return filter_func
        else:
            raise TypeError("Filter methods must return a Q object."
                            "If you have a list use reduce with operator.or_ or operator.and_"
                            )

    def build_query_from_filters(self, filters):
        """Generate a Q object that is a logical AND of a list of Q objects

        .. note::
            Override this method to build a more complex Q object than AND(filters.values())

        :param filters: Dict of {Form field name: Q object,...}
        :type filters: dict
        :returns Q: AND(filters.values())
        :raises TypeError: if any value in the filters dict is not a Q object
        """
        try:
            values = filters.values()
        except AttributeError:
            raise TypeError("The parameter filters must be a dict")

        if not all(isinstance(value, Q) for value in values):
            raise TypeError("values in filter dict must be Q objects")

        return reduce(operator.and_, values)

    def get_range_field_print(self, form_field, cleaned_field_data):
        """
        Default string representation of multichoice field

        :param form_field: FormField (Unused)
        :type form_field: str

            .. note:: FormField is needed to lookup choices

        :param cleaned_field_data: the cleaned_data for the field
        :type cleaned_field_data: dict

        :returns str: "MIN - MAX [(include empty values)]"
        """

        pretty_print = "%s - %s" % (cleaned_field_data["min"],
                                    cleaned_field_data["max"])
        if cleaned_field_data["allow_empty"] is True:
            pretty_print = "%s (include empty values)" % pretty_print

        return pretty_print

    def get_multichoice_field_print(self, form_field, cleaned_field_data):
        """
        Default string representation of multichoice field

        :param form_field: FormField
        :type form_field: str

            .. note:: FormField is needed to lookup choices

        :param cleaned_field_data: the cleaned_data for the field
        :type cleaned_field_data: dict

        :returns str: Comma delimited get_display_FIELD() for selected choices
        """
        choices = dict((str(k), v)
                       for k, v in dict(form_field.choices).items())

        return ",".join([choices[key] for key in cleaned_field_data])

    def pretty_print_query(self, fields_to_print = None):
        """
        Get an OrderedDict to facilitate printing of generated filter

        :param fields_to_print: List of names in changed_data
        :type fields_to_print: list

        .. note:: If fields_to_print == None, self.changed_data is used

        :returns dict: {form field name: string representation of filter,...}
        :raises NotImplementedError: For fields that do not have a default print builder and no custom print builder can be found
        :raises ValueError: if any name in the field_to_print is not in self.changed_data
        """
        vals = OrderedDict()
        if fields_to_print is None:
            fields_to_print = self.changed_data
        else:
            if not set(fields_to_print).issubset(set(self.changed_data)):
                raise ValueError('field names in fields_to_print must be in self.changed_data')

        for field_name in sorted(fields_to_print):
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

    def query_hash(self):
        """
        Get an md5 hexdigest of the pretty_print_query().

        .. note:: Useful for caching results of a given query

        :returns str: 32 char md5.hexdigest()
        """
        return hashlib.md5(str(self.pretty_print_query()).encode('utf-8')).hexdigest()

