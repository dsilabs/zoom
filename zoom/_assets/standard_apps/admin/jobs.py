"""
    administer background jobs
"""

from datetime import datetime

import zoom

class BackgroundController(zoom.Controller):

    def index(self):
        """Returns a list of background jobs"""

        jobs = zoom.sites.Site(zoom.system.site.path).background_jobs

        def describe_last_run(job):
            run = job.get_last_runtime()
            if not run:
                return 'Hasn\'t run yet'
            
            return run.describe(as_html=True)
        labels = 'Name', 'Cron', 'Next Scheduled Run', 'Last Run'
        content = zoom.browse(
            (
                (
                    job.qualified_name,
                    job.schedule or 'No schedule (always runs)',
                    'In ' + zoom.tools.how_long(datetime.now(), job.next_run_schedule),
                    describe_last_run(job)
                )
                for job in jobs
            ),
            labels=labels
        )

        title = 'Jobs <span class="meta"><small>alpha</small></span>'
        return zoom.page(content, title=title)

main = zoom.dispatch(BackgroundController)

