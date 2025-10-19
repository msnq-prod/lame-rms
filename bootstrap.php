<?php

declare(strict_types=1);

require_once __DIR__ . '/vendor/autoload.php';

use Dotenv\Dotenv;

if (!defined('PROJECT_ROOT')) {
    define('PROJECT_ROOT', __DIR__);
}

if (class_exists(Dotenv::class)) {
    $dotenv = Dotenv::createImmutable(PROJECT_ROOT);
    $dotenv->safeLoad();
}

if (!function_exists('env')) {
    /**
     * Retrieve an environment variable with an optional default.
     */
    function env(string $key, $default = null)
    {
        $value = $_ENV[$key] ?? $_SERVER[$key] ?? getenv($key);

        if ($value === false) {
            $value = null;
        }

        if (is_string($value)) {
            $value = trim($value);
            if ($value === '') {
                $value = null;
            }
        }

        return $value ?? $default;
    }
}

if (!function_exists('require_env')) {
    /**
     * Retrieve a required environment variable or throw a runtime exception.
     */
    function require_env(string $key): string
    {
        $value = env($key);
        if ($value === null || $value === '') {
            throw new RuntimeException(sprintf('Environment variable %s is not set.', $key));
        }

        return $value;
    }
}
