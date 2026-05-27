import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name='agents.run_price_optimizer')
def run_price_optimizer():
    """Optimise les prix des catégories chaque nuit à minuit."""
    from .price_optimizer import price_optimizer
    try:
        result = price_optimizer.run()
        logger.warning('Price optimizer: %s', result)
        return result
    except Exception as exc:
        logger.error('Price optimizer error: %s', repr(exc), exc_info=True)
        raise


@shared_task(name='agents.run_fraud_detector')
def run_fraud_detector():
    """Scan anti-fraude toutes les heures."""
    from .fraud_detector import fraud_detector
    try:
        result = fraud_detector.run()
        logger.warning('Fraud detector: %s', result)
        return result
    except Exception as exc:
        logger.error('Fraud detector error: %s', repr(exc), exc_info=True)
        raise
