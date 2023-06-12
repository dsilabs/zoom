
import logging
import model

from zoom.background import repeatedly

logger = logging.getLogger(__name__)

@repeatedly
def hello():
    logger.info('hello from test2 function with model reference')
    response = model.app()
    expecting = 'test2.app'
    logger.info('%s %s', response, response == expecting)
    return True
