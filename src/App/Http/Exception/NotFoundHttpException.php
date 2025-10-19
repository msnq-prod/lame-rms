<?php

declare(strict_types=1);

namespace App\Http\Exception;

class NotFoundHttpException extends HttpException
{
    public function __construct(string $message = 'Page not found', ?\Throwable $previous = null)
    {
        parent::__construct(404, $message, [], $previous);
    }
}
