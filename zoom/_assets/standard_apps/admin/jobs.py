"""
    administer background jobs
"""

import zoom


def timespan(time1, time2):
    if time1 and time2:
        return time1 - time2
    return ''


class BackgroundController(zoom.Controller):

    def index(self):
        """Returns a list of background jobs"""

        actions = []
        if zoom.system.user.is_admin:
            actions.append(('Clear Placeholders', 'jobs/clear'))

        jobs = zoom.sites.Site(zoom.system.site.path).background_jobs
        lookup = {
            job.qualified_name: job
            for job in zoom.store_of(zoom.background.BackgroundJobPlaceholder)
        }

        when = zoom.helpers.when

        labels = (
            'Name', 'Status', 'Trigger', 'Next Run', 'Last Run',
            'Elapsed', 'Last Run Status'
        )

        content = zoom.browse(
            (
                (
                    job.name,
                    job.status,
                    job.trigger,
                    when(job.next_run),
                    when(
                        lookup.get(job.qualified_name) and
                        lookup.get(job.qualified_name).last_run
                    ) or 'never',
                    timespan(
                        lookup.get(job.qualified_name).last_finished
                        if job.qualified_name in lookup else None,
                        lookup[job.qualified_name].last_run
                        if job.qualified_name in lookup else None,
                    ),
                    lookup[job.qualified_name].last_run_status
                    if job.qualified_name in lookup and
                    lookup[job.qualified_name].last_run_status
                    else '-'
                )
                for job in jobs
            ),
            labels=labels,
        )

        title = 'Jobs'
        return zoom.page(content, title=title,actions=actions)

    @zoom.authorize('administrators')
    def clear(self):
        zoom.store_of(zoom.background.BackgroundJobPlaceholder).zap()
        return zoom.home('jobs')

main = zoom.dispatch(BackgroundController)

