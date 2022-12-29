from enum import Enum
import datetime
import os
from .db import db

class Status(str, Enum):
    NEW = "new"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"

class BoundingBoxes(db.EmbeddedDocument):
    x = db.FloatField(required=True)
    y = db.FloatField(required=True)
    width = db.FloatField(required=True)
    height = db.FloatField(required=True)

class Sentences(db.Document):
    page = db.ReferenceField('Pages', required=True)
    index = db.IntField(required=True)
    text = db.StringField()
    boundingBox = db.ListField(db.EmbeddedDocumentField('BoundingBoxes'))
    audioLength = db.FloatField()
    createdAt = db.DateTimeField(required=True)
    updatedAt = db.DateTimeField(required=True)
    def save(self, *args, **kwargs):
        if not self.createdAt:
            self.createdAt = datetime.datetime.now()
        self.updatedAt = datetime.datetime.now()
        return super(Sentences, self).save(*args, **kwargs)

class Pages(db.Document):
    chapter = db.ReferenceField("Chapters", required=True)
    index = db.IntField(required=True)
    pdfStatus = db.EnumField(Status, default=Status.NEW)
    imageStatus = db.EnumField(Status, default=Status.NEW)
    ocrStatus = db.EnumField(Status, default=Status.NEW)
    audioStatus = db.EnumField(Status, default=Status.NEW)
    createdAt = db.DateTimeField(required=True)
    updatedAt = db.DateTimeField(required=True)
    # meta = {
    #     'indexes': [
    #         {
    #             'fields': ['chapter', 'index'],
    #             'unique': True  
    #         }
    #     ]
    # }
    def get_page_folder_path(self):
        return f"book_{self.chapter.book.id}/chapter_{self.chapter.id}/page_{self.id}"
    def get_page_image_path(self):
        return f"book_{self.chapter.book.id}/chapter_{self.chapter.id}/page_{self.id}/page_{self.id}.png"
    def get_page_pdf_path(self):
        return f"book_{self.chapter.book.id}/chapter_{self.chapter.id}/page_{self.id}/page_{self.id}.pdf"
    def get_page_audio_path(self):
        return f"book_{self.chapter.book.id}/chapter_{self.chapter.id}/page_{self.id}/page_{self.id}.mp3"
    def save(self, *args, **kwargs):
        if not self.createdAt:
            self.createdAt = datetime.datetime.now()
        self.updatedAt = datetime.datetime.now()
        return super(Pages, self).save(*args, **kwargs)
    
class Chapters(db.Document):
    book = db.ReferenceField("Books", required=True)
    name = db.StringField(required=True)
    index = db.IntField(required=True)  
    # pdfStatus = db.EnumField(Status, default=Status.NEW)
    createdAt = db.DateTimeField(required=True)
    updatedAt = db.DateTimeField(required=True)
    # meta = {
    #     'indexes': [
    #         {
    #             'fields': ['book', 'index'],
    #             'unique': True  
    #         }
    #     ]
    # }
    def get_chapter_folder_path(self):
        return f"book_{self.book.id}/chapter_{self.id}"
    def save(self, *args, **kwargs):
        if not self.createdAt:
            self.createdAt = datetime.datetime.now()
        self.updatedAt = datetime.datetime.now()
        return super(Chapters, self).save(*args, **kwargs)
    def check_status(self, attribute):
        if any(page[attribute] == Status.ERROR for page in self.pages):
            return "error"
        elif all(page[attribute] == Status.READY for page in self.pages):
            return "ready"
        elif any(page[attribute] == Status.PROCESSING for page in self.pages):
            return "processing"
        else:
            return "new"
    @property
    def status(self):
        return {
            "pdf_status" : self.check_status("pdf_status"),
            "image_status" : self.check_status("image_status"),
            "ocr_status"  : self.check_status("ocr_status"),
            "audio_status" : self.check_status("audio_status")
        }


class Books(db.Document):
    title = db.StringField(required=True)
    authors = db.ListField(required=True)
    categories = db.ListField(required=True)
    image = db.URLField()
    description = db.StringField(required=True)
    createdAt = db.DateTimeField(required=True)
    updatedAt = db.DateTimeField(required=True)
    def get_book_pdf_path(self):
        return f"book_{self.id}/book_{self.id}.pdf"

Chapters.register_delete_rule(Pages, 'chapter', db.CASCADE)
Pages.register_delete_rule(Sentences, 'page', db.CASCADE)