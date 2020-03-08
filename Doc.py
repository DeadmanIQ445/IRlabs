import mongoengine
mongoengine.connect("engine")


class Doc(mongoengine.Document):
    title = mongoengine.StringField()
    body = mongoengine.StringField()
    date = mongoengine.StringField()

    @classmethod
    def get_by_id(cls, id):
        return cls.objects.get(__id=id)

class DocR:
    def __init__(self, title=None, body=None, date=None, id=None, json=None):
        if json:
            self.title = json['title']
            self.body = json['body']
            self.date = json['date']
            self.id = json['id']
        else:
            self.title = title
            self.body = body
            self.date = date
            self.id = id
