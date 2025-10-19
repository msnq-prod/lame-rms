<?php

declare(strict_types=1);

namespace App\Http;

class Response
{
    private string $body;
    private int $status;
    /** @var array<string, string> */
    private array $headers;

    public function __construct(string $body = '', int $status = 200, array $headers = [])
    {
        $this->body = $body;
        $this->status = $status;
        $this->headers = $headers;
    }

    public function getStatus(): int
    {
        return $this->status;
    }

    /**
     * @return array<string, string>
     */
    public function getHeaders(): array
    {
        return $this->headers;
    }

    public function getBody(): string
    {
        return $this->body;
    }

    public function send(): void
    {
        http_response_code($this->status);
        foreach ($this->headers as $name => $value) {
            header($name . ': ' . $value);
        }
        if ($_SERVER['REQUEST_METHOD'] === 'HEAD') {
            return;
        }
        echo $this->body;
    }
}
