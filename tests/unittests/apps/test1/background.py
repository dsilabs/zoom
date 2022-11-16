
import logging
from zoom.background import cron
import model

logger = logging.getLogger(__name__)

@cron('* * * * *')
def hello():
    logger.info('hello from basic function')


@cron('* * * * *')
def hello2():
    logger.info('hello from test1 function with model reference')
    response = model.app()
    expecting = 'test1.model.app:test1.module1.get_text'
    logger.warning('%s %s', response, response == expecting)
