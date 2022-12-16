class InternalServerError(Exception):
    pass

class SchemaValidationError(Exception):
    pass

class PageAlreadyExistsError(Exception):
    pass

class UpdatingPageError(Exception):
    pass

class DeletingPageError(Exception):
    pass

class PageNotExistsError(Exception):
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
     "PageAlreadyExistsError": {
         "message": "Page with given name already exists",
         "status": 400
     },
     "UpdatingPageError": {
         "message": "Updating Page added by other is forbidden",
         "status": 403
     },
     "DeletingPageError": {
         "message": "Deleting Page added by other is forbidden",
         "status": 403
     },
     "PageNotExistsError": {
         "message": "Page with given id doesn't exists",
         "status": 400
     }
}