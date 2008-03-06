from django.db import models
from django.conf import settings
from sqlalchemy import Column
from sqlalchemy.orm import deferred, synonym
from sqlalchemy.types import *
from sqlalchemy.ext.associationproxy import association_proxy
from django_sqlalchemy.models.statements import ClassMutator
from django_sqlalchemy.models.properties import Property

class Field(models.Field, Property):
    
    def __init__(self, *args, **kwargs):
        self.synonym = kwargs.pop('synonym', None)
        self.deferred = kwargs.pop('deferred', False)
        self.colname = kwargs.pop('name', None)
        self.column = None
        self.property = None
        # call django's init. this is here because I cannot figure out how to call django's Field.__init__
        # due to the way the maxlength metaclass is wired up.  it does crazy things, calling back to the 
        # derived class causing an infinite loop.
        Property.__init__(self, *args, **kwargs)
        models.Field.__init__(self, **kwargs)
    
    def attach(self, entity, name):
        # If no colname was defined (through the 'colname' kwarg), set
        # it to the name of the attr.
        if self.colname is None:
            self.colname = name
        super(Field, self).attach(entity, name)
    
    def create_pk_cols(self):
        if self.primary_key:
            self.create_col()
    
    def create_non_pk_cols(self):
        if not self.primary_key:
            self.create_col()
    
    def create_col(self):
        # create the base kwargs dict for sa
        kwargs = dict(nullable=self.null,
                index=self.db_index, unique=self.unique, default=self.default)
        # dump in field specific kwargs and overrides
        kwargs.update(self.sa_column_kwargs())
        self.column = Column(self.name, self.sa_column_type(), 
                *self.sa_column_args(),
                **kwargs)
        self.entity._descriptor.add_column(self.column)
        
    def create_properties(self):
        if self.deferred:
            group = None
            if isinstance(self.deferred, basestring):
                group = self.deferred
            self.property = deferred(self.column, group=group)
        elif self.name != self.colname:
            self.property = self.column

        if self.property:
            self.entity._descriptor.add_property(self.name, self.property)

        if self.synonym:
            self.entity._descriptor.add_property(self.synonym, 
                                                 synonym(self.name))
    
    def sa_column_type(self):
        raise NotImplementedError
    
    def sa_column_args(self):
        return tuple()
    
    def sa_column_kwargs(self):
        return dict()
       
class AutoField(models.AutoField, Field):
    def __init__(self, *args, **kwargs):
        models.AutoField.__init__(self, *args, **kwargs)
        Field.__init__(self, *args, **kwargs)
        
    def sa_column_kwargs(self):
        kwargs = dict(primary_key=True)
        base = super(AutoField, self).sa_column_kwargs()
        base.update(kwargs)
        return base
    
    def sa_column_type(self):
        return Integer()

class BooleanField(models.BooleanField, Field):
    def __init__(self, *args, **kwargs):
        models.BooleanField.__init__(self, *args, **kwargs)
        Field.__init__(self, *args, **kwargs)
    
    def sa_column_type(self):
        return Boolean()
    
class CharField(models.CharField, Field):
    def __init__(self, *args, **kwargs):
        Field.__init__(self, *args, **kwargs)
    
    def sa_column_type(self):
        return Unicode(length=self.max_length)
        
class CommaSeparatedIntegerField(models.CommaSeparatedIntegerField, CharField):
    def __init__(self, *args, **kwargs):
        CharField.__init__(self, *args, **kwargs)
    
class DateField(models.DateField, Field):
    def __init__(self, verbose_name=None, name=None, auto_now=False, auto_now_add=False, **kwargs):
        models.DateField.__init__(self, verbose_name=verbose_name, 
                                        name=name, 
                                        auto_now=auto_now, 
                                        auto_now_add=auto_now_add, **kwargs)
        Field.__init__(self, verbose_name=None, name=None, **kwargs)
    
    def sa_column_type(self):
        return Date()

class DateTimeField(models.DateTimeField, DateField):
    def __init__(self, *args, **kwargs):
        DateField.__init__(self, *args, **kwargs)
    
    def sa_column_type(self):
        return DateTime()

class DecimalField(models.DecimalField, Field):
    def __init__(self, *args, **kwargs):
        models.DecimalField.__init__(self, verbose_name=kwargs.get('verbose_name', None), 
                                           name=kwargs.get('name', None), 
                                           max_digits=kwargs.get('max_digits', None), 
                                           decimal_places=kwargs.get('decimal_places', None), **kwargs)
        Field.__init__(self, *args, **kwargs)
    
    def sa_column_kwargs(self):
        kwargs = dict(precision=self.decimal_places, length=self.max_digits)
        base = super(DecimalField, self).sa_column_kwargs()
        base.update(kwargs)
        return base

    def sa_column_type(self):
        return Numeric()

class EmailField(models.EmailField, CharField):
    def __init__(self, *args, **kwargs):
        models.EmailField.__init__(self,  *args, **kwargs)
        CharField.__init__(self, *args, **kwargs)
    
class FileField(models.FileField, Field):
    def __init__(self, *args, **kwargs):
        models.FileField.__init__(self, verbose_name=kwargs.get('verbose_name', None), 
                                        name=kwargs.get('name', None), 
                                        upload_to=kwargs.get('upload_to', ''), **kwargs)
        Field.__init__(self, *args, **kwargs)
    
    def sa_column_type(self):
        return Unicode(length=self.max_length)

class FilePathField(models.FilePathField, Field):
    def __init__(self, *args, **kwargs):
        models.FilePathField.__init__(self, verbose_name=kwargs.get('verbose_name', None), 
                                            name=kwargs.get('name', None), 
                                            path=kwargs.get('path', ''), 
                                            match=kwargs.get('match', None), 
                                            match=kwargs.get('recursive', False), **kwargs)
        Field.__init__(self, *args, **kwargs)
    
    def sa_column_type(self):
        return Unicode(length=self.max_length)

class FloatField(models.FloatField, Field):
    def __init__(self, *args, **kwargs):
        Field.__init__(self, *args, **kwargs)
    
    def sa_column_type(self):
        return Float()

class ImageField(models.ImageField, FileField):
    def __init__(self, *args, **kwargs):
        models.ImageField.__init__(self, verbose_name=kwargs.get('verbose_name', None), 
                                        name=kwargs.get('name', None), 
                                        width_field=kwargs.get('width_field', ''), 
                                        height_field=kwargs.get('height_field', None), **kwargs)
        FileField.__init__(self, *args, **kwargs)

class IntegerField(models.IntegerField, Field):
    def __init__(self, *args, **kwargs):
        Field.__init__(self, *args, **kwargs)
    
    def sa_column_type(self):
        return Integer()

class IPAddressField(models.IPAddressField, Field):
    def __init__(self, *args, **kwargs):
        Field.__init__(self, *args, **kwargs)
    
    def sa_column_type(self):
        return Unicode(length=self.max_length)

class NullBooleanField(models.NullBooleanField, Field):
    def __init__(self, *args, **kwargs):
        models.NullBooleanField.__init__(self, *args, **kwargs)
        Field.__init__(self, *args, **kwargs)
    
    def sa_column_type(self):
        return Boolean()

class PhoneNumberField(models.PhoneNumberField, IntegerField):
    def __init__(self, *args, **kwargs):
        IntegerField.__init__(self, *args, **kwargs)
    
    def sa_column_type(self):
        ''' This is a bit odd because in Django the PhoneNumberField descends from an IntegerField in a 
            hacky way of getting around not providing a max_length.  The database backends enforce the
            length as a varchar(20).
        '''
        return Unicode(length=20)

class PositiveIntegerField(models.PositiveIntegerField, IntegerField):
    def __init__(self, *args, **kwargs):
        IntegerField.__init__(self, *args, **kwargs)

class PositiveSmallIntegerField(models.PositiveSmallIntegerField, IntegerField):
    def __init__(self, *args, **kwargs):
        IntegerField.__init__(self, *args, **kwargs)
    
    def sa_column_type(self):
        return SmallInteger()

class SlugField(models.SlugField, CharField):
    def __init__(self, *args, **kwargs):
        models.SlugField.__init__(self, *args, **kwargs)
        CharField.__init__(self, *args, **kwargs)

class SmallIntegerField(models.SmallIntegerField, IntegerField):
    def __init__(self, *args, **kwargs):
        IntegerField.__init__(self, *args, **kwargs)
    
    def sa_column_type(self):
        return SmallInteger()

class TextField(models.TextField, Field):
    def __init__(self, *args, **kwargs):
        Field.__init__(self, *args, **kwargs)
    
    def sa_column_type(self):
        return UnicodeText()

class TimeField(models.TimeField, Field):
    def __init__(self, *args, **kwargs):
        models.TimeField.__init__(self, verbose_name=kwargs.get('verbose_name', None), 
                                        name=kwargs.get('name', None), 
                                        auto_now=kwargs.get('auto_now', False), 
                                        auto_now_add=kwargs.get('auto_now_add', False), **kwargs)
        Field.__init__(self, *args, **kwargs)
    
    def sa_column_type(self):
        return Time()

class URLField(models.URLField, CharField):
    def __init__(self, *args, **kwargs):
        models.URLField.__init__(self, verbose_name=kwargs.get('verbose_name', None), 
                                       name=kwargs.get('name', None), 
                                       verify_exists=kwargs.get('verify_exists', True), **kwargs)
        CharField.__init__(self, *args, **kwargs)

class USStateField(models.USStateField, Field):
    def __init__(self, *args, **kwargs):
        Field.__init__(self, *args, **kwargs)
    
    def sa_column_type(self):
        return Unicode(length=2)

class XMLField(models.XMLField, TextField):
    def __init__(self, *args, **kwargs):
        models.XMLField.__init__(self, verbose_name=kwargs.get('verbose_name', None), 
                                       name=kwargs.get('name', None), 
                                       schema_path=kwargs.get('schema_path', None), **kwargs)
        TextField.__init__(self, *args, **kwargs)

class OrderingField(models.OrderingField, IntegerField):
    def __init__(self, *args, **kwargs):
        OrderingField.__init__(self, *args, **kwargs)
        IntegerField.__init__(self, *args, **kwargs)