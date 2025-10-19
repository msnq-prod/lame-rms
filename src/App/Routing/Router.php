<?php

declare(strict_types=1);

namespace App\Routing;

use App\Http\Exception\MethodNotAllowedHttpException;
use App\Http\Exception\NotFoundHttpException;
use App\Http\Request;
use App\Http\Response;
use FastRoute\Dispatcher;
use FastRoute\RouteCollector;

use function FastRoute\simpleDispatcher;

class Router
{
    private Dispatcher $dispatcher;
    private LegacyDispatcher $legacyDispatcher;

    public function __construct(LegacyDispatcher $legacyDispatcher)
    {
        $this->legacyDispatcher = $legacyDispatcher;
        $this->dispatcher = simpleDispatcher(static function (RouteCollector $routes) {
            $routes->addRoute(['GET', 'POST', 'HEAD', 'OPTIONS'], '/{path:.*}', 'legacy');
        });
    }

    public function dispatch(Request $request): ?Response
    {
        $routeInfo = $this->dispatcher->dispatch($request->getMethod(), $request->getPathForRouting());

        switch ($routeInfo[0]) {
            case Dispatcher::NOT_FOUND:
                throw new NotFoundHttpException();
            case Dispatcher::METHOD_NOT_ALLOWED:
                /** @var array<int, string> $allowed */
                $allowed = $routeInfo[1];
                throw new MethodNotAllowedHttpException($allowed);
            case Dispatcher::FOUND:
                if ($request->getMethod() === 'OPTIONS') {
                    return new Response('', 204, ['Allow' => 'GET, POST, HEAD, OPTIONS']);
                }

                /** @var array<string, string> $vars */
                $vars = $routeInfo[2];
                return $this->legacyDispatcher->dispatch($request, $vars);
            default:
                throw new NotFoundHttpException();
        }
    }
}
