"""
    Background job runtime management and registry.

    Applications register background jobs by including a background.py
    module in their application folder in which functions are regsitered
    using the cron function provided here.

    Once per tick (usually a minute) Zoom scans all of the applications
    for each site looking for background.py modules that contain registered
    jobs.  Those jobs are then registered in the BackgroundJob entity store
    where they are visible via the /admin/jobs dashboard.

"""

import os
import sys
import logging
import inspect
import hashlib
import importlib
import traceback

from datetime import datetime
from croniter import croniter

import zoom
from zoom.store import Entity, store_of

logger = logging.getLogger(__name__)

# Registrars. Note these will not work unless the module is imported
# in a call to load_app_background_jobs.
_job_set = None

class BackgroundJobPlaceholder(Entity):
    """Background Job"""

    @property
    def job_id(self):
        return self._id


class BackgroundJob:

    def __init__(self, uow, uow_source, schedule):
        self.job_id = None
        self.created = None
        self.uow = uow
        self.uow_source = uow_source
        self.schedule = schedule
        self.app = None
        self.last_run = None
        self.last_finished = None
        self.last_run_result = None
        self.last_run_status = None

    @property
    def qualified_name(self):
        return '{}/{}:{}'.format(
            self.app.site.name,
            self.app.name,
            self.uow.__name__,
        )

    @property
    def name(self):
        return '{}:{}'.format(
            self.app.name,
            self.uow.__name__,
        )

    @property
    def status(self):
        return 'ready'

    @property
    def trigger(self):
        return self.schedule or 'No schedule (always runs)'

    @property
    def next_run(self):
        if not self.schedule:
            return datetime.now()
        last_run = self.last_finished or self.created or datetime.now()
        return croniter(self.schedule, last_run).get_next(datetime)

    @property
    def uow_signature(self):
        return hashlib.md5(self.uow_source.encode('utf-8')).hexdigest()

    def load(self):
        """Load Job persistent variables"""
        store = store_of(BackgroundJobPlaceholder)
        record = store.first(qualified_name=self.qualified_name)
        if record:
            self.job_id = record.job_id
            self.created = record.created
            self.last_run = record.last_run
            self.last_finished = record.last_finished
            self.last_run_result = record.last_run_result
            self.last_run_status = record.last_run_status
        else:
            self.created = zoom.tools.now()
            self.job_id = store.put(
                BackgroundJobPlaceholder(
                    qualified_name=self.qualified_name,
                    site=self.app.site.name,
                    created=self.created,
                    last_run=self.last_run,
                    last_run_result=self.last_run_result,
                    last_run_status=self.last_run_status
                )
            )

    def save(self):
        store = store_of(BackgroundJobPlaceholder)
        record = store.first(qualified_name=self.qualified_name)

        if record is None:
            raise Exception('job record missing')

        record.update(
            last_run=self.last_run,
            last_finished=self.last_finished,
            last_run_result=self.last_run_result,
            last_run_status=self.last_run_status,
        )
        store.put(record)

    def __repr__(self):
        return '<BackgroundJob name="%s" schedule="%s">'%(
            self.uow.__name__, self.schedule
        )


def cron(schedule):
    """decorator to schedule a job to be run in the background

    Use to decorate a function in background.py in any app to have
    that function be executed on the specified cron schedule,
    """
    def register(job_fn):
        if _job_set is not None:
            _job_set.append(BackgroundJob(
                job_fn, inspect.getsource(job_fn), schedule
            ))
        return job_fn
    return register

def frequently(job_fn):
    """decorator to schedule a job to run every fifteen mintues"""
    return cron('*/15 * * * *')(job_fn)

def always(job_fn):
    """decorator to schedule a job to run on every execution cycle"""
    return cron('* * * * *')(job_fn)

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
    sys.path.insert(0, app.path)
    # Remove any existing background module from sys.modules (probably this
    # module), to prevent that cache from trapping the import we're about to
    # do.
    if 'background' in sys.modules:
        del sys.modules['background']

    # Pop the CWD and chdir to the app directory.
    base_dir = os.getcwd()
    os.chdir(app.path)
    try:

        # Import the background module from the app. This has the side effect of
        # allowing the job registrars to populate _job_set.
        importlib.import_module('background', app.path)

    except BaseException:
        logger.error('unable to load background job %r', app.path)
        return set()

    finally:
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


class BackgroundJobResult(Entity):
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


def purge_old_job_results():
    """Purge old background job results"""

    cmd = """
    delete from attributes
    where kind = 'background_job_result' and row_id not in (
        select row_id from (
            select distinct row_id from attributes
            where kind = 'background_job_result'
            order by row_id desc
            limit 100  -- keep this many result records
        ) foo
    )
    """

    logger.info('purging old background job results')
    db = zoom.get_db()
    db(cmd)
    logger.debug('finished purging old background job results')


def reset_modules():
    """reset the modules to a known starting set

    memorizes the modules currently in use and then removes any other
    modules when called again
    """
    # pylint: disable=global-variable-undefined, invalid-name
    global init_modules
    if 'init_modules' in globals():
        for module in [x for x in sys.modules if x not in init_modules]:
            del sys.modules[module]
    else:
        init_modules = list(sys.modules.keys())


def run_background_jobs(app):

    reset_modules()

    site = zoom.system.site

    jobs_list = app.background_jobs
    if not jobs_list:
        return None

    logger.debug(
        'scanning %d background jobs for %s/%s',
        len(jobs_list),
        site.name,
        app.name
    )
    tick_time = datetime.now()
    failed = succeeded = total = 0

    for job in jobs_list:

        job.load()

        if tick_time < job.next_run:
            continue

        # Execute the job.
        logger.info('running background job %s', job.qualified_name)
        start_time = zoom.tools.now()

        # Run the jobs unit of work with safety.
        return_value = runtime_error = str()
        try:

            save_cwd = os.getcwd()
            os.chdir(app.path)
            try:
                try:
                    return_value = job.uow()
                finally:
                    # re-activate the site in case the background
                    # job has activated a different site
                    site.activate()
            finally:
                os.chdir(save_cwd)

            logger.debug('\treturned: %s', return_value)
            status = 'success'
            succeeded += 1
        except BaseException as ex:
            runtime_error = ''.join(traceback.format_exception(
                ex.__class__, ex, ex.__traceback__
            ))
            logger.critical(
                '\tjob %s failed!\n%s',
                job.qualified_name,
                runtime_error.join(('='*10 + '\n',)*2)
            )
            status = 'failed'
            return_value = None
            failed += 1
        total += 1

        finish_time = zoom.tools.now()

        job.last_run = start_time
        job.last_run_result = return_value
        job.last_run_status = status
        job.last_finished = finish_time
        job.save()

        job_log = store_of(BackgroundJobResult)
        job_log.put(BackgroundJobResult(
            job_qualified_name=job.qualified_name,
            job_site=job.app.site.name,
            job_name=job.name,
            start_time=start_time,
            finish_time=finish_time,
            return_value=return_value,
            run_status=status,
            runtime_error=runtime_error
        ))

    logger.debug('ran %d jobs (%d succeeded, %d failed)', \
            total, succeeded, failed)


# Runtime inspection.
def read_job_log():
    return store_of(BackgroundJobResult).all()
