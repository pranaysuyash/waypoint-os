# Procfile — spine-api
#
# Usage with Fly.io:
#   fly launch --image ghcr.io/your-org/spine-api:latest
#   fly secrets set TRAVELER_SAFE_STRICT=0
#   fly deploy
#
# Usage with Render:
#   render blueprint render.yaml
#
# Override vars per environment:
#   SPINE_API_CORS=https://your-frontend.com
#   SPINE_API_WORKERS=4
#   TRAVELER_SAFE_STRICT=1

web: uvicorn spine_api.server:app --host 0.0.0.0 --port 8000 --workers 4
