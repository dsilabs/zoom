"""Background job runtime management and registry."""

import os
import sys
import time
import logging
import inspect
import hashlib
import importlib
import traceback

from datetime import datetime
from croniter import croniter

from zoom.store import Entity, store_of

logger = logging.getLogger(__name__)

# Registrars. Note these will not work unless the module is imported
# in a call to load_app_background_jobs.
_job_set = None

class BackgroundJobRecord_(Entity):
    """
    qualified_name = None
    uow_signature = None
    next_run_schedule = None
    """
BackgroundJobRecord = BackgroundJobRecord_

class BackgroundJob:

    def __init__(self, uow, uow_source, schedule):
        self.uow = uow
        self.uow_source = uow_source
        self.schedule = schedule
        self.app = None

    @property
    def qualified_name(self):
        return '/'.join((
            self.app.site.name, self.app.name, self.uow.__name__
        ))

    @property
    def uow_signature(self):
        return hashlib.md5(self.uow_source.encode('utf-8')).hexdigest()

    @property
    def next_run_schedule(self):
        if not self.schedule:
            return datetime.now()
        return croniter(self.schedule, datetime.now()).get_next(datetime)

    def get_record(self):
        return store_of(BackgroundJobRecord).first(qualified_name=self.qualified_name)

    def get_runtimes(self):
        return store_of(JobRuntime).find(job_qualified_name=self.qualified_name)

    def get_last_runtime(self):
        runtimes = self.get_runtimes()
        last = None
        for runtime in runtimes:
            if not last or runtime.timestamp_dt > last.timestamp_dt:
                last = runtime

        return last

    def save_record(self):
        store = store_of(BackgroundJobRecord)
        existing = self.get_record()
        if existing:
            store.delete(existing._id)
        store.put(BackgroundJobRecord(
            qualified_name=self.qualified_name,
            uow_signature=self.uow_signature,
            next_run_schedule=self.next_run_schedule.isoformat()
        ))

    def has_changed_since_record(self):
        previous = self.get_record()
        return (
            not previous or
            previous.uow_signature != self.uow_signature
        )

    def __repr__(self):
        return '<BackgroundJob name="%s" schedule="%s">'%(
            self.uow.__name__, self.schedule
        )

def cron(schedule):
    def register(job_fn):
        if _job_set is not None:
            _job_set.append(BackgroundJob(
                job_fn, inspect.getsource(job_fn), schedule
            ))
        return job_fn
    return register

def frequently(job_fn):
    return cron('*/5 * * * *')(job_fn)

def always(job_fn):
    return cron(None)(job_fn)

# Discovery.
def load_app_background_jobs(app):
    """Load the background jobs for the given app from that apps background.py
    module."""
    global _job_set

    # Ensure we have a background module.
    background_module_path = os.path.join(app.path, 'background.py')
    if not os.path.isfile(background_module_path):
        return list()

    # Initialize the job registrar storage. This is extended by registration
    # functions when initialized like this.
    _job_set = list()

    # Add CWD to import path so we can import background modules after we chdir
    # into app directories.
    sys.path.append('.')
    # Remove any existing background module from sys.modules (probably this
    # module), to prevent that cache from trapping the import we're about to
    # do.
    if 'background' in sys.modules:
        del sys.modules['background']

    # Pop the CWD and chdir to the app directory.
    base_dir = os.getcwd()
    os.chdir(app.path)

    # Import the background module from the app. This has the side effect of
    # allowing the job registrars to populate _job_set.
    importlib.import_module('background', app.path)

    # Return to our previous CWD.
    os.chdir(base_dir)

    # Remove our modification from the import path.
    del sys.path[-1]

    # Un-initialize the _job_set global to prevent weird behaviour in the case
    # of app code importing symbols from their background.py modules.
    job_set = _job_set
    _job_set = None

    # Annotate each collected job with it's parent app.
    for job in job_set: # pylint: disable=not-an-iterable
        job.app = app

    return job_set

# Runtime management.
class JobRuntime_(Entity):
    """
    job_qualified_name = None
    timestamp = None
    elapsed_time = None
    return_value = None
    runtime_error = None
    """

    @property
    def timestamp_dt(self):
        return datetime.fromisoformat(self.timestamp)

    def describe(self, as_html=False):
        return_desc = None
        if not self.runtime_error:
            return_desc = (
                '<strong>Returned: </strong> %s'
                if as_html else
                'Returned: %s'
            )%repr(self.return_value)
        else:
            return_desc = (
                '<strong>Errored: </strong> %s'
                if as_html else
                'Errored: [%s]'
            )%self.runtime_error.split('\n')[-2]

        timing_desc = (
            '<i>in %sms at %s</i>'
            if as_html else
            'in %sms at %s'
        )%(round(self.elapsed_time*1000), self.timestamp)

        return ' '.join((return_desc, timing_desc))
JobRuntime = JobRuntime_

def run_background_jobs(site, app):

    jobs_list = app.background_jobs
    if not len(jobs_list):
        return

    logger.info('Running %d background jobs for %s/%s', len(jobs_list), site.name, app.name)
    tick_time = datetime.now()
    exec_store = store_of(JobRuntime)
    failed = succeeded = total = 0

    for job in jobs_list:
        # Decide whether the job should execute.
        should_run = False
        if job.has_changed_since_record():
            # If we've never seen this job for runtime, or it's source has
            # cosmetically changed since we last did, run it for sure.
            should_run = True
        else:
            # Run it if the next schedule we created when we last saw it here
            # has been passed.
            job_record = job.get_record()
            next_run = datetime.fromisoformat(job_record.next_run_schedule)
            should_run = tick_time >= next_run

        if not should_run:
            logger.debug('Skipping background job %s', job.qualified_name)
            continue

        # Execute the job.
        logger.debug('Running %s', job.qualified_name)
        start_time = time.time()

        # Run the jobs unit of work with safety.
        return_value = runtime_error = str()
        try:
            return_value = job.uow()
            logger.debug('\tReturned: %s', return_value)
            succeeded += 1
        except BaseException as ex:
            runtime_error = ''.join(traceback.format_exception(
                ex.__class__, ex, ex.__traceback__
            ))
            logger.critical('\tJob %s failed!\n%s',
                job.qualified_name,
                runtime_error.join(('='*10 + '\n',)*2)
            )
            failed += 1
        total += 1

        # Record the execution and update the job record.
        job.save_record()
        exec_store.put(JobRuntime(
            job_qualified_name=job.qualified_name,
            timestamp=datetime.now().isoformat(),
            elapsed_time=time.time() - start_time,
            return_value=str(return_value),
            runtime_error=runtime_error
        ))

    logger.debug('Ran %d jobs (%d succeeded, %d failed)', \
            total, succeeded, failed)

# Runtime inspection.
def read_job_log():
    return store_of(JobRuntime).all()
