<?php

declare(strict_types=1);

namespace Tests\Smoke;

use App\Http\Exception\NotFoundHttpException;
use App\Http\Request;
use App\Routing\LegacyDispatcher;
use App\Routing\LegacyResolution;
use PHPUnit\Framework\TestCase;
use ReflectionClass;

final class LegacyDispatcherSmokeTest extends TestCase
{
    private LegacyDispatcher $dispatcher;
    /** @var array<string, mixed> */
    private array $serverBackup = [];

    protected function setUp(): void
    {
        parent::setUp();
        $this->serverBackup = $_SERVER;
        $srcDirectory = realpath(__DIR__ . '/../../src');
        $this->dispatcher = new LegacyDispatcher($srcDirectory !== false ? $srcDirectory : __DIR__ . '/../../src');
    }

    protected function tearDown(): void
    {
        $_SERVER = $this->serverBackup;
        parent::tearDown();
    }

    public function testRootPageResolvesToIndexScript(): void
    {
        $resolution = $this->invokeResolve('/');
        $this->assertInstanceOf(LegacyResolution::class, $resolution);
        $this->assertFalse($resolution->isRedirect());

        $expected = realpath(__DIR__ . '/../../src/index.php');
        $this->assertSame($expected, $resolution->getScriptPath());
    }

    public function testDirectoryTraversalIsRejected(): void
    {
        $_SERVER['REQUEST_METHOD'] = 'GET';
        $_SERVER['REQUEST_URI'] = '/../etc/passwd';
        $_SERVER['QUERY_STRING'] = '';

        $request = Request::fromGlobals();

        $this->expectException(NotFoundHttpException::class);
        $this->dispatcher->dispatch($request);
    }

    public function testLoginDirectoryTriggersRedirect(): void
    {
        $resolution = $this->invokeResolve('/login');
        $this->assertInstanceOf(LegacyResolution::class, $resolution);
        $this->assertTrue($resolution->isRedirect());
        $this->assertSame('/login/', $resolution->getRedirectTarget());
    }

    public function testLoginIndexScriptResolvesDirectly(): void
    {
        $resolution = $this->invokeResolve('/login/index.php');
        $this->assertInstanceOf(LegacyResolution::class, $resolution);
        $this->assertFalse($resolution->isRedirect());

        $expected = realpath(__DIR__ . '/../../src/login/index.php');
        $this->assertSame($expected, $resolution->getScriptPath());
    }

    /**
     * @return LegacyResolution|null
     */
    private function invokeResolve(string $path): ?LegacyResolution
    {
        $reflection = new ReflectionClass(LegacyDispatcher::class);
        $method = $reflection->getMethod('resolve');
        $method->setAccessible(true);

        /** @var LegacyResolution|null $resolution */
        $resolution = $method->invoke($this->dispatcher, $path);

        return $resolution;
    }
}
