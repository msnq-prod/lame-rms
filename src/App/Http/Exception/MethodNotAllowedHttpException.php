<?php

declare(strict_types=1);

namespace App\Http\Exception;

class MethodNotAllowedHttpException extends HttpException
{
    /** @var array<int, string> */
    private array $allowedMethods;

    /**
     * @param array<int, string> $allowedMethods
     */
    public function __construct(array $allowedMethods, string $message = 'Method not allowed', ?\Throwable $previous = null)
    {
        $headers = ['Allow' => implode(', ', $allowedMethods)];
        parent::__construct(405, $message, $headers, $previous);
        $this->allowedMethods = $allowedMethods;
    }

    /**
     * @return array<int, string>
     */
    public function getAllowedMethods(): array
    {
        return $this->allowedMethods;
    }
}
