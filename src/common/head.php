<?php

/**
 * This file is used by every page. It is included in every page and contains the following:
 * - Database connection
 * - Twig setup
 * - Error handling
 * - Sentry error reporting
 * - Global functions ("bCMS" class)
 * - Config Variables 
 */
require_once __DIR__ . '/../../bootstrap.php';
require_once __DIR__ . '/libs/Config/Config.php';

use Aws\S3\S3Client;
use Aws\S3\Exception\S3Exception;
use Aws\CloudFront\CloudFrontClient;
use Aws\Exception\AwsException;
use Twig\Extra\String\StringExtension;

//TWIG
$TWIGLOADER = new \Twig\Loader\FilesystemLoader([__DIR__ . '/../']);
$devMode = env('DEV_MODE', 'false') === 'true';
if ($devMode) {
    $TWIG = new \Twig\Environment($TWIGLOADER, array(
        'debug' => true,
        'auto_reload' => true,
        'charset' => 'utf-8'
    ));
    $TWIG->addExtension(new \Twig\Extension\DebugExtension());
} else {
    $TWIG = new \Twig\Environment($TWIGLOADER, array(
        'debug' => false,
        'auto_reload' => false,
        'cache' => '/tmp/',
        'charset' => 'utf-8'
    ));
}
$TWIG->addExtension(new StringExtension());

if ($devMode) {
    ini_set('display_errors', 1);
    ini_set('display_startup_errors', 1);
    error_reporting(E_ERROR | E_PARSE);
} else {
    ini_set('display_errors', 0);
    ini_set('display_startup_errors', 0);
    error_reporting(0);
}

/* DATBASE CONNECTION */
try {
    $dbPort = env('DB_PORT', 3306);
    if (!is_numeric($dbPort)) {
        throw new RuntimeException('Environment variable DB_PORT must be numeric.');
    }

    $DBLIB = new MysqliDb([
        'host' => require_env('DB_HOSTNAME'),
        'username' => require_env('DB_USERNAME'), //CREATE INSERT SELECT UPDATE DELETE
        'password' => require_env('DB_PASSWORD'),
        'db' => require_env('DB_DATABASE'),
        'port' => (int) $dbPort,
        //'prefix' => 'adamrms_',
        'charset' => 'utf8mb4'
    ]);
} catch (Throwable $e) {
    // TODO use twig for this
    $message = "Could not connect to database";
    if ($devMode) {
        $message .= ': ' . $e->getMessage() . "\n\n\nPlease double check you have setup environment variables correctly for the database connection.";
    }
    echo $message;
    exit;
}

$CONFIGCLASS = new Config;
$CONFIG = $CONFIGCLASS->getConfigArray();
if (count($CONFIGCLASS->CONFIG_MISSING_VALUES) > 0) {
    $update = false;
    if (isset($_POST['settingUpConfigUsingConfigFormTwig']) and $_POST['settingUpConfigUsingConfigFormTwig'] == "true") {
        $update = $CONFIGCLASS->formArrayProcess($_POST);
    }
    if ($update !== true) die($TWIG->render('common/libs/Config/configForm.twig', ["form" => $CONFIGCLASS->formArrayBuild(), "errors" => is_array($update) ? $update : []]));
    else {
        header("Location: " . $CONFIG['ROOTURL'] . "?");
        exit;
    }
}

$setupWizardActive = false;
try {
    $setupCompleted = $CONFIGCLASS->get('SETUP_COMPLETED');
} catch (Throwable $exception) {
    $setupCompleted = '0';
}
if ($setupCompleted !== '1') {
    try {
        $DBLIB->where('users_deleted', 0);
        $usersCount = (int) $DBLIB->getValue('users', 'COUNT(*)');
    } catch (Throwable $exception) {
        $usersCount = 0;
    }
    if ($usersCount === 0) {
        $setupWizardActive = true;
        if (!defined('SETUP_WIZARD_URL')) {
            $setupRoot = $CONFIG['ROOTURL'] ?? (env('APP_URL') ?? '/');
            $setupRoot = rtrim($setupRoot, '/');
            define('SETUP_WIZARD_URL', $setupRoot . '/setup/');
        }
        if (!defined('SETUP_WIZARD_REQUIRED')) {
            define('SETUP_WIZARD_REQUIRED', true);
        }
        $scriptName = $_SERVER['SCRIPT_NAME'] ?? '';
        $requestUri = $_SERVER['REQUEST_URI'] ?? '';
        $isSetupRoute = (strpos($scriptName, '/setup/') !== false) || (strpos($requestUri, '/setup') === 0);
        if (!$isSetupRoute) {
            if (defined('APP_IS_API') && APP_IS_API === true) {
                http_response_code(503);
                echo json_encode([
                    'result' => false,
                    'error' => [
                        'code' => 'SETUP_REQUIRED',
                        'message' => 'Initial administrator account required before using the API.'
                    ],
                ]);
                exit;
            }
            header('Location: ' . SETUP_WIZARD_URL);
            die('<meta http-equiv="refresh" content="0; url=' . SETUP_WIZARD_URL . '" />');
        }
    }
}

// Set the timezone
date_default_timezone_set($CONFIG['TIMEZONE']);

// Include the bCMS class, which contains useful functions 
require_once __DIR__ . '/libs/bCMS/bCMS.php';
$GLOBALS['bCMS'] = new bCMS;

if (!$devMode && $CONFIG['ERRORS_PROVIDERS_SENTRY'] && strlen($CONFIG['ERRORS_PROVIDERS_SENTRY']) > 0) {
    Sentry\init([
        'dsn' => $CONFIG['ERRORS_PROVIDERS_SENTRY'],
        'release' => $bCMS->getVersionNumber(),
        'sample_rate' => 1.0,
    ]);
}

// TODO move these functions to a class
function generateNewTag()
{
    global $DBLIB;
    //Get highest current tag
    $DBLIB->orderBy("assets_tag", "DESC");
    $DBLIB->where("assets_tag", 'A-%', 'like');
    $tag = $DBLIB->getone("assets", ["assets_tag"]);
    if ($tag) {
        if (is_numeric(str_replace("A-", "", $tag["assets_tag"]))) {
            $value = intval(str_replace("A-", "", $tag["assets_tag"])) + 1;
            if ($value <= 9999) $value = sprintf('%04d', $value);
            return "A-" . $value;
        } else return "A-0001";
    } else return "A-0001";
}
function assetFlagsAndBlocks($assetid)
{
    global $DBLIB;
    $DBLIB->where("maintenanceJobs.maintenanceJobs_deleted", 0);
    $DBLIB->where("(maintenanceJobs.maintenanceJobs_blockAssets = 1 OR maintenanceJobs.maintenanceJobs_flagAssets = 1)");
    $DBLIB->where("(FIND_IN_SET(" . $assetid . ", maintenanceJobs.maintenanceJobs_assets) > 0)");
    $DBLIB->join("maintenanceJobsStatuses", "maintenanceJobs.maintenanceJobsStatuses_id=maintenanceJobsStatuses.maintenanceJobsStatuses_id", "LEFT");
    //$DBLIB->join("users AS userCreator", "userCreator.users_userid=maintenanceJobs.maintenanceJobs_user_creator", "LEFT");
    //$DBLIB->join("users AS userAssigned", "userAssigned.users_userid=maintenanceJobs.maintenanceJobs_user_assignedTo", "LEFT");
    $DBLIB->orderBy("maintenanceJobs.maintenanceJobs_priority", "DESC");
    $jobs = $DBLIB->get('maintenanceJobs', null, ["maintenanceJobs.maintenanceJobs_id", "maintenanceJobs.maintenanceJobs_faultDescription", "maintenanceJobs.maintenanceJobs_title", "maintenanceJobs.maintenanceJobs_faultDescription", "maintenanceJobs.maintenanceJobs_flagAssets", "maintenanceJobs.maintenanceJobs_blockAssets", "maintenanceJobsStatuses.maintenanceJobsStatuses_name"]);
    $return = ["BLOCK" => [], "FLAG" => [], "COUNT" => ["BLOCK" => 0, "FLAG" => 0]];
    if (!$jobs) return $return;
    foreach ($jobs as $job) {
        if ($job["maintenanceJobs_blockAssets"] == 1) {
            $return['BLOCK'][] = $job;
            $return['COUNT']['BLOCK'] += 1;
        }
        if ($job["maintenanceJobs_flagAssets"] == 1) {
            $return['FLAG'][] = $job;
            $return['COUNT']['FLAG'] += 1;
        }
    }
    return $return;
}
function assetLatestScan($assetid)
{
    if ($assetid == null) return false;
    global $DBLIB;
    $DBLIB->orderBy("assetsBarcodesScans.assetsBarcodesScans_timestamp", "DESC");
    $DBLIB->where("assetsBarcodes.assets_id", $assetid);
    $DBLIB->where("assetsBarcodes.assetsBarcodes_deleted", 0);
    $DBLIB->join("assetsBarcodes", "assetsBarcodes.assetsBarcodes_id=assetsBarcodesScans.assetsBarcodes_id");
    $DBLIB->join("locationsBarcodes", "locationsBarcodes.locationsBarcodes_id=assetsBarcodesScans.locationsBarcodes_id", "LEFT");
    $DBLIB->join("assets", "assets.assets_id=assetsBarcodesScans.location_assets_id", "LEFT");
    $DBLIB->join("assetTypes", "assets.assetTypes_id=assetTypes.assetTypes_id", "LEFT");
    $DBLIB->join("locations", "locations.locations_id=locationsBarcodes.locations_id", "LEFT");
    $DBLIB->join("users", "users.users_userid=assetsBarcodesScans.users_userid");
    return $DBLIB->getone("assetsBarcodesScans", ["assetsBarcodesScans.*", "users.users_name1", "users.users_name2", "locations.locations_name", "locations.locations_id", "assets.assetTypes_id", "assetTypes.assetTypes_name", "assets.assets_tag"]);
}

// Setup the "PAGEDATA" array which is used by Twig
$PAGEDATA = array('CONFIG' => $CONFIG, 'VERSION' => $bCMS->getVersionNumber());
$PAGEDATA['SETUP_WIZARD_REQUIRED'] = $setupWizardActive;
$PAGEDATA['SETUP_WIZARD_URL'] = defined('SETUP_WIZARD_URL') ? SETUP_WIZARD_URL : null;

// Setup the "MAINTENANCEJOBPRIORITIES" array which is used by Twig
$GLOBALS['MAINTENANCEJOBPRIORITIES'] = [
    1 => ["class" => "danger", "id" => 1, "text" => "Emergency"],
    2 => ["class" => "danger", "id" => 2, "text" => "Business Critical"],
    3 => ["class" => "danger", "id" => 3, "text" => "Urgent"],
    4 => ["class" => "danger", "id" => 4, "text" => "Routine - High"],
    5 => ["class" => "warning", "id" => 5, "text" => "Routine - Medium", "default" => true],
    6 => ["class" => "warning", "id" => 6, "text" => "Routine - Low"],
    7 => ["class" => "warning", "id" => 7, "text" => "Monthly-cycle Maintenance"],
    8 => ["class" => "success", "id" => 8, "text" => "Annual-cycle Maintenance"],
    9 => ["class" => "success", "id" => 9, "text" => "Long Term"],
    10 => ["class" => "info", "id" => 10, "text" => "Log only"]
];
$PAGEDATA['MAINTENANCEJOBPRIORITIES'] = $GLOBALS['MAINTENANCEJOBPRIORITIES'];


// Include Twig Extensions
require_once __DIR__ . '/libs/twigExtensions.php';

// Try to open up a session cookie
try {
    $sessionLifetime = 43200; //12 hours
    $cookieReferenceUrl = env('APP_URL', $CONFIG['ROOTURL'] ?? null);
    $cookieComponents = $cookieReferenceUrl ? parse_url($cookieReferenceUrl) : [];
    $cookieDomain = $cookieComponents['host'] ?? '';
    $cookiePath = $cookieComponents['path'] ?? '/';
    if (!$cookiePath) {
        $cookiePath = '/';
    }
    $cookieSecure = isset($cookieComponents['scheme']) && strtolower($cookieComponents['scheme']) === 'https';
    $cookieSameSite = $cookieSecure ? 'Lax' : 'Strict';

    if (session_status() !== PHP_SESSION_ACTIVE) {
        session_set_cookie_params([
            'lifetime' => $sessionLifetime,
            'path' => $cookiePath,
            'domain' => $cookieDomain ?: '',
            'secure' => $cookieSecure,
            'httponly' => true,
            'samesite' => $cookieSameSite,
        ]);
        session_start(); //Open up the session
    }
} catch (Exception $e) {
    //Do Nothing
}


// Include the content security policy
$CSP = [
    "default-src" => [
        ["value" => "'none'", "comment" => ""]
    ],
    "script-src" => [
        ["value" => "'self'", "comment" => ""],
        ["value" => "'unsafe-inline'", "comment" => "We have loads of inline JS"],
        ["value" => "'unsafe-eval'", "comment" => ""],
        ["value" => "https://*.adam-rms.com", "comment" => ""],
        ["value" => "https://cdnjs.cloudflare.com", "comment" => ""],
        ["value" => "https://static.cloudflareinsights.com", "comment" => ""],
        ["value" => "https://www.youtube.com", "comment" => "Training modules allow youtube embed"],
        ["value" => "https://*.ytimg.com", "comment" => "Training modules allow youtube embed"],
        ["value" => "https://*.freshstatus.io", "comment" => ""],
        ["value" => "https://js.stripe.com", "comment" => "Stripe payment pricing table"]
    ],
    "style-src" => [
        ["value" => "'unsafe-inline'", "comment" => "We have loads of inline CSS"],
        ["value" => "'self'", "comment" => ""],
        ["value" => "https://*.adam-rms.com", "comment" => ""],
        ["value" => "https://cdnjs.cloudflare.com", "comment" => ""],
        ["value" => "https://fonts.googleapis.com", "comment" => "Google fonts is used extensivley"]
    ],
    "font-src" => [
        ["value" => "'self'", "comment" => ""],
        ["value" => "data:", "comment" => ""],
        ["value" => "https://*.adam-rms.com", "comment" => ""],
        ["value" => "https://fonts.googleapis.com", "comment" => "Google fonts is used extensivley"],
        ["value" => "https://fonts.gstatic.com", "comment" => "Google fonts is used extensivley"],
        ["value" => "https://cdnjs.cloudflare.com", "comment" => "Libraries referenced in HTML"]
    ],
    "manifest-src" => [
        ["value" => "'self'", "comment" => ""],
        ["value" => "https://*.adam-rms.com", "comment" => "Show images on mobile devices like favicons"]
    ],
    "img-src" => [
        ["value" => "'self'", "comment" => ""],
        ["value" => "data:", "comment" => ""],
        ["value" => "blob:", "comment" => ""],
        ["value" => "https://*.adam-rms.com", "comment" => ""],
        ["value" => "https://cdnjs.cloudflare.com", "comment" => "Libraries referenced in HTML"],
        ["value" => "https://cloudflareinsights.com", "comment" => ""],
        ["value" => "https://*.ytimg.com", "comment" => "Training modules allow youtube embed"]
    ],
    "connect-src" => [
        ["value" => "'self'", "comment" => ""],
        ["value" => "https://*.adam-rms.com", "comment" => ""],
        ["value" => "https://sentry.io", "comment" => ""],
        ["value" => "https://cloudflareinsights.com", "comment" => ""],
        ["value" => "https://*.amazonaws.com", "comment" => "To allow S3 uploads"],
        ["value" => "https://*.freshstatus.io", "comment" => ""]
    ],
    "frame-src" => [
        ["value" => "https://www.youtube.com", "comment" => "Training modules allow youtube embed"],
        ["value" => "https://*.freshstatus.io", "comment" => "Training modules allow youtube embed"],
        ["value" => "https://js.stripe.com", "comment" => "Stripe payment pricing table"]
    ],
    "object-src" => [
        ["value" => "'self'", "comment" => ""],
        ["value" => "blob:", "comment" => "Inline PDFs generated by the system"]
    ],
    "worker-src" => [
        ["value" => "'self'", "comment" => ""],
        ["value" => "blob:", "comment" => "Use of camera"]
    ],
    "frame-ancestors" => [
        ["value" => "'self'", "comment" => ""]
    ],
    "report-uri" => [
        ["value" => "https://o83272.ingest.sentry.io/api/5204912/security/?sentry_key=3937ab95cc404dfa95b0e0cb91db5fc6", "comment" => "Report to sentry"]
    ]
];
$CSPString = "Content-Security-Policy: ";
foreach ($CONFIG['CSP'] as $key => $value) {
    $CSPString .= $key;
    foreach ($value as $subvalue) {
        $CSPString .= " " . $subvalue['value'];
    }
    $CSPString .= ";";
}
header($CSPString);


// Include the Auth class
require_once __DIR__ . '/libs/Auth/main.php';
$GLOBALS['AUTH'] = new bID;
