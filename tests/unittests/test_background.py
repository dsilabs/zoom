"""
    test background
"""

import unittest

import zoom
from zoom.background import BackgroundJobResult, purge_old_job_results


class TestBackground(unittest.TestCase):

    def setUp(self):
        zoom.system.site = zoom.sites.Site()

    def test_purge(self):

        job_log = zoom.store_of(BackgroundJobResult)

        now = zoom.tools.now()

        # clear out all old job results
        job_log.zap()

        NUMBER_TO_GENERATE = 110

        for i in range(NUMBER_TO_GENERATE):
            job_log.put(
                BackgroundJobResult(
                    job_qualified_name='job_qualified_name',
                    job_name='job_name',
                    start_time=now,
                    finish_time=now,
                    return_value=0,
                    run_status='C',
                    runtime_error=None
                )
            )

        self.assertEqual(len(job_log), NUMBER_TO_GENERATE)

        purge_old_job_results()

        self.assertEqual(len(job_log), 100)

    def test_instance_jobs_exist(self):
        instance = zoom.instances.Instance()
        test_apps_path = zoom.tools.zoompath('tests', 'unittests', 'apps')
        names = []
        for site in instance.sites.values():
            site.apps_paths.append(test_apps_path)
            for job in site.background_jobs:
                names.append(job.qualified_name)
            del site.apps_paths[-1]
        self.assertEqual(
            names,
            [
                'localhost/sample:tick',
                'localhost/test2:hello',
                'localhost/test1:hello',
                'localhost/test1:hello2'
            ]
        )

    def test_site_background_jobs_exist(self):
        site = zoom.sites.Site()
        site.apps_paths.append(zoom.tools.zoompath('tests', 'unittests', 'apps'))
        names = sorted([job.name for job in site.background_jobs])
        self.assertEqual(
            names,
            ['sample:tick', 'test1:hello', 'test1:hello2', 'test2:hello']
        )