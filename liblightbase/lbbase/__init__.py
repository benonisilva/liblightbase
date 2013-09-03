
from liblightbase.lbbase import fields
import json
import voluptuous

class Base():
    """
    Defining a LB Base object
    """
    def __init__(self, name, description, password, color, content,
                index_export=False , index_url=None, index_time=None,
                doc_extract=False, extract_time=None):
        """
        Base attributes
        """
        self.name = name
        self.description = description
        self.password = password
        self.color = color
        self.content = content
        self.index_export = index_export
        self.index_url = index_url
        self.index_time = index_time
        self.doc_extract = doc_extract
        self.extract_time = extract_time

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, c):
        content_list = list()
        if type(c) is list:
            for value in c:
                if isinstance(value, fields.Field) or isinstance(value, fields.Group):
                    content_list.append(value)
                else:
                    msg = 'InstanceError This should be an instance of Field or Group. instead it is %s' % value
                    raise Exception(msg)
            self._content = content_list
        else:
            msg = 'Type Error: content must be a list instead of %s' % c
            raise Exception(msg)
            self._content = None

    @property
    def object(self):
        """ Builds base object 
        """
        return dict(
            content = [attr.object for attr in self.content],
            metadata = dict(
                name = self.name,
                description = self.description,
                password = self.password,
                color = self.color,
                index_export = self.index_export,
                index_url = self.index_url,
                index_time = self.index_time,
                doc_extract = self.doc_extract,
                extract_time = self.extract_time
            )
        )

    @property
    def schema(self):
        """ Builds base Schema
        """
        _schema = dict()
        for attr in self.content:
            required = getattr(attr, 'required', None)
            name = attr.name
            if required:
                if required.required is True:
                    name = voluptuous.Required(attr.name)
            _schema.update({ name: attr.schema })
        return voluptuous.Schema(_schema)

    @property
    def json(self):
        """ Builds base JSON
        """
        return json.dumps(self.object, ensure_ascii=True)
