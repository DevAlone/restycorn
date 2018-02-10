from .base_serializer import BaseSerializer
from .exceptions import SerializationError


class PostgreSQLSerializer(BaseSerializer):
    def __init__(self, fields):
        self.fields = {
            field if ' as ' not in field else field.split(' as ', maxsplit=2)[0]:
                field if ' as ' not in field else field.split(' as ', maxsplit=2)[1]
            for field in fields
        }
        print(self.fields)

    def serialize(self, item) -> dict:
        result = {}
        for key, val in item.items():
            if key in self.fields:
                result[self.fields[key]] = val

        if len(result) != len(self.fields):
            raise SerializationError()

        return result
