class InternalServerError(Exception):
    pass

class SchemaValidationError(Exception):
    pass

class ChapterAlreadyExistsError(Exception):
    pass

class UpdatingChapterError(Exception):
    pass

class DeletingChapterError(Exception):
    pass

class ChapterNotExistsError(Exception):
    pass


errors = {
    "InternalServerError": {
        "message": "Something went wrong",
        "status": 500
    },
     "SchemaValidationError": {
         "message": "Request is missing required fields",
         "status": 400
     },
     "ChapterAlreadyExistsError": {
         "message": "Chapter with given name already exists",
         "status": 400
     },
     "UpdatingChapterError": {
         "message": "Updating Chapter added by other is forbidden",
         "status": 403
     },
     "DeletingChapterError": {
         "message": "Deleting Chapter added by other is forbidden",
         "status": 403
     },
     "ChapterNotExistsError": {
         "message": "Chapter with given id doesn't exists",
         "status": 400
     }
}