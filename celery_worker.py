import os
from app import celery_app, app

if __name__ == '__main__':
    with app.app_context():
        celery_app.start()
      
