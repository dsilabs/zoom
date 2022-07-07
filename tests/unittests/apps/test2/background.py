
import logging
import model

from zoom.background import cron

logger = logging.getLogger(__name__)

@cron('* * * * *')
def hello():
    logger.info('hello from test2 function with model reference')
    response = model.app()
    expecting = 'test2.app'
    logger.info('%s %s', response, response == expecting)
    return True
