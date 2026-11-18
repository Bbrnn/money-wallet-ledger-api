import hashlib
import json
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from .models import IdempotencyKey

class IdempotencyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only enforce idempotency on state-changing POST/PUT requests to api/v1/
        if request.method in ["POST", "PUT"] and request.path.startswith("/api/v1/"):
            idempotency_key = request.headers.get("Idempotency-Key")
            
            if not idempotency_key:
                return JsonResponse(
                    {"error": "Idempotency-Key header is required for this request."}, 
                    status=400
                )

            # Compute payload hash to detect parameter tampering on retry
            try:
                body_data = request.body.decode('utf-8')
                request_hash = hashlib.sha256(body_data.encode()).hexdigest()
            except Exception:
                request_hash = ""

            # Check if key already exists
            existing = IdempotencyKey.objects.filter(key=idempotency_key).first()
            if existing:
                if existing.request_hash != request_hash:
                    return JsonResponse(
                        {"error": "Idempotency key reused with a different request payload."}, 
                        status=422
                    )
                # Return cached response instantly
                return JsonResponse(existing.response_body, status=existing.response_status)

            # Attach key and hash to request for view/service handling if needed
            request.idempotency_key = idempotency_key
            request.request_hash = request_hash

        response = self.get_response(request)

        # Cache successful POST/PUT responses if idempotency key was provided
        if hasattr(request, "idempotency_key") and 200 <= response.status_code < 300:
            try:
                response_body = json.loads(response.content.decode('utf-8'))
                IdempotencyKey.objects.create(
                    key=request.idempotency_key,
                    wallet_id=response_body.get("wallet_id", "00000000-0000-0000-0000-000000000000"),
                    request_hash=request.request_hash,
                    response_status=response.status_code,
                    response_body=response_body,
                    expires_at=timezone.now() + timedelta(hours=24)
                )
            except Exception:
                pass # Fail silently if response body isn't JSON

        return response