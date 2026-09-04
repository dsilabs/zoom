"""
    administer background jobs
"""

import zoom


def timespan(time1, time2):
    if time1 and time2:
        return time1 - time2
    return ''


def current_jobs():
    return zoom.sites.Site(zoom.system.site.path).background_jobs


class BackgroundController(zoom.Controller):

    def index(self):
        """Returns a list of background jobs"""

        jobs = current_jobs()
        current_names = set(job.qualified_name for job in jobs)
        lookup = {
            job.qualified_name: job
            for job in zoom.store_of(zoom.background.BackgroundJobPlaceholder)
        }

        result_counts = {}
        latest = {}
        for result in zoom.store_of(zoom.background.BackgroundJobResult):
            name = result.job_qualified_name
            result_counts[name] = result_counts.get(name, 0) + 1
            prev = latest.get(name)
            if prev is None or (result._id or 0) > (prev._id or 0):
                latest[name] = result

        leftover_names = sorted(
            name for name in result_counts if name not in current_names
        )
        leftover_count = sum(result_counts[name] for name in leftover_names)

        actions = []
        if zoom.system.user.is_admin:
            actions.append(('Clear Placeholders', 'jobs/clear'))
            if leftover_count:
                actions.append(('Clear Leftover Results', 'jobs/clear_leftovers'))

        when = zoom.helpers.when

        def run_columns(qualified_name):
            record = lookup.get(qualified_name)
            if record:
                return (
                    when(record.last_run) or 'never',
                    timespan(record.last_finished, record.last_run),
                    record.last_run_status or '-',
                )
            result = latest.get(qualified_name)
            if result:
                return (
                    when(getattr(result, 'start_time', None)) or 'never',
                    timespan(
                        getattr(result, 'finish_time', None),
                        getattr(result, 'start_time', None),
                    ),
                    getattr(result, 'run_status', None) or '-',
                )
            return 'never', '', '-'

        rows = []
        for job in jobs:
            last_run, elapsed, status = run_columns(job.qualified_name)
            rows.append((
                job.name,
                job.status,
                job.trigger,
                when(job.next_run),
                last_run,
                elapsed,
                status,
                result_counts.get(job.qualified_name, 0),
            ))

        for name in leftover_names:
            last_run, elapsed, status = run_columns(name)
            result = latest[name]
            rows.append((
                getattr(result, 'job_name', None) or name,
                'inactive',
                '-',
                '-',
                last_run,
                elapsed,
                status,
                result_counts[name],
            ))

        job_count = len(jobs)
        job_label = 'job' if job_count == 1 else 'jobs'
        listed_results = sum(
            result_counts.get(job.qualified_name, 0) for job in jobs
        )
        result_label = 'job result' if listed_results == 1 else 'job results'
        footer = '%s %s, %s %s' % (
            job_count, job_label, listed_results, result_label
        )
        if leftover_count:
            footer += ', %s leftover' % leftover_count

        labels = (
            'Name', 'Status', 'Trigger', 'Next Run', 'Last Run',
            'Elapsed', 'Last Run Status', 'Results'
        )

        content = zoom.browse(rows, labels=labels, footer=footer)

        title = 'Jobs'
        return zoom.page(content, title=title, actions=actions)

    @zoom.authorize('administrators')
    def clear(self):
        zoom.store_of(zoom.background.BackgroundJobPlaceholder).zap()
        return zoom.home('jobs')

    @zoom.authorize('administrators')
    def clear_leftovers(self):
        current_names = set(job.qualified_name for job in current_jobs())
        job_log = zoom.store_of(zoom.background.BackgroundJobResult)
        for result in list(job_log):
            if result.job_qualified_name not in current_names:
                job_log.delete(result._id)
        return zoom.home('jobs')

main = zoom.dispatch(BackgroundController)
