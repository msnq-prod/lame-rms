<?php

declare(strict_types=1);

namespace App\Routing;

class LegacyResolution
{
    private ?string $scriptPath;
    private ?string $redirectTarget;
    private int $status;

    private function __construct(?string $scriptPath, ?string $redirectTarget, int $status = 200)
    {
        $this->scriptPath = $scriptPath;
        $this->redirectTarget = $redirectTarget;
        $this->status = $status;
    }

    public static function forScript(string $path): self
    {
        return new self($path, null, 200);
    }

    public static function forRedirect(string $target, int $status = 301): self
    {
        return new self(null, $target, $status);
    }

    public function isRedirect(): bool
    {
        return $this->redirectTarget !== null;
    }

    public function getRedirectTarget(): ?string
    {
        return $this->redirectTarget;
    }

    public function getRedirectStatus(): int
    {
        return $this->status;
    }

    public function getScriptPath(): ?string
    {
        return $this->scriptPath;
    }
}
