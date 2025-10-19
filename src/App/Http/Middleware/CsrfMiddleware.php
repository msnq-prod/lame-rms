<?php

declare(strict_types=1);

namespace App\Http\Middleware;

use App\Http\Request;
use App\Http\Response;
use App\Security\CsrfTokenManager;

class CsrfMiddleware implements MiddlewareInterface
{
    private CsrfTokenManager $tokenManager;

    public function __construct(CsrfTokenManager $tokenManager)
    {
        $this->tokenManager = $tokenManager;
    }

    public function process(Request $request, callable $next): ?Response
    {
        $this->tokenManager->ensureToken();

        if ($this->shouldSkip($request)) {
            return $next($request);
        }

        if (in_array($request->getMethod(), ['POST', 'PUT', 'PATCH', 'DELETE'], true)) {
            $submittedToken = $_POST['_csrf_token'] ?? $_SERVER['HTTP_X_CSRF_TOKEN'] ?? null;
            if (!$this->tokenManager->isTokenValid(is_string($submittedToken) ? $submittedToken : null)) {
                return new Response(
                    '<h1>Invalid CSRF token</h1><p>Please refresh the page and try again.</p>',
                    419,
                    ['Content-Type' => 'text/html; charset=utf-8']
                );
            }
        }

        return $next($request);
    }

    private function shouldSkip(Request $request): bool
    {
        $path = $request->getPathForRouting();
        if (str_starts_with($path, '/api')) {
            return true;
        }

        return false;
    }
}
