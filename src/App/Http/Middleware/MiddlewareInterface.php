<?php

declare(strict_types=1);

namespace App\Http\Middleware;

use App\Http\Request;
use App\Http\Response;

interface MiddlewareInterface
{
    /**
     * @param callable(Request): (Response|null) $next
     */
    public function process(Request $request, callable $next);
}
