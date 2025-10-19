<?php

declare(strict_types=1);

namespace App\Security;

class CsrfTokenManager
{
    private const SESSION_KEY = '_csrf_token';

    public function ensureToken(): string
    {
        if (session_status() !== PHP_SESSION_ACTIVE) {
            session_start();
        }

        if (!isset($_SESSION[self::SESSION_KEY]) || !is_string($_SESSION[self::SESSION_KEY])) {
            $_SESSION[self::SESSION_KEY] = bin2hex(random_bytes(32));
        }

        return $_SESSION[self::SESSION_KEY];
    }

    public function isTokenValid(?string $token): bool
    {
        if ($token === null || $token === '') {
            return false;
        }

        if (session_status() !== PHP_SESSION_ACTIVE) {
            session_start();
        }

        $current = $_SESSION[self::SESSION_KEY] ?? null;
        if (!is_string($current)) {
            return false;
        }

        return hash_equals($current, $token);
    }
}
