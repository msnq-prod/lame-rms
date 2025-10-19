<?php

declare(strict_types=1);

namespace App\Http\Middleware;

use App\Http\Exception\HttpException;
use App\Http\Exception\MethodNotAllowedHttpException;
use App\Http\Exception\NotFoundHttpException;
use App\Http\Request;
use App\Http\Response;

class ErrorHandlingMiddleware implements MiddlewareInterface
{
    public function process(Request $request, callable $next): ?Response
    {
        try {
            $response = $next($request);
            if ($response instanceof Response) {
                return $response;
            }

            return null;
        } catch (MethodNotAllowedHttpException $exception) {
            return $this->renderSimplePage(
                $exception->getStatusCode(),
                'Method Not Allowed',
                'The requested method is not allowed for this resource.',
                $exception->getHeaders()
            );
        } catch (NotFoundHttpException $exception) {
            return $this->renderSimplePage(
                $exception->getStatusCode(),
                'Page Not Found',
                'Sorry, we could not find the page you were looking for.'
            );
        } catch (HttpException $exception) {
            return $this->renderSimplePage(
                $exception->getStatusCode(),
                'Request Error',
                $exception->getMessage() ?: 'An unexpected error occurred.',
                $exception->getHeaders()
            );
        } catch (\Throwable $exception) {
            $this->report($exception);
            return $this->renderSimplePage(
                500,
                'Server Error',
                'An unexpected error occurred. Please try again later.'
            );
        }
    }

    /**
     * @param array<string, string> $headers
     */
    private function renderSimplePage(int $status, string $title, string $message, array $headers = []): Response
    {
        $body = <<<HTML
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>{$title}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 4rem; background: #f9fafb; color: #111827; }
        main { max-width: 42rem; margin: 0 auto; }
        h1 { font-size: 2rem; margin-bottom: 1rem; }
        p { font-size: 1rem; line-height: 1.6; }
        a { color: #2563eb; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <main>
        <h1>{$title}</h1>
        <p>{$message}</p>
        <p><a href="/">Return to the dashboard</a></p>
    </main>
</body>
</html>
HTML;

        return new Response($body, $status, $headers + ['Content-Type' => 'text/html; charset=utf-8']);
    }

    private function report(\Throwable $exception): void
    {
        if (class_exists(\Sentry\State\HubInterface::class) && function_exists('Sentry\captureException')) {
            \Sentry\captureException($exception);
        }
        error_log($exception->getMessage());
    }
}
