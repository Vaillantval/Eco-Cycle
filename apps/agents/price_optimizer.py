import json
import logging

from anthropic import Anthropic
from django.conf import settings
from django.db.models import Avg, Count, Max, Min, Sum

from apps.accounts.models import User
from apps.marketplace.models import Order
from apps.notifications.models import Notification
from apps.waste.models import WasteCategory

logger = logging.getLogger(__name__)

PRICE_OPTIMIZER_PROMPT = """
Tu es un agent économiste spécialisé dans le marché de recyclage haïtien.
Tu as accès aux données réelles de transactions de la plateforme EcoCycle Haiti.

Ton rôle :
- Analyser les prix de vente réels par catégorie de déchets
- Identifier les écarts entre les prix de base et le marché réel
- Recommander des ajustements précis et justifiés
- Détecter les catégories sous-valorisées ou sur-valorisées

Contexte économique :
- Monnaie : Gourde haïtienne (HTG)
- Marché : recycleurs locaux de Port-au-Prince, Cap-Haïtien, Gonaïves
- Objectif : maximiser la valeur pour les citoyens tout en restant attractif pour les acheteurs

Retourne UNIQUEMENT un JSON valide sans markdown :
{
  "adjustments": [
    {
      "category_slug": "plastic",
      "current_base_price": 50,
      "recommended_price": 65,
      "market_average": 68,
      "justification": "Les transactions du mois montrent...",
      "confidence": 0.87,
      "action": "increase|decrease|maintain"
    }
  ],
  "market_insights": "Analyse globale du marché ce mois",
  "alert": "Alerte importante si détectée, sinon null"
}
"""


class PriceOptimizerAgent:

    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def gather_market_data(self) -> dict:
        from datetime import timedelta
        from django.utils import timezone

        last_month = timezone.now() - timedelta(days=30)
        market_data = {}

        for category in WasteCategory.objects.filter(is_active=True):
            orders = Order.objects.filter(
                auction__listing__category=category,
                status='completed',
                created_at__gte=last_month,
            )
            stats = orders.aggregate(
                avg_price=Avg('amount'),
                min_price=Min('amount'),
                max_price=Max('amount'),
                total_orders=Count('id'),
            )
            total_kg = orders.aggregate(
                kg=Sum('auction__listing__quantity_kg')
            )['kg'] or 0

            market_data[category.slug] = {
                'name': category.name,
                'current_base_price_per_kg': float(category.base_price_per_kg),
                'avg_sale_price': float(stats['avg_price'] or 0),
                'min_sale_price': float(stats['min_price'] or 0),
                'max_sale_price': float(stats['max_price'] or 0),
                'total_orders': stats['total_orders'],
                'total_kg_sold': float(total_kg),
            }

        return market_data

    def run(self) -> dict:
        market_data = self.gather_market_data()

        total_orders = sum(d['total_orders'] for d in market_data.values())
        if total_orders < 5:
            return {'status': 'insufficient_data', 'total_orders': total_orders}

        response = self.client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=1024,
            system=PRICE_OPTIMIZER_PROMPT,
            messages=[{
                'role': 'user',
                'content': (
                    'Analyse ces données de marché du dernier mois et recommande '
                    'des ajustements de prix :\n\n'
                    + json.dumps(market_data, indent=2, ensure_ascii=False)
                    + '\n\nSois précis et justifie chaque recommandation avec les données.'
                ),
            }],
        )

        result = json.loads(response.content[0].text.strip())

        applied = []
        for adj in result.get('adjustments', []):
            if adj['confidence'] >= 0.75 and adj['action'] != 'maintain':
                category = WasteCategory.objects.filter(slug=adj['category_slug']).first()
                if category:
                    old_price = float(category.base_price_per_kg)
                    category.base_price_per_kg = adj['recommended_price']
                    category.save()
                    applied.append({
                        'category': category.name,
                        'old_price': old_price,
                        'new_price': adj['recommended_price'],
                        'justification': adj['justification'],
                    })

        if applied:
            admins = User.objects.filter(role='admin', is_active=True)
            message = self._build_admin_message(applied, result)
            for admin in admins:
                Notification.objects.create(
                    user=admin,
                    notification_type='system',
                    title="💰 Prix mis à jour par l'Agent IA",
                    message=message,
                    data={'adjustments': applied, 'insights': result.get('market_insights')},
                )
                from apps.notifications.email_service import EmailService
                EmailService._send(
                    admin.email,
                    '[EcoCycle Agent] Optimisation des prix effectuée',
                    f'<h2>Rapport Optimiseur de Prix</h2><pre>{message}</pre>',
                )

        return {
            'status': 'success',
            'applied_adjustments': applied,
            'insights': result.get('market_insights'),
            'alert': result.get('alert'),
        }

    def _build_admin_message(self, applied: list, result: dict) -> str:
        lines = ['Ajustements appliqués automatiquement :']
        for adj in applied:
            direction = '↑' if adj['new_price'] > adj['old_price'] else '↓'
            lines.append(
                f"{direction} {adj['category']} : "
                f"{adj['old_price']} → {adj['new_price']} HTG/kg"
            )
        if result.get('market_insights'):
            lines.append(f"\nAnalyse : {result['market_insights']}")
        return '\n'.join(lines)


price_optimizer = PriceOptimizerAgent()
