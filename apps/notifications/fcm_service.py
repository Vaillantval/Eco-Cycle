import json
import base64
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

_firebase_initialized = False


def _initialize_firebase():
    global _firebase_initialized
    if _firebase_initialized:
        return
    try:
        import firebase_admin
        from firebase_admin import credentials
        if not firebase_admin._apps:
            if settings.FIREBASE_CREDENTIALS_B64:
                creds_json = json.loads(
                    base64.b64decode(settings.FIREBASE_CREDENTIALS_B64).decode()
                )
                cred = credentials.Certificate(creds_json)
            else:
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
        _firebase_initialized = True
    except Exception as e:
        logger.warning(f'Firebase init skipped: {e}')


class FCMService:

    @staticmethod
    def send_to_user(user, title: str, body: str, data: dict = None):
        if not user.fcm_token:
            return None
        _initialize_firebase()
        if not _firebase_initialized:
            return None
        try:
            from firebase_admin import messaging
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data={str(k): str(v) for k, v in (data or {}).items()},
                token=user.fcm_token,
                android=messaging.AndroidConfig(priority='high'),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(sound='default')
                    )
                ),
            )
            return messaging.send(message)
        except Exception as e:
            logger.error(f'FCM send error to {user.email}: {e}')
            return None

    @staticmethod
    def send_to_multiple(users, title: str, body: str, data: dict = None):
        tokens = [u.fcm_token for u in users if u.fcm_token]
        if not tokens:
            return
        _initialize_firebase()
        if not _firebase_initialized:
            return None
        try:
            from firebase_admin import messaging
            multicast = messaging.MulticastMessage(
                notification=messaging.Notification(title=title, body=body),
                data={str(k): str(v) for k, v in (data or {}).items()},
                tokens=tokens,
            )
            return messaging.send_each_for_multicast(multicast)
        except Exception as e:
            logger.error(f'FCM multicast error: {e}')
            return None
