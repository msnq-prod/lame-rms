<?php

declare(strict_types=1);

namespace App\Http;

class Request
{
    private string $method;
    private string $uri;
    private string $path;
    private string $queryString;
    private array $server;

    private function __construct(string $method, string $uri, string $path, string $queryString, array $server)
    {
        $this->method = strtoupper($method);
        $this->uri = $uri;
        $this->path = $path === '' ? '/' : $path;
        $this->queryString = $queryString;
        $this->server = $server;
    }

    public static function fromGlobals(): self
    {
        $method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
        $uri = $_SERVER['REQUEST_URI'] ?? '/';
        $path = parse_url($uri, PHP_URL_PATH) ?: '/';
        $queryString = $_SERVER['QUERY_STRING'] ?? '';

        return new self($method, $uri, $path, $queryString, $_SERVER);
    }

    public function getMethod(): string
    {
        return $this->method;
    }

    public function getUri(): string
    {
        return $this->uri;
    }

    public function getPath(): string
    {
        return $this->path;
    }

    public function getQueryString(): string
    {
        return $this->queryString;
    }

    public function getServerParams(): array
    {
        return $this->server;
    }

    public function withServerParam(string $key, $value): void
    {
        $this->server[$key] = $value;
        $_SERVER[$key] = $value;
    }

    public function getPathForRouting(): string
    {
        return rawurldecode($this->path);
    }

    public function getRequestedPath(): string
    {
        return $this->path;
    }
}
