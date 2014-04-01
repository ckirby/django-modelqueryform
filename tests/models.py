from __future__ import unicode_literals
from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class BaseModelForTest(models.Model):
    integer = models.IntegerField()
    integer_with_choices = models.IntegerField(choices=[[1, "a"], [2, "b"], [3, "c"]])
    float = models.FloatField()
    boolean = models.BooleanField()
    null_boolean = models.NullBooleanField()
    text = models.TextField()
    related_type = models.OneToOneField('RelatedModelForTest', related_name="ones", null=True)
    foreign_related = models.ForeignKey('RelatedModelForTest', related_name="foreigns", null=True)
    many_related = models.ManyToManyField('RelatedModelForTest', related_name="manys", null=True)

    def __str__(self):
        return "%s" % self.pk

@python_2_unicode_compatible
class RelatedModelForTest(models.Model):
    related_type = models.IntegerField()

    def __str__(self):
        return "%s" % self.related_type
