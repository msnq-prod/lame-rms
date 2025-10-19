<?php

declare(strict_types=1);

namespace App\Routing;

use App\Http\Exception\NotFoundHttpException;
use App\Http\Request;
use App\Http\Response;

class LegacyDispatcher
{
    private string $srcDirectory;

    public function __construct(string $srcDirectory)
    {
        $this->srcDirectory = rtrim($srcDirectory, '/');
    }

    /**
     * @param array<string, string> $vars
     */
    public function dispatch(Request $request, array $vars = []): ?Response
    {
        $resolution = $this->resolve($request->getRequestedPath());

        if ($resolution === null) {
            throw new NotFoundHttpException();
        }

        if ($resolution->isRedirect()) {
            $target = $resolution->getRedirectTarget() ?? '/';
            if ($request->getQueryString() !== '') {
                $target .= (str_contains($target, '?') ? '&' : '?') . $request->getQueryString();
            }

            return new Response('', $resolution->getRedirectStatus(), ['Location' => $target]);
        }

        $scriptPath = $resolution->getScriptPath();
        if ($scriptPath === null) {
            throw new NotFoundHttpException();
        }

        $this->includeLegacyScript($request, $scriptPath);
        return null;
    }

    private function resolve(string $rawPath): ?LegacyResolution
    {
        $path = rawurldecode($rawPath);
        if ($path === '') {
            $path = '/';
        }

        if (!str_starts_with($path, '/')) {
            $path = '/' . $path;
        }

        if (str_contains($path, '..')) {
            return null;
        }

        if ($path === '/' || $path === '/index.php') {
            return LegacyResolution::forScript($this->srcDirectory . '/index.php');
        }

        if (str_ends_with($path, '/') && $path !== '/') {
            $trimmed = rtrim($path, '/');
            $fileCandidate = $this->srcDirectory . $trimmed . '.php';
            if (is_file($fileCandidate)) {
                return LegacyResolution::forRedirect($trimmed);
            }
        }

        if (str_ends_with($path, '.php')) {
            $file = $this->srcDirectory . $path;
            if (is_file($file)) {
                return LegacyResolution::forScript($file);
            }
            return null;
        }

        $fileCandidate = $this->srcDirectory . $path . '.php';
        if (is_file($fileCandidate)) {
            return LegacyResolution::forScript($fileCandidate);
        }

        $dirCandidate = $this->srcDirectory . $path;
        if (is_dir($dirCandidate)) {
            $indexCandidate = $dirCandidate . '/index.php';
            if (is_file($indexCandidate)) {
                if (!str_ends_with($path, '/')) {
                    return LegacyResolution::forRedirect($path . '/');
                }
                return LegacyResolution::forScript($indexCandidate);
            }
        }

        $trimmed = rtrim($path, '/');
        $indexCandidate = $this->srcDirectory . $trimmed . '/index.php';
        if (is_file($indexCandidate)) {
            return LegacyResolution::forRedirect($trimmed . '/');
        }

        return null;
    }

    private function includeLegacyScript(Request $request, string $scriptPath): void
    {
        $realPath = realpath($scriptPath);
        if ($realPath === false) {
            throw new NotFoundHttpException();
        }

        $cwd = getcwd();
        $scriptDir = dirname($realPath);
        $scriptName = '/' . ltrim(str_replace($this->srcDirectory, '', $realPath), '/');

        $request->withServerParam('SCRIPT_FILENAME', $realPath);
        $request->withServerParam('SCRIPT_NAME', $scriptName);
        $request->withServerParam('PHP_SELF', $scriptName);

        chdir($scriptDir);
        require $realPath;
        chdir($cwd ?: '.');
    }
}
