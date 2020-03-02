import mongoengine
mongoengine.connect("engine")


class Doc(mongoengine.Document):
    title = mongoengine.StringField()
    body = mongoengine.StringField()
    date = mongoengine.StringField()

    @classmethod
    def get_by_id(cls, id):
        return cls.objects.get(__id=id)
