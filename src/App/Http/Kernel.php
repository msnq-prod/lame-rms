<?php

declare(strict_types=1);

namespace App\Http;

use App\Http\Middleware\MiddlewareInterface;

class Kernel
{
    /** @var array<int, MiddlewareInterface> */
    private array $middleware;

    /** @var callable */
    private $handler;

    /**
     * @param callable $handler
     * @param array<int, MiddlewareInterface> $middleware
     */
    public function __construct(callable $handler, array $middleware = [])
    {
        $this->handler = $handler;
        $this->middleware = $middleware;
    }

    public function handle(Request $request): void
    {
        $dispatcher = array_reduce(
            array_reverse($this->middleware),
            static function (callable $next, MiddlewareInterface $middleware): callable {
                return static function (Request $request) use ($middleware, $next) {
                    return $middleware->process($request, $next);
                };
            },
            $this->handler
        );

        $response = $dispatcher($request);

        if ($response instanceof Response) {
            $response->send();
        }
    }
}
