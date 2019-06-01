"""
    administer background jobs
"""

import zoom

class BackgroundController(zoom.Controller):

    def index(self):
        """Returns a list of background jobs"""

        jobs = zoom.sites.Site(zoom.system.site.path).get_background_jobs()

        labels = 'Name', 'Path', 'Cron', 'Scheduled', 'Status'
        content = zoom.browse(
            (
                (
                    job.name,
                    job.path,
                    job.cron,
                    job.scheduled,
                    job.status,
                )
                for job in jobs
            ),
            labels=labels
        )

        title = 'Jobs <span class="meta"><small>alpha</small></span>'
        return zoom.page(content, title=title)

main = zoom.dispatch(BackgroundController)

