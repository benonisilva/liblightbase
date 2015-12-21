#!/usr/env python
# -*- coding: utf-8 -*-
from liblightbase import lbutils
from liblightbase.lbdoc.metadata import DocumentMetadata

def generate_metaclass(struct, base=None):
    """ 
    Generate document metaclass. The document metaclass 
    is an abstraction of document model defined by base 
    structures.
    @param struct: Field or Group object.
    @param base: Base object or None.
    """
    build_metadata = False
    if base is None:
        base = struct
        build_metadata = True
    snames = struct.content.__snames__
    rnames = struct.content.__rnames__

    class MetaClass(object):
        """ 
        Document metaclass. Describes the structures defifined by
        document structure model.
        """
        # @property __valreq__: Flag used to validate required
        # fields or not.
        __valreq__ = True

        # @property __slots__: reserves space for the declared 
        # variables and prevents the automatic creation of 
        # __dict__ and __weakref__ for each instance.
        __slots__ = ['_' + sname for sname in snames]
        if build_metadata:
            __slots__.append('__metadata__')

        def __init__(self, **kwargs):
            """ Document MetaClass constructor
            """
            if self.__valreq__:
                lbutils.validate_required(rnames, kwargs)
            for arg in kwargs:
                setattr(self, arg, kwargs[arg])

    for childstruct in struct.content:
        structname, prop = generate_property(base, childstruct)
        setattr(MetaClass, structname, prop)
    if build_metadata:
        MetaClass._metadata = build_metadata_prop()
    MetaClass.__name__ = struct.metadata.name
    return MetaClass


def generate_property(base, struct):
    """
    Make python's property based on structure attributes.
    @param base: Base object.
    @param struct: Field or Group object.
    """
    if struct.is_group:
        structname = struct.metadata.name
    else:
        # Se não for grupo é campo
        structname = struct.name
    attr_name = '_' + structname

    def getter(self):
        value = getattr(self, attr_name)
        if struct.is_field:
            return getattr(value, '__value__')
        return value

    def setter(self, value):
        struct_metaclass = base.metaclass(structname)
        if struct.is_field:
            value = struct_metaclass(value)
        elif struct.is_group:
            if struct.metadata.multivalued:
                msg = 'object {} should be instance of {}'.format(
                    struct.metadata.name, list)
                assert isinstance(value, list), msg
                msg = '{} list elements should be instances of {}'.format(
                    struct.metadata.name, struct_metaclass)
                assertion = all(isinstance(element, struct_metaclass) \
                    for element in value)
                assert assertion, msg
                value = generate_multimetaclass(struct,
                    struct_metaclass)(value)
            else:
                msg = '{} object should be an instance of {}'.format(
                    struct.metadata.name, struct_metaclass)
                assert isinstance(value, struct_metaclass), msg
        setattr(self, attr_name, value)

    def deleter(self):
        delattr(self, attr_name)

    return structname, property(getter,
        setter, deleter, structname)

def build_metadata_prop():

    def fget(self):
        return self.__metadata__

    def fset(self, value):
        msg = '_metadata attribute should be a DocumentMetadata object.'
        assert isinstance(value, DocumentMetadata)
        self.__metadata__ = value

    def fdel(self):
        del self.__metadata__

    return property(fget, fset, fdel, '_metadata')


def generate_multimetaclass(struct, struct_metaclass):
    """ 
    Generate metaclass to use with multivalued groups.
    @param struct: Field or Group object
    @param struct_metaclass: The struct Metaclass 
    """

    class MultiGroupMetaClass(list):
        """
        Multivalued Group Metaclass. Metaclass used to ensure list
        elements are instances of right metaclasses.
        """

        def __setitem__(self, index, element):
            """ x.__setitem__(y, z) <==> x[y] = z
            """
            msg = '{} list elements should be instances of {}'.format(
                struct.metadata.name, struct_metaclass)
            assert isinstance(element, struct_metaclass), msg
            return super(MultiGroupMetaClass, self).__setitem__(index,
                element)

        def append(self, element):
            """ L.append(object) -- append object to end
            """
            msg = '{} list elements should be instances of {}'.format(
                struct.metadata.name, struct_metaclass)
            assert isinstance(element, struct_metaclass), msg
            return super(MultiGroupMetaClass, self).append(element)

    return MultiGroupMetaClass

def generate_field_metaclass(field, base):
    """
    Generate field metaclass. The field metaclass 
    validates incoming value against fields' datatype. 
    @param field: Field object.
    @param base: Base object.
    """

    class FieldMetaClass(object):
        """ 
        Field MetaClass. validates incoming 
        value against fields' datatype.
        """
        def __init__(self, value):
            self.__value__ = value

        def __setattr__(self, obj, value):
            validator = field._datatype.__schema__(base, field, 0)
            if field.multivalued is True:
                msg = 'Expected type list for {}, but found {}'
                assert isinstance(value, list), msg.format(
                    field.name, type(value))
                value = [validator(element) for element in value]
            else:
                value = validator(value)
            super(FieldMetaClass, self).__setattr__('__value__', value)

        def __getattr__(self, obj):
            return super(FieldMetaClass, self).__getattribute__('__value__')

    FieldMetaClass.__name__ = field.name
    return FieldMetaClass
