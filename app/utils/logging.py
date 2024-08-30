# import logging
# import json
# from pythonjsonlogger import jsonlogger

# class CustomJsonFormatter(jsonlogger.JsonFormatter):
#     def format(self, record):
#         log_record = {
#             "level": record.levelname,
#             "message": record.getMessage(),
#             "timestamp": self.formatTime(record, self.datefmt),
#             "module": record.module,
#             "function": record.funcName,
#             "line": record.lineno,
#         }
#         return json.dumps(log_record)

# def get_logger(name: str):
#     logger = logging.getLogger(name)
#     logger.setLevel(logging.INFO)

#     if not logger.hasHandlers():
#         handler = logging.StreamHandler()
#         handler.setFormatter(CustomJsonFormatter())
#         logger.addHandler(handler)

#     return logger

# def configure_uvicorn_logging():
#     logger = logging.getLogger("uvicorn")
#     logger.setLevel(logging.INFO)
    
#     # Clear existing handlers to prevent double logging
#     if logger.hasHandlers():
#         logger.handlers.clear()
    
#     # Set up the JSON formatter
#     handler = logging.StreamHandler()
#     handler.setFormatter(CustomJsonFormatter())
#     logger.addHandler(handler)
    
#     # Ensure access and error logs use the same formatter
#     access_logger = logging.getLogger("uvicorn.access")
#     error_logger = logging.getLogger("uvicorn.error")
#     uvicorn_logger = logging.getLogger("uvicorn")
    
#     for log in [access_logger, error_logger, uvicorn_logger]:
#         log.setLevel(logging.INFO)
#         if log.hasHandlers():
#             log.handlers.clear()
#         log.addHandler(handler)

# def configure_celery_logging():
#     """Configure Celery to use the custom JSON logger."""
#     celery_logger = logging.getLogger('celery')
#     celery_logger.setLevel(logging.INFO)

#     # Clear any existing handlers
#     celery_logger.handlers = []

#     # Add the custom JSON handler
#     handler = logging.StreamHandler()
#     handler.setFormatter(CustomJsonFormatter())
#     celery_logger.addHandler(handler)