<?php

declare(strict_types=1);

namespace Tests\Smoke;

use App\Routing\LegacyDispatcher;
use App\Routing\LegacyResolution;
use PHPUnit\Framework\TestCase;
use ReflectionClass;

final class LegacyDispatcherSmokeTest extends TestCase
{
    private LegacyDispatcher $dispatcher;

    protected function setUp(): void
    {
        parent::setUp();
        $srcDirectory = realpath(__DIR__ . '/../../src');
        $this->dispatcher = new LegacyDispatcher($srcDirectory !== false ? $srcDirectory : __DIR__ . '/../../src');
    }

    public function testRootPageResolvesToIndexScript(): void
    {
        $resolution = $this->invokeResolve('/');
        $this->assertInstanceOf(LegacyResolution::class, $resolution);
        $this->assertFalse($resolution->isRedirect());

        $expected = realpath(__DIR__ . '/../../src/index.php');
        $this->assertSame($expected, $resolution->getScriptPath());
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
