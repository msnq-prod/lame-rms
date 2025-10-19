<?php

declare(strict_types=1);

namespace Tests\Smoke;

use App\Http\Request;
use App\Http\Response;
use App\Routing\LegacyDispatcher;
use App\Routing\Router;
use PHPUnit\Framework\TestCase;

final class RouterSmokeTest extends TestCase
{
    public function testOptionsRequestDoesNotInvokeLegacyLayer(): void
    {
        $legacyDispatcher = $this->createMock(LegacyDispatcher::class);
        $legacyDispatcher->expects($this->never())->method('dispatch');

        $router = new Router($legacyDispatcher);
        $request = $this->createRequest('OPTIONS', '/any/path');

        $response = $router->dispatch($request);

        $this->assertInstanceOf(Response::class, $response);
        $this->assertSame(204, $response->getStatus());
        $this->assertSame('GET, POST, HEAD, OPTIONS', $response->getHeaders()['Allow'] ?? null);
        $this->assertSame('', $response->getBody());
    }

    public function testGetRequestIsForwardedToLegacyLayer(): void
    {
        $legacyDispatcher = $this->createMock(LegacyDispatcher::class);
        $legacyDispatcher
            ->expects($this->once())
            ->method('dispatch')
            ->with($this->isInstanceOf(Request::class), $this->isType('array'))
            ->willReturn(null);

        $router = new Router($legacyDispatcher);
        $request = $this->createRequest('GET', '/login');

        $this->assertNull($router->dispatch($request));
    }

    private function createRequest(string $method, string $uri): Request
    {
        $parts = parse_url($uri);
        $_SERVER['REQUEST_METHOD'] = strtoupper($method);
        $_SERVER['REQUEST_URI'] = $uri;
        $_SERVER['QUERY_STRING'] = $parts['query'] ?? '';

        return Request::fromGlobals();
    }
}
