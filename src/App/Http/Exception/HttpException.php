<?php

declare(strict_types=1);

namespace App\Http\Exception;

use RuntimeException;

class HttpException extends RuntimeException
{
    private int $statusCode;
    /** @var array<string, string> */
    private array $headers;

    public function __construct(int $statusCode, string $message = '', array $headers = [], ?\Throwable $previous = null)
    {
        parent::__construct($message, 0, $previous);
        $this->statusCode = $statusCode;
        $this->headers = $headers;
    }

    public function getStatusCode(): int
    {
        return $this->statusCode;
    }

    /**
     * @return array<string, string>
     */
    public function getHeaders(): array
    {
        return $this->headers;
    }
}
