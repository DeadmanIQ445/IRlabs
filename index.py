import mongoengine
mongoengine.connect("engine")


class Inverted(mongoengine.Document):
    word = mongoengine.StringField()
    docs = mongoengine.ListField()
