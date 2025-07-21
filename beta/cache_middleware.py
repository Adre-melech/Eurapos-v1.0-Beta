class CacheControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.path.endswith((".css", ".js", ".png", ".jpg", ".webp", ".woff2")):
            response.headers["Cache-Control"] = "max-age=31536000, immutable"

        return response