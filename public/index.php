<?php

declare(strict_types=1);

use App\Http\Kernel;
use App\Http\Middleware\AuthMiddleware;
use App\Http\Middleware\CsrfMiddleware;
use App\Http\Middleware\ErrorHandlingMiddleware;
use App\Http\Request;
use App\Routing\LegacyDispatcher;
use App\Routing\Router;
use App\Security\CsrfTokenManager;

require dirname(__DIR__) . '/vendor/autoload.php';

$request = Request::fromGlobals();
$tokenManager = new CsrfTokenManager();
$legacyDispatcher = new LegacyDispatcher(dirname(__DIR__) . '/src');
$router = new Router($legacyDispatcher);

$kernel = new Kernel(
    static fn (Request $request) => $router->dispatch($request),
    [
        new ErrorHandlingMiddleware(),
        new CsrfMiddleware($tokenManager),
        new AuthMiddleware(dirname(__DIR__) . '/src', $tokenManager),
    ]
);

$kernel->handle($request);
