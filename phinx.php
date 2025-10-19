<?php

require_once __DIR__ . '/bootstrap.php';

$adapter = env('DB_ADAPTER', 'mysql');
$basePort = env('DB_PORT', 3306);
if (!is_numeric($basePort)) {
    throw new RuntimeException('Environment variable DB_PORT must be numeric.');
}

$baseConfig = [
    'adapter' => $adapter,
    'host' => require_env('DB_HOSTNAME'),
    'name' => require_env('DB_DATABASE'),
    'user' => require_env('DB_USERNAME'),
    'pass' => require_env('DB_PASSWORD'),
    'port' => (int) $basePort,
    'charset' => 'utf8mb4',
    'collation' => 'utf8mb4_unicode_ci',
];

$environmentConfig = static function (string $environment) use ($baseConfig): array {
    $suffix = strtoupper($environment);

    $port = env("DB_PORT_{$suffix}", $baseConfig['port']);
    if (!is_numeric($port)) {
        throw new RuntimeException(sprintf('Environment variable DB_PORT_%s must be numeric.', $suffix));
    }

    return array_merge($baseConfig, [
        'host' => env("DB_HOSTNAME_{$suffix}", $baseConfig['host']),
        'name' => env("DB_DATABASE_{$suffix}", $baseConfig['name']),
        'user' => env("DB_USERNAME_{$suffix}", $baseConfig['user']),
        'pass' => env("DB_PASSWORD_{$suffix}", $baseConfig['pass']),
        'port' => (int) $port,
    ]);
};

return [
    'paths' => [
        'migrations' => __DIR__ . '/db/migrations',
        'seeds' => __DIR__ . '/db/seeds'
    ],
    'schema_file' => __DIR__ . '/db/schema.php',
    'foreign_keys' => true,
    'environments' => [
        'migration_table' => 'phinxlog',
        'default_environment' => env('PHINX_ENV', 'development'),
        'production' => $environmentConfig('production'),
        'development' => $environmentConfig('development'),
        'test' => $environmentConfig('test'),
    ],
    'version_order' => 'creation'
];
