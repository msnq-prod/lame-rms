<?php
require_once 'loginAjaxHead.php';

use \Firebase\JWT\JWT;

const LOGIN_RATE_LIMIT_WINDOW_SECONDS = 900; // 15 minutes
const LOGIN_RATE_LIMIT_BLOCK_SECONDS = 900;  // 15 minutes
const LOGIN_RATE_LIMIT_MAX_ATTEMPTS = 5;

const DEFAULT_CREDENTIAL_USERNAME = 'username';
const DEFAULT_CREDENTIAL_SALT_ONE = '8smqAFD9';
const DEFAULT_CREDENTIAL_SALT_TWO = 'uOhfrOCW';
const DEFAULT_CREDENTIAL_HASH = 'sha256';
const DEFAULT_CREDENTIAL_PASSWORD_HASH = 'fa5a51baef12914c7f2e0e1176a030bf086d26edae298c25d5f84c90bc72ecd7';

function loginGetClientIp(): string
{
    if (!empty($_SERVER['HTTP_CF_CONNECTING_IP'])) {
        return $_SERVER['HTTP_CF_CONNECTING_IP'];
    }
    if (!empty($_SERVER['HTTP_X_FORWARDED_FOR'])) {
        $forwarded = explode(',', $_SERVER['HTTP_X_FORWARDED_FOR']);
        return trim($forwarded[0]);
    }
    return $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';
}

function loginRateLimitKey(string $value): string
{
    return hash('sha256', $value);
}

function loginRateLimitGet(string $type, string $hash): ?array
{
    global $DBLIB;
    $DBLIB->where('loginRateLimits_type', $type);
    $DBLIB->where('loginRateLimits_key', $hash);
    $record = $DBLIB->getOne('loginRateLimits', [
        'loginRateLimits_id',
        'loginRateLimits_attempts',
        'loginRateLimits_lastAttempt',
        'loginRateLimits_blockedUntil',
    ]);
    return $record ?: null;
}

function loginRateLimitFetchStates(array $descriptors, int $now): array
{
    $states = [];
    $blocked = null;
    foreach ($descriptors as $descriptor) {
        $record = loginRateLimitGet($descriptor['type'], $descriptor['hash']);
        $state = [
            'type' => $descriptor['type'],
            'hash' => $descriptor['hash'],
            'record' => $record,
        ];
        $states[] = $state;
        if ($record && !empty($record['loginRateLimits_blockedUntil'])) {
            $blockedUntilTs = strtotime($record['loginRateLimits_blockedUntil']);
            if ($blockedUntilTs !== false && $blockedUntilTs > $now) {
                if ($blocked === null || $blockedUntilTs > $blocked['until']) {
                    $blocked = [
                        'state' => $state,
                        'until' => $blockedUntilTs,
                    ];
                }
            }
        }
    }
    return ['states' => $states, 'blocked' => $blocked];
}

function loginRateLimitRegisterFailure(array $state, int $now): void
{
    global $DBLIB;
    $attempts = 1;
    $blockUntil = null;
    $nowSql = date('Y-m-d H:i:s', $now);

    if ($state['record']) {
        $lastAttemptTs = $state['record']['loginRateLimits_lastAttempt'] ? strtotime($state['record']['loginRateLimits_lastAttempt']) : null;
        if ($lastAttemptTs && ($now - $lastAttemptTs) <= LOGIN_RATE_LIMIT_WINDOW_SECONDS) {
            $attempts = (int) $state['record']['loginRateLimits_attempts'] + 1;
        }
        $existingBlock = $state['record']['loginRateLimits_blockedUntil'] ? strtotime($state['record']['loginRateLimits_blockedUntil']) : null;
        if ($existingBlock && $existingBlock > $now) {
            $blockUntil = date('Y-m-d H:i:s', $existingBlock);
            $attempts = max($attempts, (int) $state['record']['loginRateLimits_attempts']);
        }
    }

    if ($blockUntil === null && $attempts >= LOGIN_RATE_LIMIT_MAX_ATTEMPTS) {
        $blockUntil = date('Y-m-d H:i:s', $now + LOGIN_RATE_LIMIT_BLOCK_SECONDS);
    }

    if ($state['record']) {
        $DBLIB->where('loginRateLimits_id', $state['record']['loginRateLimits_id']);
        $DBLIB->update('loginRateLimits', [
            'loginRateLimits_attempts' => min($attempts, LOGIN_RATE_LIMIT_MAX_ATTEMPTS),
            'loginRateLimits_lastAttempt' => $nowSql,
            'loginRateLimits_blockedUntil' => $blockUntil,
        ]);
    } else {
        $DBLIB->insert('loginRateLimits', [
            'loginRateLimits_type' => $state['type'],
            'loginRateLimits_key' => $state['hash'],
            'loginRateLimits_attempts' => min($attempts, LOGIN_RATE_LIMIT_MAX_ATTEMPTS),
            'loginRateLimits_lastAttempt' => $nowSql,
            'loginRateLimits_blockedUntil' => $blockUntil,
        ]);
    }
}

function loginRateLimitRegisterSuccess(array $state, int $now): void
{
    global $DBLIB;
    if (!$state['record']) {
        return;
    }
    $DBLIB->where('loginRateLimits_id', $state['record']['loginRateLimits_id']);
    $DBLIB->update('loginRateLimits', [
        'loginRateLimits_attempts' => 0,
        'loginRateLimits_lastAttempt' => date('Y-m-d H:i:s', $now),
        'loginRateLimits_blockedUntil' => null,
    ]);
}

function loginRecordAttempt(string $input, string $ipAddress, bool $blocked, bool $successful): void
{
    global $DBLIB;
    $DBLIB->insert('loginAttempts', [
        'loginAttempts_ip' => $ipAddress,
        'loginAttempts_textEntered' => $input,
        'loginAttempts_timestamp' => date('Y-m-d H:i:s'),
        'loginAttempts_blocked' => $blocked ? '1' : '0',
        'loginAttempts_successful' => $successful ? '1' : '0',
    ]);
}

function loginIsDefaultCredentialUser(array $user): bool
{
    return $user['users_username'] === DEFAULT_CREDENTIAL_USERNAME
        && $user['users_salty1'] === DEFAULT_CREDENTIAL_SALT_ONE
        && $user['users_salty2'] === DEFAULT_CREDENTIAL_SALT_TWO
        && $user['users_hash'] === DEFAULT_CREDENTIAL_HASH
        && $user['users_password'] === DEFAULT_CREDENTIAL_PASSWORD_HASH;
}

if (isset($_POST['formInput']) && isset($_POST['password'])) {
    $input = trim(strtolower($GLOBALS['bCMS']->sanitizeString($_POST['formInput'])));
    $password = $GLOBALS['bCMS']->sanitizeString($_POST['password']);
    if ($input === '' || $password === '') {
        finish(false, ['code' => null, 'message' => 'No data specified']);
    }

    $ipAddress = loginGetClientIp();
    $now = time();
    $rateLimitDescriptors = [
        ['type' => 'identifier', 'hash' => loginRateLimitKey($input)],
        ['type' => 'ip', 'hash' => loginRateLimitKey($ipAddress)],
    ];
    $rateLimitState = loginRateLimitFetchStates($rateLimitDescriptors, $now);

    if ($rateLimitState['blocked'] !== null) {
        loginRecordAttempt($input, $ipAddress, true, false);
        $secondsRemaining = max(0, $rateLimitState['blocked']['until'] - $now);
        $minutesRemaining = max(1, (int) ceil($secondsRemaining / 60));
        finish(false, ['code' => null, 'message' => 'Too many failed login attempts. Please try again in ' . $minutesRemaining . ' minute' . ($minutesRemaining === 1 ? '' : 's') . '.']);
    }

    if (filter_var($input, FILTER_VALIDATE_EMAIL)) {
        $DBLIB->where('users_email', $input);
    } else {
        $DBLIB->where('users_username', $input);
    }
    $DBLIB->where('users_deleted', 0);
    $DBLIB->where('users_password', null, 'IS NOT');
    $user = $DBLIB->getOne('users', [
        'users.users_salty1',
        'users.users_salty2',
        'users.users_password',
        'users.users_hash',
        'users.users_userid',
        'users.users_suspended',
        'users.users_username',
        'users.users_email',
    ]);

    $successful = false;
    if ($user) {
        $expectedHash = hash($user['users_hash'], $user['users_salty1'] . $password . $user['users_salty2']);
        $successful = hash_equals($user['users_password'], $expectedHash);
    }

    if (!$successful) {
        foreach ($rateLimitState['states'] as $state) {
            loginRateLimitRegisterFailure($state, $now);
        }
        loginRecordAttempt($input, $ipAddress, false, false);
        finish(false, ['code' => null, 'message' => 'Username, email or password incorrect']);
    }

    if (!$CONFIG['DEV'] && loginIsDefaultCredentialUser($user)) {
        foreach ($rateLimitState['states'] as $state) {
            loginRateLimitRegisterFailure($state, $now);
        }
        loginRecordAttempt($input, $ipAddress, false, false);
        finish(false, ['code' => null, 'message' => 'Default administrator credentials are disabled.']);
    }

    if ($user['users_suspended'] != '0') {
        loginRecordAttempt($input, $ipAddress, false, false);
        finish(false, ['code' => null, 'message' => 'User account is suspended']);
    }

    foreach ($rateLimitState['states'] as $state) {
        loginRateLimitRegisterSuccess($state, $now);
    }

    loginRecordAttempt($input, $ipAddress, false, true);

    if ((!isset($_SESSION['return']) || !$_SESSION['return']) && isset($_SESSION['app-oauth'])) {
        $token = $GLOBALS['AUTH']->generateToken($user['users_userid'], false, 'App OAuth', 'app-v1');
        $jwt = $GLOBALS['AUTH']->issueJWT($token, $user['users_userid'], 'app-v1');
        finish(true, null, ['redirect' => $_SESSION['app-oauth'] . 'oauth_callback?token=' . $jwt]);
    }

    $GLOBALS['AUTH']->generateToken($user['users_userid'], false, 'Web', 'web-session');
    finish(true, null, ['redirect' => (isset($_SESSION['return']) && $_SESSION['return']) ? $_SESSION['return'] : $CONFIG['ROOTURL']]);
}

finish(false, ['code' => null, 'message' => 'Unknown error']);
