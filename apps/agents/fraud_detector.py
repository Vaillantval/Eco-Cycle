import json
import logging
from datetime import timedelta

from anthropic import Anthropic
from django.conf import settings
from django.db.models import Count, F
from django.utils import timezone

from apps.accounts.models import User
from apps.marketplace.models import Auction, Bid, Order
from apps.notifications.models import Notification
from apps.waste.models import WasteListing

logger = logging.getLogger(__name__)

FRAUD_DETECTOR_PROMPT = """
Tu es un agent de sécurité spécialisé dans la détection de fraudes
sur une marketplace de recyclage en Haïti.

Comportements frauduleux à détecter :
1. LISTINGS_EN_MASSE : même user soumet 10+ listings similaires en 24h
2. AUTO_ENCHERE : user enchérit sur ses propres listings
3. PRIX_ABERRANT : valeur estimée 10x supérieure au prix marché normal
4. COMPTE_FANTOME : compte créé < 24h avec activité intense immédiate
5. ENCHERE_FICTIVE : pattern de fausses enchères pour faire monter le prix

Pour chaque anomalie détectée, retourne un niveau de risque :
- LOW : surveiller, ne pas agir
- MEDIUM : notifier admin
- HIGH : bloquer immédiatement + notifier admin

Retourne UNIQUEMENT un JSON valide sans markdown :
{
  "anomalies": [
    {
      "type": "LISTINGS_EN_MASSE|AUTO_ENCHERE|PRIX_ABERRANT|COMPTE_FANTOME|ENCHERE_FICTIVE",
      "risk_level": "LOW|MEDIUM|HIGH",
      "user_id": "uuid",
      "user_email": "email",
      "description": "Description précise de l'anomalie",
      "evidence": "Données qui prouvent la fraude",
      "recommended_action": "Action recommandée",
      "auto_block": true
    }
  ],
  "scan_summary": "Résumé du scan",
  "total_anomalies": 0
}
"""


class FraudDetectorAgent:

    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def gather_suspicious_activity(self) -> dict:
        last_24h = timezone.now() - timedelta(hours=24)
        suspicious = {}

        # 1. Listings en masse (10+ en 24h par le même user)
        bulk = (
            WasteListing.objects
            .filter(created_at__gte=last_24h)
            .values('user__id', 'user__email')
            .annotate(count=Count('id'))
            .filter(count__gte=10)
        )
        if bulk:
            suspicious['bulk_listings'] = list(bulk)

        # 2. Auto-enchères (user enchérit sur son propre listing)
        auto_bids = (
            Bid.objects
            .filter(created_at__gte=last_24h, bidder=F('auction__seller'))
            .select_related('bidder', 'auction__listing')
        )
        if auto_bids.exists():
            suspicious['auto_bids'] = [
                {
                    'user_id': str(bid.bidder.id),
                    'user_email': bid.bidder.email,
                    'auction_id': str(bid.auction.id),
                    'amount': float(bid.amount),
                }
                for bid in auto_bids
            ]

        # 3. Prix aberrants (valeur IA > 5x le plafond attendu de la catégorie)
        aberrant = []
        for listing in (
            WasteListing.objects
            .filter(created_at__gte=last_24h, ai_estimated_value__isnull=False)
            .select_related('user', 'category')
        ):
            if listing.category and listing.ai_estimated_value:
                expected_max = (
                    float(listing.category.base_price_per_kg)
                    * float(listing.quantity_kg or 1)
                    * 5
                )
                ai_val = float(listing.ai_estimated_value)
                if ai_val > expected_max:
                    aberrant.append({
                        'listing_id': str(listing.id),
                        'title': listing.title,
                        'user_id': str(listing.user.id),
                        'user_email': listing.user.email,
                        'ai_value': ai_val,
                        'expected_max': expected_max,
                        'ratio': round(ai_val / expected_max, 2),
                    })
        if aberrant:
            suspicious['overpriced_listings'] = aberrant

        # 4. Comptes fantômes (créés < 24h avec activité intense)
        ghost = []
        for user in User.objects.filter(date_joined__gte=last_24h):
            listings_count = WasteListing.objects.filter(user=user).count()
            bids_count = Bid.objects.filter(bidder=user).count()
            if listings_count >= 5 or bids_count >= 10:
                ghost.append({
                    'user_id': str(user.id),
                    'user_email': user.email,
                    'created_at': user.date_joined.isoformat(),
                    'listings_count': listings_count,
                    'bids_count': bids_count,
                })
        if ghost:
            suspicious['ghost_accounts'] = ghost

        # 5. Enchères excessives (20+ enchères en 24h par le même user)
        excessive = (
            Bid.objects
            .filter(created_at__gte=last_24h)
            .values('bidder_id')
            .annotate(bid_count=Count('id'))
            .filter(bid_count__gte=20)
        )
        if excessive:
            suspicious['excessive_bidding'] = list(excessive)

        return suspicious

    def run(self) -> dict:
        suspicious_data = self.gather_suspicious_activity()

        if not suspicious_data:
            return {
                'status': 'clean',
                'message': 'Aucune activité suspecte détectée.',
                'scanned_at': timezone.now().isoformat(),
            }

        response = self.client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=1024,
            system=FRAUD_DETECTOR_PROMPT,
            messages=[{
                'role': 'user',
                'content': (
                    'Analyse ces activités suspectes détectées sur EcoCycle '
                    'au cours des dernières 24 heures :\n\n'
                    + json.dumps(suspicious_data, indent=2, ensure_ascii=False)
                    + '\n\nÉvalue le niveau de risque et recommande les actions appropriées.'
                ),
            }],
        )

        result = json.loads(response.content[0].text.strip())

        # Bloquer automatiquement les comptes HIGH
        blocked_users = []
        for anomaly in result.get('anomalies', []):
            if anomaly.get('auto_block') and anomaly['risk_level'] == 'HIGH':
                try:
                    user = User.objects.get(id=anomaly['user_id'])
                    user.is_active = False
                    user.save()
                    blocked_users.append({'user': user.email, 'reason': anomaly['description']})
                except User.DoesNotExist:
                    pass

        # Notifier admins pour MEDIUM et HIGH
        medium_high = [
            a for a in result.get('anomalies', [])
            if a['risk_level'] in ('MEDIUM', 'HIGH')
        ]
        if medium_high:
            admins = User.objects.filter(role='admin', is_active=True)
            for admin in admins:
                Notification.objects.create(
                    user=admin,
                    notification_type='system',
                    title=f'🚨 {len(medium_high)} anomalie(s) détectée(s)',
                    message=result.get('scan_summary', ''),
                    data={'anomalies': medium_high, 'blocked_users': blocked_users},
                )
                from apps.notifications.email_service import EmailService
                EmailService._send(
                    admin.email,
                    f'[EcoCycle Sécurité] {len(medium_high)} anomalie(s) détectée(s)',
                    self._build_report_html(medium_high, blocked_users),
                )

        return {
            'status': 'anomalies_found',
            'total_anomalies': result.get('total_anomalies', 0),
            'blocked_users': blocked_users,
            'medium_high_count': len(medium_high),
            'summary': result.get('scan_summary'),
        }

    def _build_report_html(self, anomalies: list, blocked: list) -> str:
        rows = ''.join(
            f"""<tr>
                <td style="color:{'#ef4444' if a['risk_level']=='HIGH' else '#f07c1a'}">
                  <b>{a['risk_level']}</b>
                </td>
                <td>{a['type']}</td>
                <td>{a.get('user_email','N/A')}</td>
                <td>{a['description']}</td>
                <td>{a['recommended_action']}</td>
              </tr>"""
            for a in anomalies
        )
        blocked_html = ''
        if blocked:
            blocked_html = '<h3 style="color:#ef4444">Comptes bloqués automatiquement :</h3>'
            blocked_html += ''.join(f'<p>🚫 {b["user"]} — {b["reason"]}</p>' for b in blocked)
        return f"""
        <h2>🚨 Rapport de Sécurité EcoCycle</h2>
        <table border="1" style="border-collapse:collapse;width:100%">
          <tr style="background:#1a1a2e;color:white">
            <th>Niveau</th><th>Type</th><th>User</th>
            <th>Description</th><th>Action recommandée</th>
          </tr>
          {rows}
        </table>
        {blocked_html}
        """


fraud_detector = FraudDetectorAgent()
