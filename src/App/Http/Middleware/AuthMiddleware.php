<?php

declare(strict_types=1);

namespace App\Http\Middleware;

use App\Http\Request;
use App\Http\Response;
use App\Security\CsrfTokenManager;
use Twig\Markup;
use Twig\TwigFunction;

class AuthMiddleware implements MiddlewareInterface
{
    private string $srcDirectory;
    private CsrfTokenManager $csrfTokenManager;

    /** @var array<int, string> */
    private array $publicPrefixes = [
        '/login',
        '/setup',
        '/public',
    ];

    public function __construct(string $srcDirectory, CsrfTokenManager $csrfTokenManager)
    {
        $this->srcDirectory = rtrim($srcDirectory, '/');
        $this->csrfTokenManager = $csrfTokenManager;
    }

    public function process(Request $request, callable $next): ?Response
    {
        $this->bootstrapEnvironment();

        $path = $request->getPathForRouting();

        if ($this->isApiRequest($path)) {
            return $next($request);
        }

        if ($this->requiresAuthentication($path)) {
            $this->requireHeadSecure();
        }

        return $next($request);
    }

    private function bootstrapEnvironment(): void
    {
        require_once $this->srcDirectory . '/common/head.php';

        $token = $this->csrfTokenManager->ensureToken();
        if (isset($GLOBALS['TWIG']) && $GLOBALS['TWIG'] instanceof \Twig\Environment) {
            $twig = $GLOBALS['TWIG'];
            $twig->addGlobal('csrf_token', $token);

            if (!$twig->getFunction('csrf_field')) {
                $manager = $this->csrfTokenManager;
                $twig->addFunction(new TwigFunction('csrf_field', static function () use ($manager) {
                    $value = $manager->ensureToken();
                    return new Markup(
                        '<input type="hidden" name="_csrf_token" value="' . htmlspecialchars($value, ENT_QUOTES, 'UTF-8') . '">',
                        'UTF-8'
                    );
                }, ['is_safe' => ['html']]));
            }
        }
    }

    private function requiresAuthentication(string $path): bool
    {
        foreach ($this->publicPrefixes as $prefix) {
            if ($path === $prefix || str_starts_with($path, $prefix . '/')) {
                return false;
            }
        }

        return true;
    }

    private function isApiRequest(string $path): bool
    {
        return str_starts_with($path, '/api');
    }

    private function requireHeadSecure(): void
    {
        require_once $this->srcDirectory . '/common/headSecure.php';
    }
}
