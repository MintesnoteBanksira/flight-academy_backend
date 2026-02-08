"""
Firebase Admin SDK configuration for push notifications
"""
import json
import firebase_admin
from firebase_admin import credentials, messaging
from .config import settings
import os


def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    if firebase_admin._apps:
        return  # Already initialized
    
    # Try to get credentials from environment variable
    firebase_creds_json = os.environ.get('FIREBASE_CREDENTIALS')
    
    if firebase_creds_json:
        try:
            cred_dict = json.loads(firebase_creds_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized from environment variable")
            return
        except Exception as e:
            print(f"Error initializing Firebase from env: {e}")
    
    # Try individual environment variables
    project_id = os.environ.get('FIREBASE_PROJECT_ID')
    private_key = os.environ.get('FIREBASE_PRIVATE_KEY')
    client_email = os.environ.get('FIREBASE_CLIENT_EMAIL')
    
    if project_id and private_key and client_email:
        try:
            # Handle escaped newlines in private key
            private_key = private_key.replace('\\n', '\n')
            
            cred_dict = {
                "type": "service_account",
                "project_id": project_id,
                "private_key": private_key,
                "client_email": client_email,
                "token_uri": "https://oauth2.googleapis.com/token",
            }
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized from individual env vars")
            return
        except Exception as e:
            print(f"Error initializing Firebase from individual vars: {e}")
    
    print("Firebase not configured - push notifications disabled")


async def send_push_notification(
    token: str,
    title: str,
    body: str,
    data: dict = None
) -> bool:
    """
    Send a push notification to a single device
    
    Args:
        token: FCM device token
        title: Notification title
        body: Notification body
        data: Additional data payload
    
    Returns:
        True if successful, False otherwise
    """
    if not firebase_admin._apps:
        print("Firebase not initialized, skipping push notification")
        return False
    
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=token,
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    sound='default',
                    priority='high',
                    channel_id='flight_academy_channel',
                ),
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound='default',
                        badge=1,
                    ),
                ),
            ),
        )
        
        response = messaging.send(message)
        print(f"Successfully sent message: {response}")
        return True
        
    except messaging.UnregisteredError:
        print(f"Token {token[:20]}... is no longer valid")
        return False
    except Exception as e:
        print(f"Error sending push notification: {e}")
        return False


async def send_push_notification_batch(
    tokens: list,
    title: str,
    body: str,
    data: dict = None
) -> dict:
    """
    Send push notifications to multiple devices
    
    Args:
        tokens: List of FCM device tokens
        title: Notification title
        body: Notification body
        data: Additional data payload
    
    Returns:
        Dict with success_count and failure_count
    """
    if not firebase_admin._apps:
        print("Firebase not initialized, skipping push notifications")
        return {"success_count": 0, "failure_count": len(tokens)}
    
    if not tokens:
        return {"success_count": 0, "failure_count": 0}
    
    try:
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            tokens=tokens,
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    sound='default',
                    priority='high',
                    channel_id='flight_academy_channel',
                ),
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound='default',
                        badge=1,
                    ),
                ),
            ),
        )
        
        response = messaging.send_each_for_multicast(message)
        
        # Log failed tokens for cleanup
        failed_tokens = []
        for idx, send_response in enumerate(response.responses):
            if not send_response.success:
                failed_tokens.append(tokens[idx])
                if isinstance(send_response.exception, messaging.UnregisteredError):
                    print(f"Token {tokens[idx][:20]}... is no longer valid")
        
        return {
            "success_count": response.success_count,
            "failure_count": response.failure_count,
            "failed_tokens": failed_tokens
        }
        
    except Exception as e:
        print(f"Error sending batch push notifications: {e}")
        return {"success_count": 0, "failure_count": len(tokens)}
