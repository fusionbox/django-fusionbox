from django.test import TestCase
from test_touchable.models import *


class TestTouchable(TestCase):
    def test_foreignkey(self):
        child = TouchableChildForeignKey.objects.create()
        parent = TouchableParent.objects.create(
                child=child)

        child.save()
        assert TouchableParent.objects.get(pk=parent.pk).updated_at > parent.updated_at

    def test_onetoone(self):
        child = TouchableChildOneToOne.objects.create()
        parent = TouchableParent.objects.create(
                child_one_to_one=child)

        child.save()
        assert TouchableParent.objects.get(pk=parent.pk).updated_at > parent.updated_at

    def test_manytomany(self):
        child = TouchableChildManyToMany.objects.create()
        parent = TouchableParent.objects.create()
        parent.children.add(child)

        parent = TouchableParent.objects.get(id=parent.id)

        child.save()

        assert TouchableParent.objects.get(pk=parent.pk).updated_at > parent.updated_at

    def test_other_way_foreign(self):
        parent = TouchableParent.objects.create()
        child = TouchableChildForeignKeyOtherWay.objects.create(parent=parent)
        child.save()

        assert TouchableParent.objects.get(pk=parent.pk).updated_at > parent.updated_at


    def test_other_many(self):
        parent = TouchableParent.objects.create()
        child = TouchableChildManyToManyOtherWay.objects.create()
        child.save()

        child.parents.add(parent)
        child.save()

        assert TouchableParent.objects.get(pk=parent.pk).updated_at > parent.updated_at

    def test_other_one(self):
        parent = TouchableParent.objects.create()
        child = TouchableChildOneToOneOtherWay.objects.create(parent=parent)

        child.save()

        assert TouchableParent.objects.get(pk=parent.pk).updated_at > parent.updated_at

    def test_two_levels(self):
        parent = TouchableParent.objects.create()
        child = TouchableChild2ForeignKey.objects.create(parent=parent)
        grandchild = TouchableChildTwoLeveles(parent=child)

        grandchild.save()

        assert TouchableParent.objects.get(pk=parent.pk).updated_at > parent.updated_at
