<?php
require_once __DIR__ . '/../common/head.php';

if (!$setupWizardActive) {
    header('Location: ' . rtrim($CONFIG['ROOTURL'], '/') . '/login/');
    exit;
}

$PAGEDATA['pageConfig'] = ["TITLE" => "Initial Setup"];
$PAGEDATA['errors'] = [];
$PAGEDATA['values'] = [
    'name1' => '',
    'name2' => '',
    'email' => '',
    'username' => '',
];
$PAGEDATA['success'] = false;
$PAGEDATA['passwordMinimumLength'] = 10;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $firstName = trim($_POST['name1'] ?? '');
    $lastName = trim($_POST['name2'] ?? '');
    $email = trim($_POST['email'] ?? '');
    $username = trim($_POST['username'] ?? '');
    $password = $_POST['password'] ?? '';
    $passwordConfirm = $_POST['password_confirm'] ?? '';

    $PAGEDATA['values'] = [
        'name1' => $firstName,
        'name2' => $lastName,
        'email' => $email,
        'username' => $username,
    ];

    if ($firstName === '') {
        $PAGEDATA['errors']['name1'] = 'First name is required.';
    }

    if ($lastName === '') {
        $PAGEDATA['errors']['name2'] = 'Last name is required.';
    }

    if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        $PAGEDATA['errors']['email'] = 'Enter a valid email address.';
    }

    if (strlen($username) < 3) {
        $PAGEDATA['errors']['username'] = 'Username must be at least 3 characters long.';
    } elseif (!preg_match('/^[A-Za-z0-9._-]+$/', $username)) {
        $PAGEDATA['errors']['username'] = 'Username may only contain letters, numbers, dots, hyphens and underscores.';
    }

    if (strlen($password) < $PAGEDATA['passwordMinimumLength']) {
        $PAGEDATA['errors']['password'] = 'Password must be at least ' . $PAGEDATA['passwordMinimumLength'] . ' characters long.';
    }

    if ($password !== $passwordConfirm) {
        $PAGEDATA['errors']['password_confirm'] = 'Passwords do not match.';
    }

    $emailLower = strtolower($email);
    $usernameLower = strtolower($username);

    if (!isset($PAGEDATA['errors']['username'])) {
        $DBLIB->where('users_deleted', 0);
        $DBLIB->where('users_username', $usernameLower);
        $existingUsername = (int) $DBLIB->getValue('users', 'COUNT(*)');
        if ($existingUsername > 0) {
            $PAGEDATA['errors']['username'] = 'Username is already in use.';
        }
    }

    if (!isset($PAGEDATA['errors']['email'])) {
        $DBLIB->where('users_deleted', 0);
        $DBLIB->where('users_email', $emailLower);
        $existingEmail = (int) $DBLIB->getValue('users', 'COUNT(*)');
        if ($existingEmail > 0) {
            $PAGEDATA['errors']['email'] = 'Email address is already in use.';
        }
    }

    if (count($PAGEDATA['errors']) === 0) {
        $saltOne = $bCMS->randomString(8);
        $saltTwo = $bCMS->randomString(8);
        $hashAlgorithm = $CONFIG['AUTH_NEXTHASH'] ?? 'sha256';
        $passwordHash = hash($hashAlgorithm, $saltOne . $password . $saltTwo);

        $userData = [
            'users_email' => $emailLower,
            'users_username' => $usernameLower,
            'users_name1' => $bCMS->sanitizeString($firstName),
            'users_name2' => $bCMS->sanitizeString($lastName),
            'users_salty1' => $saltOne,
            'users_salty2' => $saltTwo,
            'users_hash' => $hashAlgorithm,
            'users_password' => $passwordHash,
            'users_changepass' => 0,
            'users_suspended' => 0,
            'users_deleted' => 0,
            'users_emailVerified' => 1,
            'users_created' => date('Y-m-d H:i:s'),
        ];

        $newUserId = $DBLIB->insert('users', $userData);

        if (!$newUserId) {
            $PAGEDATA['errors']['general'] = 'Unable to create the administrator account. Please check the application logs.';
        } else {
            $positionCreated = $DBLIB->insert('userPositions', [
                'users_userid' => $newUserId,
                'positions_id' => 1,
            ]);

            if (!$positionCreated) {
                $DBLIB->where('users_userid', $newUserId);
                $DBLIB->delete('users');
                $PAGEDATA['errors']['general'] = 'Unable to assign administrator permissions. Please try again.';
            } else {
                $configSaved = false;
                $DBLIB->where('config_key', 'SETUP_COMPLETED');
                $configExists = $DBLIB->getOne('config', ['config_key']);
                if ($configExists) {
                    $DBLIB->where('config_key', 'SETUP_COMPLETED');
                    $configSaved = $DBLIB->update('config', ['config_value' => '1']);
                } else {
                    $configSaved = (bool) $DBLIB->insert('config', ['config_key' => 'SETUP_COMPLETED', 'config_value' => '1']);
                }

                if (!$configSaved) {
                    $DBLIB->where('users_userid', $newUserId);
                    $DBLIB->delete('userPositions');
                    $DBLIB->where('users_userid', $newUserId);
                    $DBLIB->delete('users');
                    $PAGEDATA['errors']['general'] = 'Account created but unable to update setup status. Please contact support.';
                } else {
                    $bCMS->auditLog('INSERT', 'users', 'Initial administrator created via setup wizard', $newUserId, $newUserId);
                    $setupWizardActive = false;
                    $PAGEDATA['success'] = true;
                    $PAGEDATA['SETUP_WIZARD_REQUIRED'] = false;
                    $PAGEDATA['CONFIG']['SETUP_COMPLETED'] = '1';
                }
            }
        }
    }
}

if ($PAGEDATA['success']) {
    echo $TWIG->render('setup/success.twig', $PAGEDATA);
} else {
    echo $TWIG->render('setup/wizard.twig', $PAGEDATA);
}
