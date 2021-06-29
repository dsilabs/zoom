"""
    test background
"""

import unittest

import zoom
from zoom.background import BackgroundJobResult, purge_old_job_results


class TestBackground(unittest.TestCase):

    def setUp(self):
        zoom.system.site = zoom.sites.Site()
        # zoom.system.request = zoom.utils.Bunch(
        #     site=zoom.system.site,
        #     app=zoom.utils.Bunch(templates_paths=[], url='/app1')
        # )
        # zoom.system.providers = [{}]

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
