import math
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class PlopPlopService:

    BASE_URL = 'https://plopplop.solutionip.app'

    def __init__(self):
        self.client_id  = settings.PLOPPLOP['CLIENT_ID']
        self.return_url = settings.PLOPPLOP['RETURN_URL']

    def create_payment(self, reference_id: str, montant: float, payment_method: str = 'all'):
        """
        Crée une transaction PlopPlop et retourne l'URL de redirection.
        payment_method: 'moncash' | 'natcash' | 'kashpaw' | 'all'
        Returns {'success': bool, 'url': str, 'transaction_id': str, 'error': str}
        """
        payload = {
            'client_id':      self.client_id,
            'refference_id':  str(reference_id),
            'montant':        math.ceil(float(montant)),
            'payment_method': payment_method,
            'url_retour':     self.return_url,
        }
        try:
            resp = requests.post(
                f'{self.BASE_URL}/api/paiement-marchand',
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get('status') is True:
                return {
                    'success': True,
                    'url': data.get('url'),
                    'transaction_id': str(data.get('transaction_id', '')),
                }
            return {'success': False, 'error': data.get('message', 'Erreur PlopPlop')}
        except requests.RequestException as e:
            logger.error(f'[PlopPlop] create_payment error: {e}')
            return {'success': False, 'error': str(e)}

    def verify_payment(self, reference_id: str):
        """
        Vérifie le statut d'un paiement PlopPlop.
        Returns {
            'success': bool, 'paid': bool,
            'montant': float, 'method': str,
            'id_transaction': str, 'date': str, 'heure': str,
            'error': str
        }
        """
        payload = {
            'client_id':     self.client_id,
            'refference_id': str(reference_id),
        }
        try:
            resp = requests.post(
                f'{self.BASE_URL}/api/paiement-verify',
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get('status') is True:
                return {
                    'success': True,
                    'paid': data.get('trans_status') == 'ok',
                    'montant': data.get('montant'),
                    'method': data.get('method', ''),
                    'id_transaction': str(data.get('id_transaction', '')),
                    'date': data.get('date', ''),
                    'heure': data.get('heure', ''),
                }
            return {'success': False, 'paid': False, 'error': data.get('message', 'Erreur PlopPlop')}
        except requests.RequestException as e:
            logger.error(f'[PlopPlop] verify_payment error: {e}')
            return {'success': False, 'paid': False, 'error': str(e)}
