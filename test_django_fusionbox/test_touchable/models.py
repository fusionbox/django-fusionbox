from django.db import models

from fusionbox.behaviors import Touchable


# The order of these models is signification. Putting a
# ForeignKey('TouchableParent') on a model defined _after_ TouchableParent is
# created means the behavior metaclass does not know about the foreign key at
# the time TouchableParent is created, and must use Django's signals framework
# to be informed of it. 

class TouchableParent(Touchable):
    child = models.ForeignKey('TouchableChildForeignKey', null=True)
    child_one_to_one = models.OneToOneField('TouchableChildOneToOne', null=True)
    children = models.ManyToManyField('TouchableChildManyToMany')

class TouchableChildForeignKey(models.Model):
    pass

class TouchableChildOneToOne(models.Model):
    pass

class TouchableChildManyToMany(models.Model):
    pass

class TouchableChildForeignKeyOtherWay(models.Model):
    parent = models.ForeignKey('TouchableParent')

class TouchableChildOneToOneOtherWay(models.Model):
    parent = models.OneToOneField('TouchableParent')

class TouchableChildManyToManyOtherWay(models.Model):
    parents = models.ManyToManyField('TouchableParent')

class TouchableChild2ForeignKey(Touchable):
    parent = models.ForeignKey(TouchableParent)

class TouchableChildTwoLeveles(models.Model):
    parent = models.ForeignKey('TouchableChild2ForeignKey')
