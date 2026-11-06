from celery import shared_task
from .models import ImportJob
from .services import ExcelImporter

@shared_task
def process_import_job(job_id):
    try:
        job = ImportJob.objects.get(pk=job_id)
    except ImportJob.DoesNotExist:
        return
    importer = ExcelImporter(job)
    importer.run()